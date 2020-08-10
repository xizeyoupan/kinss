from utils import *
from flask_restful import Api, Resource
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user)
from flask import (Flask, jsonify, make_response, redirect, render_template,
                   request, send_file)
import httpx
from urllib.parse import urlparse
from distutils.util import strtobool
import os
import copy
from gevent import monkey
from gevent.pywsgi import WSGIServer
monkey.patch_all()

client = None
currentPath = os.path.dirname(os.path.realpath(__file__))

SERVER_URL = ''


class User(UserMixin):
    pass


class Article(Resource):
    decorators = [login_required]

    def get(self):
        url = request.args.get("url")
        if url == 'next':
            artilce_list = db.get_article_list(current_user.get_id(), 'unread')
            artilce_list = [artilce_list[0], ]
            return jsonify({"state": "success", "data": artilce_list})
        if url:
            url = parse_url_path(url)
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

        feed_url = parse_url_path(feed_url)
        db.update_feed({action: strtobool(r_type)}, user, feed_url)
        data = db.get_article(feed_url, user)
        return jsonify({"state": "success", 'data': data})


class Refresh(Resource):
    decorators = [login_required]

    def get(self):
        c = copy.deepcopy(current_user)
        scheduler.add_job(gather_rss, args=[c, ])
        return jsonify({"state": "success", "info": 'Refreshing.'})


class GetImg(Resource):
    decorators = [login_required]

    def get(self):
        src = request.args.get("src")
        url = request.args.get("url")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
                   'Referer': urlparse(url).scheme + '://' + urlparse(url).netloc}
        r = httpx.get(src, headers=headers)
        if r.status_code == httpx.codes.OK:
            res = make_response(r.content)
            res.headers['Content-Type'] = r.headers['Content-Type']
            return res
        else:
            r.raise_for_status()


class GetQrCode(Resource):
    decorators = [login_required]

    def get(self):
        content = request.args.get("content")
        img = get_qrcode_img(content)
        return send_file(img, mimetype='image/jpeg')


class GetCategories(Resource):
    decorators = [login_required]

    def get(self):
        return client.get_categories()


class GetFeeds(Resource):
    decorators = [login_required]

    def get(self):
        return client.get_feeds()


app = Flask(__name__)
app.secret_key = 'whatIsSecret_key?'
api = Api(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Unauthorized User'
login_manager.login_message_category = "info"

api.add_resource(Article, '/api/article')
api.add_resource(ArticleList, '/api/article-list')
api.add_resource(Action, '/api/action')
api.add_resource(Refresh, '/api/refresh')
api.add_resource(GetImg, '/api/get-img')
api.add_resource(GetQrCode, '/api/get-qrcode')
api.add_resource(GetCategories, '/api/get-categories')
api.add_resource(GetFeeds, '/api/get-feeds')


@login_manager.user_loader
def load_user(username):
    curr_user = User()
    curr_user.id = username
    return curr_user


@app.route('/')
def index():
    global SERVER_URL
    url = get_config(currentPath)
    if not url:
        return 'Set SERVER_URL first!<a href=/setting>setting</a>'
    SERVER_URL = url
    return '<a href=/login>login</a><hr><a href=/setting>setting</a>'


@app.route('/article')
@login_required
def get_read_page():
    return render_template('article.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    global client
    if request.method == 'GET':
        return render_template('login.html', title='login', action='/login')

    if request.method == 'POST':
        name = request.form['name']
        psd = request.form['psd']
        if not all([name, psd]):
            return make_response("invalid param", 400)

        client = get_client(SERVER_URL, name, psd)

        if client:
            curr_user = User()
            curr_user.id = name
            login_user(curr_user)
            r_next = request.args.get('next')
            return redirect(r_next or '/article')
        else:
            return make_response("invalid param", 401)


@app.route('/setting', methods=['GET', 'POST'])
def setting():
    if request.method == 'GET':
        return render_template('setting.html', title='设置', url=get_config(currentPath))

    if request.method == 'POST':
        baseurl = request.form['baseurl']

        if baseurl:
            set_config(currentPath, baseurl)
            return 'Update successfully.click <a href=/login>here</a> to login.'
        else:
            return make_response("invalid param", 400)


if __name__ == "__main__":
    app.debug = True
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()
    # app.run('0.0.0.0', debug=True)
