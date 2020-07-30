from utils import WSGIServer, parse_single_feed, parse_single_feed_title

import hashlib
import os
import time
from urllib.parse import urlparse

import httpx
from flask import (Flask, jsonify, make_response, redirect, render_template,
                   request)
from tinydb import Query, TinyDB, where
from fake_useragent import UserAgent


currentPath = os.path.dirname(os.path.realpath(__file__))

db = TinyDB(currentPath + '/db.json')
app = Flask(__name__)
User = Query()
user = db.table('User')
feed = db.table('Feed')
Feed = Query()
User_now = ''


def store_rss_in_db(rss_list: list):
    result = []
    for i in rss_list:
        if not feed.contains((Feed.link == i['link']) & (Feed.owner == i['owner'])):
            result.append(i)
    feed.insert_multiple(result)


def get_rss_content(client, url):
    r = client.get(url)
    if r.status_code != httpx.codes.OK:
        r.raise_for_status()
    return r.text


def gather_rss():
    username = User_now
    print(username, 'ddd')
    if not username:
        return
    with httpx.Client() as client:

        feed_all_lsit = []
        rss_dict = user.search(User.name == username)[
            0].get('rss')  # {'category':[{},]}
        if not rss_dict:
            return
        print(rss_dict)
        for key, value in rss_dict.items():
            for i in value:  # i:dict={'url':''}
                try:
                    r = get_rss_content(client, i['url'])
                except Exception as e:
                    print(e)
                    continue
                i['title'] = parse_single_feed_title(r)
                feed_all_lsit.extend(parse_single_feed(
                    r, key, username, i['url']))

            user.update({'rss': rss_dict}, User.name == username)  # 添加feed标题
        store_rss_in_db(feed_all_lsit)
        print('over')


def check_user_status(username, key):
    if not all([username, key]):
        return False

    if not user.contains(User.name == username):
        return False

    user_account = user.search(User.name == username)[0]
    time_stamp = user_account['time_stamp']
    if key == get_key(username, time_stamp):
        return True
    else:
        return False


def get_key(username: str, time_stamp: int) -> str:
    md5 = hashlib.md5(username.encode(encoding='UTF-8')).hexdigest()
    sha = hashlib.sha256(str(time_stamp).encode(encoding='UTF-8')).hexdigest()
    return md5 + sha


@app.route('/api')
def api():
    global User_now
    username = request.cookies.get('username')
    key = request.cookies.get('key')

    if not check_user_status(username, key):
        return 'Permission denied.'

    all_action = ['refresh', 'getlist', 'getarticle', 'getimg']
    action = request.args.get("action")
    if action not in all_action:
        return jsonify({"state": "error", "info": 'invalid param.'})

    if action == 'refresh':  # 一次性任务
        User_now = username
        scheduler.add_job(gather_rss)
        scheduler.resume()
        return jsonify({"state": "success", "info": 'Refreshing.'})
    elif action == 'getlist':
        r_type = request.args.get("type")
        if r_type == 'each':
            url = request.args.get("url")
            if url:
                myQuery = (where('feedurl') == url) & (
                    where('owner') == username)  # & (where('is_read') == False)
        elif r_type == 'all':
            myQuery = (where('owner') == username)
        elif r_type == '':
            pass
        artilce_list = feed.search(myQuery)
        for i in artilce_list:  # 删除文章内容
            try:
                del i['summary']
            except KeyError:
                continue
        return jsonify({"state": "success", "data": artilce_list})
    elif action == 'getarticle':
        link = request.args.get("url")
        if link:
            myQuery = (where('link') == link) & (
                where('owner') == username)
            artilce_list = feed.search(myQuery)
            return jsonify({"state": "success", "data": artilce_list})
    elif action == 'getimg':
        src = request.args.get("src")
        url = request.args.get("url")
        headers = {'User-Agent': UserAgent().random,
                   'Referer': urlparse(url).netloc}
        r = httpx.get(src, headers=headers)
        if r.status_code == httpx.codes.OK:
            res = make_response(r.content)
            res.headers['Content-Type'] = r.headers['Content-Type']
            return res
        else:
            r.raise_for_status()


@ app.route('/')
def hello_world():
    return ('<a href=/login>login</a><hr><a href=/register>register</a>')


@ app.route('/article')
def get_db_data():
    username = request.cookies.get('username')
    key = request.cookies.get('key')

    if check_user_status(username, key):
        rss_dict = user.search(User.name == username)[
            0].get('rss')  # {'category':[{},]}
        return render_template('article.html', rss_dict=rss_dict)
    else:
        return 'Permission denied.'


@ app.route('/login')
def login():
    return render_template('login.html', title='login', action='/loginCheck')


@ app.route('/register')
def register():
    return render_template('login.html', title='register',
                           action='/registerCheck')


@ app.route('/registerCheck')
def registerCheck():
    name = request.args.get('name')
    psd = request.args.get('psd')
    if not all([name, psd]):
        return 'invalid param.'

    if user.contains(User.name == name):
        return 'account exists.'
    else:
        user.insert({'name': name, 'psd': psd,
                     'time_stamp': int(time.time())})
        return 'success.click <a href=/login>here</a> to login.'


@ app.route('/loginCheck')
def loginCheck():
    global User_now
    # TODO:delete cookie
    name = request.args.get('name')
    psd = request.args.get('psd')
    if not all([name, psd]):
        return 'invalid param'

    if not user.contains(User.name == name):
        return 'account not exists.'
    user_account = user.search(User.name == name)[0]
    if psd == user_account['psd']:
        time_stamp = user_account['time_stamp']
        res = make_response(redirect('/article'))
        res.set_cookie('username', name, max_age=3600 * 24 * 3)
        res.set_cookie('key', get_key(name, time_stamp),
                       max_age=3600 * 24 * 3)

        User_now = name
        expires = user_account.get('expires')
        if expires:
            scheduler.reschedule_job('gather_rss', trigger='interval',
                                     seconds=int(expires))

            scheduler.resume()
        return res
    else:
        return 'password error.'


@ app.route('/setting', methods=['GET', 'POST'])
def setting():
    username = request.cookies.get('username')
    key = request.cookies.get('key')

    if not check_user_status(username, key):
        return 'Permission denied.'

    if request.method == 'GET':
        return render_template('setting.html', title='设置')

    if request.method == 'POST':
        # TODO proxy
        files = request.files.get('file')
        expires = request.form['expires']
        if not expires.isdigit():
            return 'invalid expires'
        rss = files.readlines()
        # TODO :categorize
        # {'name':username,'rss':{'category1':[{'url':'','title':''},],}}
        rss = [i.decode().replace('\n', '').replace('\r', '')
               for i in rss]
        rss_dict = {'Default': [{'url': i} for i in rss if i]}
        user.update({'rss': rss_dict, 'expires': expires},
                    User.name == username)

        scheduler.reschedule_job('gather_rss', trigger='interval',
                                 seconds=int(expires))
        scheduler.resume()

        return 'Update successfully.'


if __name__ == "__main__":
    app.debug = True
    from apscheduler.schedulers.gevent import GeventScheduler

    try:
        scheduler = GeventScheduler()
        scheduler.add_job(gather_rss, id='gather_rss', trigger='interval',
                          seconds=3600)
        scheduler.start(paused=True)
        http_server = WSGIServer(('0.0.0.0', 5000), app)
        http_server.serve_forever()
        # app.run('0.0.0.0', debug=True)

    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
