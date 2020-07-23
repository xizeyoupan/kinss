import hashlib
import os
import time

import httpx
from flask import (Flask, jsonify, make_response, redirect, render_template,
                   request)
# from gevent import monkey
# from gevent.pywsgi import WSGIServer
from tinydb import Query, TinyDB

from utils import parse_single_feed

# monkey.patch_all()


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
    return r.text


def gather_rss():
    username = User_now
    print(username, 'ddd')
    if not username:
        return
    with httpx.Client() as client:

        feed_all_lsit = []

        for key, vaule in user.search(User.name == username)[0]['rss'].items():
            for i in vaule:
                try:
                    r = get_rss_content(client, i)
                except Exception as e:
                    print(e)
                    continue
                feed_all_lsit.extend(parse_single_feed(r, key, username))
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
    return md5+sha


@app.route('/api')
def api():
    username = request.cookies.get('username')
    key = request.cookies.get('key')

    if not check_user_status(username, key):
        return 'Permission denied.'

    all_action = ['refresh']
    action = request.args.get("action")
    if action not in all_action:
        return jsonify({"state": "error", "info": 'invalid param.'})


@app.route('/')
def hello_world():
    return ('<a href=/login>login</a><hr><a href=/register>register</a>')


@app.route('/article')
def get_db_data(article_data: dict = None):
    username = request.cookies.get('username')
    key = request.cookies.get('key')

    if check_user_status(username, key):
        return render_template('article.html', article_data=article_data)
    else:
        return 'Permission denied.'


@app.route('/login')
def login():
    return render_template('login.html', title='login', action='/loginCheck')


@app.route('/register')
def register():
    return render_template('login.html', title='register',
                           action='/registerCheck')


@app.route('/registerCheck')
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


@app.route('/loginCheck')
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
        res.set_cookie('username', name, max_age=3600*24*3)
        res.set_cookie('key', get_key(name, time_stamp), max_age=3600*24*3)

        User_now = name
        expires = user_account.get('expires')
        if expires:
            scheduler.reschedule_job('gather_rss', trigger='interval',
                                     seconds=int(expires))

            scheduler.resume()
        return res
    else:
        return 'password error.'


@app.route('/setting', methods=['GET', 'POST'])
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
        # {'name':username,'rss':{'category1':['url1','url2'],
        # 'category2':['url1','url2'],}}
        rss_dict = {'Default': [i.decode().replace('\n', '').replace('\r', '')
                                for i in rss]}
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
        scheduler.add_job(gather_rss, id='gather_rss')
        scheduler.start(paused=True)
        # http_server = WSGIServer(('', 5000), app)
        # http_server.serve_forever()
        app.run('0.0.0.0', debug=True)

    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
