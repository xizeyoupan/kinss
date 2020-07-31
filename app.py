from utils import parse_single_feed, parse_single_feed_title, get_rss_content
import os
from distutils.util import strtobool
from urllib.parse import urlparse
import httpx
from fake_useragent import UserAgent
from flask import (Flask, jsonify, make_response, redirect, render_template,
                   request)
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user
from flask_restful import Api, Resource
from tinydb import TinyDB, where
from werkzeug.security import check_password_hash, generate_password_hash
from gevent import monkey
from gevent.pywsgi import WSGIServer
monkey.patch_all()


class User(UserMixin):
    pass


class DB:
    def __init__(self):
        self.db = TinyDB(currentPath + '/db.json')
        self.user = self.db.table('User')
        self.feed = self.db.table('Feed')

    def get_article(self, url, username) -> list:
        myQuery = (where('link') == url) & (where('owner') == username)
        artilce_list = self.feed.search(myQuery)
        return artilce_list

    def get_article_list(self, username, search_type, sort_by=None) -> list:
        if search_type == 'all':
            myQuery = (where('owner') == username)
        elif search_type == 'read':
            myQuery = (where('owner') == username) & (where('is_read') == True)
        elif search_type == 'unread':
            myQuery = (where('owner') == username) & (
                where('is_read') == False)
        elif search_type == 'starred':
            myQuery = (where('owner') == username) & (where('is_star') == True)

        artilce_list = self.feed.search(myQuery)
        return artilce_list

    def update_feed(self, feed_info: dict, username, feed_url):
        myQuery = (where('link') == feed_url) & (where('owner') == username)
        self.user.update(feed_info, myQuery)

    def get_articles_from_each_rss(self, username, rss_url, sort_by=None) -> list:
        myQuery = (where('feedurl') == rss_url) & (where('owner') == username)
        artilce_list = self.feed.search(myQuery)
        return artilce_list

    def store_rss_in_db(self, rss_list: list):
        result = []
        for i in rss_list:
            if not self.feed.contains((where('link') == i['link']) & (where('owner') == i['owner'])):
                result.append(i)
        self.feed.insert_multiple(result)

    def register_user(self, username, psd):
        self.user.insert({'name': username, 'password': psd})

    def update_user(self, user_info: dict, username):
        self.user.update(user_info, where('name') == username)

    def user_exists(self, username) -> bool:
        if not self.user.contains(where('name') == username):
            return False
        else:
            return True

    def get_user_info(self, username) -> dict:
        user = self.user.search(where('name') == username)
        return user[0]


class Article(Resource):
    decorators = [login_required]

    def get(self):
        url = request.args.get("url")
        if url:
            artilce_list = db.get_article(url, current_user.get_id())
            return jsonify({"state": "success", "data": artilce_list})
        else:
            return jsonify({"state": "error", "info": 'invalid param.'})


class ArticleList(Resource):
    decorators = [login_required]

    def get(self):
        user = current_user.get_id()
        r_type = request.args.get("type")
        if r_type == 'each':
            url = request.args.get("url")
            if url:
                artilce_list = db.get_articles_from_each_rss(user, url)
        else:
            artilce_list = db.get_article_list(user, r_type)

        for i in artilce_list:  # 删除文章内容
            try:
                del i['summary']
            except KeyError:
                continue
        return jsonify({"state": "success", "data": artilce_list})


class Action(Resource):
    decorators = [login_required]

    def get(self):
        user = current_user.get_id()
        feed_url = request.args.get("url")
        action_list = ['is_read', 'is_star']
        action = request.args.get("action")
        r_type = request.args.get("type")
        if action not in action_list:
            return jsonify({"state": "error", "info": 'invalid param.'})

        db.update_feed({action: strtobool(r_type)}, user, feed_url)


class Refresh(Resource):
    decorators = [login_required]

    def get(self):
        scheduler.add_job(gather_rss, args=[current_user.get_id(), ])
        scheduler.resume()
        return jsonify({"state": "success", "info": 'Refreshing.'})


class GetImg(Resource):
    decorators = [login_required]

    def get(self):
        src = request.args.get("src")
        url = request.args.get("url")
        headers = {'User-Agent': UserAgent().random,
                   'Referer': urlparse(url).scheme + '://' + urlparse(url).netloc}
        r = httpx.get(src, headers=headers)
        if r.status_code == httpx.codes.OK:
            res = make_response(r.content)
            res.headers['Content-Type'] = r.headers['Content-Type']
            return res
        else:
            r.raise_for_status()


currentPath = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)
app.secret_key = 'whatIsSecret_key?'
api = Api(app)
db = DB()
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Unauthorized User'
login_manager.login_message_category = "info"

api.add_resource(Article, '/api/article')
api.add_resource(ArticleList, '/api/article-list')
api.add_resource(Action, '/api/action')
api.add_resource(Refresh, '/api/refresh')
api.add_resource(GetImg, '/api/get-img')


@login_manager.user_loader
def load_user(username):
    if db.user_exists(username):
        curr_user = User()
        curr_user.id = username
        return curr_user


def gather_rss(username=None):
    if not username:
        print('ggg')
        return
    print(username, 'ddd')

    with httpx.Client() as client:

        feed_all_lsit = []
        rss_dict = db.get_user_info(username).get('rss')  # {'category':[{},]}
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

            db.update_user({'rss': rss_dict}, username)  # 添加feed标题
        db.store_rss_in_db(feed_all_lsit)
        print('over')


@app.route('/')
def index():
    return ('<a href=/login>login</a><hr><a href=/register>register</a>')


@app.route('/article')
@login_required
def get_db_data():
    user = current_user.get_id()
    rss_dict = db.get_user_info(user).get(
        'rss')  # {'category':[{},]}
    return render_template('article.html', rss_dict=rss_dict)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', title='login', action='/login')

    if request.method == 'POST':
        name = request.form['name']
        psd = request.form['psd']
        if not all([name, psd]):
            return make_response("invalid param", 400)

        if not db.user_exists(name):
            return make_response("account not exists.", 400)

        user_account = db.get_user_info(name)
        if not check_password_hash(user_account.get('password'), psd):
            return make_response("password error.", 401)
        else:
            curr_user = User()
            curr_user.id = name
            login_user(curr_user)
            r_next = request.args.get('next')
            return redirect(r_next or '/article')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('login.html', title='register', action='/register')

    if request.method == 'POST':
        name = request.form['name']
        psd = request.form['psd']
        if not all([name, psd]):
            return make_response("invalid param", 400)

        if db.user_exists(name):
            return make_response("account exists.", 400)
        else:
            db.register_user(name, generate_password_hash(psd))
            return 'success.click <a href=/login>here</a> to login.'


@app.route('/setting', methods=['GET', 'POST'])
@login_required
def setting():
    if request.method == 'GET':
        return render_template('setting.html', title='设置')

    if request.method == 'POST':
        # TODO proxy
        files = request.files.get('file')
        expires = request.form['expires']
        if not expires.isdigit():
            return make_response('invalid expires', 400)
        rss = files.readlines()
        # TODO :categorize
        # {'name':username,'rss':{'category1':[{'url':'','title':''},],}}
        rss = [i.decode().replace('\n', '').replace('\r', '')
               for i in rss]
        rss_dict = {'Default': [{'url': i} for i in rss if i]}
        db.update_user({'rss': rss_dict, 'expires': expires},
                       current_user.get_id())

        scheduler.reschedule_job('gather_rss', trigger='interval',
                                 seconds=int(expires))
        scheduler.resume()

        return 'Update successfully.click <a href=/article>here</a> to enjoy.'


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
