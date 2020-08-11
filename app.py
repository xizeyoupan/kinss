from gevent import monkey
from gevent.pywsgi import WSGIServer
monkey.patch_all()

import io
import os
from urllib.parse import urlparse

import requests
from flask import (Flask, jsonify, make_response, redirect, render_template,
                   request, send_file)
from flask_login import LoginManager, UserMixin, login_required, login_user
from flask_restful import Api, Resource


from utils import (extract_feed, get_client, get_config, get_qrcode_img,
                   resize_img, set_config)


clients_pool = []
client = None
currentPath = os.path.dirname(os.path.realpath(__file__))

SERVER_URL = get_config(currentPath)


class User(UserMixin):
    pass


class Article(Resource):
    decorators = [login_required]

    def get(self):
        entry_id = request.args.get("entry_id")
        if entry_id == 'next':
            entries = client.get_entries(status='unread', direction='desc')
            if not entries['entries']:  # 没有未读
                return jsonify({"state": "error", "info": 'all entries have been read.'})
            entry = entries['entries'][0]

        else:
            entry = client.get_entry(int(entry_id))

        entry['content'] = extract_feed(entry['content'], entry['url'])
        return jsonify({"state": "success", "data": entry})


class ArticleList(Resource):
    decorators = [login_required]

    def get(self):
        r_type = request.args.get("type")
        kwargs = {'order': 'published_at', 'direction': 'desc', 'limit': 1000}
        if r_type == 'each':
            feed_id = request.args.get("feed_id")
            entries = client.get_feed_entries(feed_id, **kwargs)
        elif r_type == 'category':
            category_id = request.args.get("category_id")
            entries = client.get_entries(**kwargs)
            entries = {'entries': [i for i in entries['entries']
                                   if i['feed']['category']['id'] == int(category_id)]}
            entries['total'] = len(entries['entries'])
        elif r_type == 'read':
            entries = client.get_entries(**kwargs, status='read')
        elif r_type == 'unread':
            entries = client.get_entries(**kwargs, status='unread')
        elif r_type == 'all':
            entries = client.get_entries(**kwargs)
        elif r_type == 'starred':
            entries = client.get_entries(**kwargs, starred=True)

        for i in entries['entries']:  # 删除文章内容
            i.pop('content')
        return jsonify({"state": "success", "data": entries})


class Action(Resource):
    decorators = [login_required]

    def get(self):
        entry_id = request.args.get("entry_id")
        action = request.args.get("action")
        r_type = request.args.get("type")
        if action == 'is_read':
            r_type = 'read' if r_type == '1' else 'unread'
            client.update_entries([int(entry_id), ], r_type)
        elif action == 'is_star':
            client.toggle_bookmark(int(entry_id))

        entry = client.get_entry(int(entry_id))
        return jsonify({"state": "success", 'data': entry})


class Refresh(Resource):
    decorators = [login_required]

    def get(self):
        client.refresh_all_feeds()
        return jsonify({"state": "success", "info": 'Refreshing.'})


class GetImg(Resource):
    decorators = [login_required]

    def get(self):
        src = request.args.get("src")
        url = request.args.get("url")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
                   'Referer': urlparse(url).scheme + '://' + urlparse(url).netloc}
        r = requests.get(src, headers=headers)
        if r.status_code == requests.codes.OK:
            if src.split('.')[-1] == 'gif':
                res = make_response(r.content)
                res.headers['Content-Type'] = r.headers['Content-Type']
                return res
            raw = resize_img(io.BytesIO(r.content))
            return send_file(raw, mimetype='image/jpeg')
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
    global client
    curr_user = User()
    curr_user.id = username
    for i in clients_pool:
        if i['id'] == username:
            client = i['client']
    return curr_user


@app.route('/')
def index():
    return '<a href=/login>login</a><hr><a href=/setting>setting</a>'


@app.route('/article')
@login_required
def get_read_page():
    return render_template('article.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    global client, SERVER_URL

    if request.method == 'GET':
        url = get_config(currentPath)
        if not url:
            return 'Set SERVER_URL first!<a href=/setting>setting</a>'
        SERVER_URL = url
        return render_template('login.html', title='login', action='/login')

    if request.method == 'POST':
        name = request.form['name']
        psd = request.form['psd']
        if not all([name, psd]):
            return make_response("invalid param", 400)

        try:
            client = get_client(SERVER_URL, name, psd)
        except Exception as e:
            print(e)
            return jsonify(error='error')

        curr_user = User()
        curr_user.id = name
        login_user(curr_user)
        r_next = request.args.get('next')
        flag = True
        for i in clients_pool:
            if i['id'] == name:
                flag = False
        if flag:
            clients_pool.append({'id': name, 'client': client})
        return redirect(r_next or '/article')


@app.route('/setting', methods=['GET', 'POST'])
def setting():
    global SERVER_URL
    if request.method == 'GET':
        return render_template('setting.html', title='设置', url=get_config(currentPath))

    if request.method == 'POST':
        baseurl = request.form['baseurl']

        if baseurl:
            set_config(currentPath, baseurl)
            SERVER_URL = baseurl
            return 'Update successfully.click <a href=/login>here</a> to login.'
        else:
            return make_response("invalid param", 400)


if __name__ == "__main__":
    # app.debug = True
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    http_server.serve_forever()
    # app.run('0.0.0.0', debug=True)
