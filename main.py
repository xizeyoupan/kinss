import json
import os
import re
import sqlite3
import threading
import time
from concurrent.futures import as_completed
from urllib import parse

import feedparser
import requests
from bottle import (Bottle, PasteServer, abort, redirect, request, response,
                    run, static_file, template)
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests_futures.sessions import FuturesSession

lock = threading.Lock()
currentPath = os.path.dirname(os.path.realpath(__file__))


def normalize_whitespace(text):
    text = re.sub(r'[\n\r\t]', ' ', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def extract_feed(html_content, url=''):
    if not html_content:
        return html_content
    soup = BeautifulSoup(html_content, 'lxml')

    for i in soup.find_all('a'):  # 删除超链接
        if i.get('href'):
            del i['href']
        if i.get('target'):
            del i['target']

    for i in soup.find_all('img'):  # 处理图片,防盗链
        if i.get('srcset'):
            del i['srcset']
        if i.get('height'):
            del i['height']
        if i.get('width'):
            del i['width']

        i['src'] = '/src/?src=' + \
            parse.quote(i['src']) + '&url='+parse.quote(url)

    res = [str(i) for i in soup.body.contents]
    return ''.join(res).replace('\xa0', '').strip()


class Kinss(object):
    def __init__(self):
        self.load_config()
        self.session = FuturesSession()
        self.check_db()
        self.refresh_thd = threading.Thread(target=self.refresh_data)
        self.refresh_thd.setDaemon(True)
        self.refresh_thd.start()

    def __del__(self):
        self.con.commit()
        self.con.close()

    def refresh_data(self):
        while True:
            self.parse_and_store_data()
            time.sleep(self.config['CACHE_EXPIRE'])

    def check_db(self):
        if not os.path.exists(currentPath+'/kinss.db'):
            self.con = sqlite3.connect(
                currentPath+'/kinss.db', check_same_thread=False)
            with self.con:
                self.con.execute("create table kinss \
                    (id integer primary key, \
                    feed_title varchar ,article_title varchar unique,\
                    published_time INTEGER, summary varchar, \
                    link varchar, is_read INTEGER)")
        else:
            self.con = sqlite3.connect(
                currentPath+'/kinss.db', check_same_thread=False)

    def parse_and_store_data(self):
        with self.session as session:
            futures = [session.get(i) for i in self.config['FEEDS']]
            for future in as_completed(futures):
                resp = future.result()
                d = feedparser.parse(resp.text)

                lock.acquire()
                data = []
                for i in d['entries']:
                    article_title = i['title']
                    if self.check_article(article_title):
                        continue

                    content = i.get('content')
                    summary = i['summary']

                    if content:
                        article_content = content[0]['value'] if len(
                            content[0]['value']) > len(summary) else summary
                    else:
                        article_content = summary
                    link = i['link']

                    article_content = normalize_whitespace(article_content)
                    article_content = extract_feed(article_content, link)

                    try:
                        published_parsed = int(
                            time.mktime(i['published_parsed']))
                    except (KeyError, TypeError):
                        published_parsed = int(time.time())

                    t = (d.feed.title, article_title,
                         published_parsed,
                         article_content, link, 0)

                    data.append(t)

                try:
                    with self.con:
                        self.con.executemany("insert into kinss\
                            (feed_title, article_title,published_time,\
                            summary, link ,is_read) \
                            values (?, ?, ?, ?, ?, ?)", data)
                except sqlite3.IntegrityError:
                    print('can not store twice')
                finally:
                    lock.release()

    def load_config(self):
        with open(currentPath+'/config.json', 'r', encoding='utf') as f:
            self.config = json.load(f)  # self.config->dict

    def check_article(self, article_title):
        res = self.con.execute(
            "select * from kinss where article_title = ?", (article_title,))
        for i in res:
            return True  # Article exists
        return False

    def read(self):
        return template(currentPath+'/static/read.tpl')

    def get_static(self, filename):
        return static_file(filename, root=currentPath+'/static/')

    def home(self):
        redirect('/read')

    def get_article(self):
        idx = request.query.id
        response.content_type = 'application/json'

        lock.acquire()
        for row in self.con.execute('SELECT * from kinss \
                                    where id = ?', (idx,)):
            lock.release()
            return json.dumps({'state': 'success', 'detail': row},
                              ensure_ascii=False)
        lock.release()
        return {'state': 'error', 'detail': 'article not found'}

    def get_article_list_from_category(self):
        category = request.query.category  # 2:all,1:read,or 0:unread
        sort = request.query.sort  # asc or desc
        response.content_type = 'application/json'
        if not category:
            category = '2'
        if not sort:
            sort = 'desc'
        data = []

        lock.acquire()
        if category == '2':
            for row in self.con.execute('SELECT id, feed_title, article_title, published_time,\
                                        is_read from kinss ORDER \
                                        BY published_time {}'.format(sort)):
                data.append(row)
        else:
            for row in self.con.execute('SELECT id, feed_title, article_title, published_time,\
                                        is_read from kinss \
                                        where is_read =? order by \
                                        published_time {}'.format(sort),
                                        (category, )):
                data.append(row)
        lock.release()
        return json.dumps({'state': 'success', 'list': data},
                          ensure_ascii=False)

    def get_feed_list(self):
        data = []
        response.content_type = 'application/json'
        lock.acquire()

        for row in self.con.execute('SELECT feed_title,is_read from kinss'):
            data.append(row)
        lock.release()

        t = {i: [0, 0] for i in list(set([k[0] for k in data]))}
        for i in data:
            if i[1] == 0:
                t[i[0]][0] += 1
            elif i[1] == 1:
                t[i[0]][1] += 1
        data = []
        for key, value in t.items():
            data.append({'title': key, 'read': value[1], 'unread': value[0]})

        return json.dumps({'state': 'success', 'feed': data},
                          ensure_ascii=False)

    def get_article_list_from_feed(self):
        feed = request.query.feed  # 2:all,1:read,or 0:unread
        sort = request.query.sort  # asc or desc
        response.content_type = 'application/json'
        if not feed:
            return {'state': 'error'}
        if not sort:
            sort = 'desc'
        data = []

        lock.acquire()
        for row in self.con.execute('SELECT id, feed_title, article_title, published_time,\
                                    is_read from kinss where feed_title =?\
                                    order by \
                                    published_time {}'.format(sort),
                                    (feed,)):
            data.append(row)
        lock.release()

        return json.dumps({'state': 'success', 'list': data},
                          ensure_ascii=False)

    def get_src(self):
        src = request.query.src
        url = request.query.url
        headers = {'referer': url, 'User-Agent': UserAgent().random}
        r = requests.get(src, headers=headers)
        if r.status_code == requests.codes.ok:
            response.set_header('Content-Type', r.headers['Content-Type'])
            return r.content
        else:
            abort(text=str(r.status_code))

    def mark_as_read(self):
        idx = request.query.id
        read_state = request.query.read_state

        if not read_state:
            read_state = 1
        try:
            int(idx)
        except ValueError:
            return {'state': 'error', 'detail': 'ValueError'}

        lock.acquire()
        self.con.execute("UPDATE kinss set is_read = ? where id=?",
                         (read_state, idx))
        self.con.commit()
        lock.release()

        if self.con.total_changes:
            return {'state': 'success'}
        else:
            return {'state': 'error', 'detail': 'nothing has been changed'}


if __name__ == '__main__':

    def appRoute(app):
        kinss = Kinss()
        routeDict = {
            '/read': kinss.read,
            '/static/<filename>': kinss.get_static,
            '/': kinss.home,
            '/src/': kinss.get_src,
            '/api/category': kinss.get_article_list_from_category,
            '/api/feed': kinss.get_article_list_from_feed,
            '/api/article': kinss.get_article,
            '/api/markread': kinss.mark_as_read,
            '/api/feedlist': kinss.get_feed_list
        }

        for url in routeDict:
            app.route(url)(routeDict[url])

    app = Bottle()
    appRoute(app)
    run(app, host='localhost', port=8080,
        server=PasteServer)
