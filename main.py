from requests_futures.sessions import FuturesSession
import json
import os
import sqlite3
import threading
from concurrent.futures import as_completed

import feedparser
from bottle import Bottle, abort, redirect, request, response
from bottle import run, static_file, template, PasteServer
import re
from urllib import parse
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests

lock = threading.Lock()
currentPath = os.path.dirname(os.path.realpath(__file__))


def save(a):
    with open('1.py', 'a+', encoding='utf8') as f:
        f.write(str(a))


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
        self.get_feeds()
        self.session = FuturesSession()
        self.check_db()
        self.freshen_thd = threading.Thread(target=self.get_data)
        self.freshen_thd.setDaemon(True)
        self.freshen_thd.start()

    def __del__(self):
        self.con.commit()
        self.con.close()

    def check_db(self):
        if not os.path.exists(currentPath+'/kinss.db'):
            self.con = sqlite3.connect(
                currentPath+'/kinss.db', check_same_thread=False)
            with self.con:
                self.con.execute("create table kinss \
                    (id integer primary key, \
                    feed_title varchar ,article_title varchar unique,\
                    published_time varchar, summary varchar, \
                    link varchar, is_read INTEGER)")
        else:
            self.con = sqlite3.connect(
                currentPath+'/kinss.db', check_same_thread=False)

    def get_data(self):
        with self.session as session:
            futures = [session.get(i) for i in self.feeds]
            for future in as_completed(futures):
                resp = future.result()
                d = feedparser.parse(resp.text)

                lock.acquire()
                data = []
                for i in d['entries']:
                    # save(i)

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

                    t = (d.feed.title, article_title,
                         i['published'], article_content, link, 0)

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

    def get_feeds(self):
        with open(currentPath+'/config.json', 'r', encoding='utf') as f:
            self.feeds = json.load(f)['FEEDS']  # self.feeds->list

    def check_article(self, article_title):
        res = self.con.execute(
            "select * from kinss where article_title = (?)", (article_title,))
        for i in res:
            return True  # Title exists
        return False

    def read(self):
        data = []
        lock.acquire()
        for row in self.con.execute('SELECT id, feed_title, article_title, published_time,\
                                is_read from kinss'):
            data.append(row)
        lock.release()
        return template(currentPath+'/static/read.tpl', data=data)

    def get_static(self, filename):
        return static_file(filename, root=currentPath+'/static/')

    def home(self):
        redirect('/read')

    def get_article(self, idx):
        lock.acquire()
        for row in self.con.execute('SELECT summary from kinss \
                                    where id = (?)', (idx,)):
            lock.release()
            return row
        lock.release()
        abort(404, 'not found')

    def get_src(self):
        src = request.query.src
        url = request.query.url
        headers = {'referer': url, 'User-Agent': UserAgent().random}
        r = requests.get(src, headers=headers)
        if r.status_code == requests.codes.ok:
            response.set_header('Content-Type', r.headers['Content-Type'])
            return r.content
        else:
            abort()


if __name__ == '__main__':

    def appRoute(app):
        kinss = Kinss()
        routeDict = {
            '/read': kinss.read,
            '/static/<filename>': kinss.get_static,
            '/': kinss.home,
            '/article/<idx>': kinss.get_article,
            '/src/': kinss.get_src
        }

        for url in routeDict:
            app.route(url)(routeDict[url])

    app = Bottle()
    appRoute(app)
    run(app, host='192.168.123.156', port=8080,
        debug=True, reloader=True, server=PasteServer)
