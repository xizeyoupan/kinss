import os
import time
import hashlib
from flask import Flask, render_template

from tinydb import Query, TinyDB
from flask import request, Response, make_response, redirect


currentPath = os.path.dirname(os.path.realpath(__file__))

db = TinyDB(currentPath + '/db.json')
app = Flask(__name__)
User = Query()
user = db.table('User')


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
        return res
    else:
        return 'password error.'


if __name__ == "__main__":
    app.debug = True
    # from gevent.pywsgi import WSGIServer
    # from gevent import monkey
    # monkey.patch_all()  # 打上猴子补丁
    # http_server = WSGIServer(('', 5000), app)
    # http_server.serve_forever()
    app.run('0.0.0.0', debug=True)
