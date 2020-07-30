import re
import time
from urllib import parse

import feedparser
from bs4 import BeautifulSoup
from gevent import monkey
from gevent.pywsgi import WSGIServer
monkey.patch_all()


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
        src = i['src']
        if src.startswith('/'):
            t = parse.urlparse(url)
            src = t.scheme + '://' + t.netloc + src
        i['src'] = '/api?action=getimg&src=' + \
            parse.quote(src) + '&url=' + parse.quote(url)

    res = [str(i) for i in soup.body.contents]
    return ''.join(res).replace('\xa0', '').strip()


def parse_single_feed(html_text, category, username, feed_url):
    d = feedparser.parse(html_text)

    each_rss_list = []
    for i in d['entries']:
        article_title = i['title']
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

        '''
        rss_dict:{feed_title:str,article_title:str,published_time:int,summary:str,
                link:str, is_read:bool,is_star:bool,category:str,owner:str,feedurl:str}
        '''

        t = {'feed_title': d.feed.title, 'article_title': article_title,
             'published_time': published_parsed, 'feedurl': feed_url,
             'summary': article_content, 'link': link, 'is_read': False,
             'is_star': False, 'category': category, 'owner': username}

        each_rss_list.append(t)
    return each_rss_list


def parse_single_feed_title(html) -> str:
    d = feedparser.parse(html)
    t = d.feed.title
    return t
