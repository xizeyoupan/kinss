from gevent import monkey
from gevent.pywsgi import WSGIServer
monkey.patch_all()

import io
import os
from datetime import timedelta
from urllib.parse import urlparse

import requests
from flask import (Flask, jsonify, make_response, redirect, render_template,
                   request, send_file, url_for)
from flask_login import (LoginManager, UserMixin, login_required, login_user,
                         logout_user)
from flask_restful import Api, Resource


from utils import (extract_feed, get_client, get_json_from_fever,
                   get_qrcode_img, resize_img)


clients_pool = []
currentPath = os.path.dirname(os.path.realpath(__file__))


class User(UserMixin):
    pass


class Article(Resource):
    decorators = [login_required]

    def get(self):
        item_id = request.args.get("item_id")

        if item_id == "next":
            ids = get_json_from_fever(
                client[0], client[1], '&unread_item_ids')

            ids = ids['unread_item_ids'].split(",")
            ids = list(filter(lambda x: x, ids))
            total = len(ids)

            if total:
                item_id = ids[0]
            else:
                return jsonify({"state": "error", "data": 'empty'})

        items = get_json_from_fever(
            client[0], client[1], '&items&with_ids=' + item_id)['items'][0]
        items['html'] = extract_feed(items['html'], items['url'])
        return jsonify({"state": "success", "data": items})


class ArticleList(Resource):
    decorators = [login_required]

    def get(self):
        type = request.args.get("type")  # unread,saved
        since_id = request.args.get("since_id")

        ids = get_json_from_fever(
            client[0], client[1], '&{}_item_ids'.format(type))

        ids = ids['{}_item_ids'.format(type)].split(",")
        ids = list(filter(lambda x: x, ids))
        total = len(ids)

        if not total:
            return jsonify({"state": "success", 'total': total, 'next_id': None})

        ids = list(map(lambda x: int(x), ids))
        ids.sort()
        ids = list(map(lambda x: str(x), ids))

        if since_id:
            ids = ids[ids.index(since_id):]

        next_id = ids[0:50][-1]
        if next_id == ids[-1]:
            next_id = None
        else:
            next_id = ids[50]
            ids = ids[0:50]

        feeds = get_json_from_fever(client[0], client[1], "&feeds")['feeds']
        temp = get_json_from_fever(client[0], client[1], "&groups")
        feeds_groups = temp['feeds_groups']
        groups = temp['groups']

        items = get_json_from_fever(
            client[0], client[1], '&items&with_ids=' + ','.join(ids))['items']

        for i in items:
            del i['html']

            for j in feeds:
                if i['feed_id'] == j['id']:
                    i['feed_title'] = j['title']
                    break

            for k in feeds_groups:
                if str(i['feed_id']) in k['feed_ids'].split(","):
                    i['group_id'] = k['group_id']
                    break

            for j in groups:
                if i['group_id'] == j['id']:
                    i['group_title'] = j['title']
                    break

        return jsonify({"state": "success", "items": items, 'total': total, 'next_id': next_id})


class Action(Resource):
    decorators = [login_required]

    def get(self):
        item_id = request.args.get("item_id")
        type = request.args.get("type")
        result = get_json_from_fever(
            client[0], client[1], '&mark=item&as={}&id={}'.format(type, item_id))
        if result['auth']:
            return jsonify({"state": "success"})


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
            else:
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


app = Flask(__name__)
app.secret_key = os.urandom(16)
api = Api(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Unauthorized User'
login_manager.login_message_category = "info"

api.add_resource(Article, '/api/article')
api.add_resource(ArticleList, '/api/article-list')
api.add_resource(Action, '/api/action')
api.add_resource(GetImg, '/api/get-img')
api.add_resource(GetQrCode, '/api/get-qrcode')


@ login_manager.user_loader
def load_user(username):
    global client
    curr_user = User()
    curr_user.id = username
    for i in clients_pool:
        if i['id'] == username:
            client = i['client']
            break
    return curr_user


@ app.route('/')
def index():
    return '<a href=/login>login</a><hr><a href=/article>read</a>'


@ app.route('/article')
@ login_required
def get_read_page():
    return render_template('article.html')


@ app.route('/login', methods=['GET', 'POST'])
def login():
    global client, SERVER_URL

    if request.method == 'GET':
        name = request.args.get('name')
        psd = request.args.get('psd')
        endpoint = request.args.get('endpoint')
        if not all([name, psd, endpoint]):
            return render_template('login.html', title='login', action='/login')

    if request.method == 'POST':
        name = request.form['name']
        psd = request.form['psd']
        endpoint = request.form['endpoint']
        if not all([name, psd, endpoint]):
            return make_response("invalid param", 400)

    try:
        client = get_client(endpoint, name, psd)
    except Exception as e:
        print(e)
        return jsonify(error=str(e))

    curr_user = User()
    curr_user.id = name + endpoint
    login_user(curr_user, remember=True, duration=timedelta(weeks=1))
    flag = True
    for i in clients_pool:
        if i['id'] == curr_user.id:
            flag = False
            break
    if flag:
        clients_pool.append({'id': curr_user.id, 'client': client})
    return redirect('/article')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    # app.debug = True
    port = os.environ.get('PORT') or 5000
    port = int(port)
    http_server = WSGIServer(('0.0.0.0', port), app)
    print('http://0.0.0.0:{}'.format(port))
    http_server.serve_forever()
    # app.run('0.0.0.0', debug=True)
