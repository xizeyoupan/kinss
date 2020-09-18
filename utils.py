import hashlib
import io
import re
from urllib import parse

import qrcode
import requests
from bs4 import BeautifulSoup
from PIL import Image


def get_qrcode_img(content):
    img = qrcode.make(content)
    output = io.BytesIO()
    img.save(output, 'JPEG', quality=70)
    output.seek(0, 0)
    return output


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
        i['src'] = '/api/get-img?src=' + \
            parse.quote(src) + '&url=' + parse.quote(url)

    res = [str(i) for i in soup.body.contents]
    return ''.join(res).replace('\xa0', '').strip()


def parse_url_path(s):
    return parse.quote(s, safe=";/?:@&=+$,%")


def get_client(endpoint, username, password) -> list:
    hash = hashlib.md5('{}:{}'.format(username, password).encode('utf8'))
    hash = hash.hexdigest()
    params = {'api_key': hash}
    try:
        r = requests.post(endpoint, params=params)
        if r.status_code == requests.codes.OK:
            if r.json()['auth'] == 1:
                return [endpoint, params]
        raise Exception("status_code:{}".format(r.status_code))
    except Exception as e:
        raise e


def resize_img(raw):
    im = Image.open(raw)
    width = im.size[0]
    if width <= 1080:
        height = im.size[1]
    else:
        bili = 1080 / width
        width = int(width * bili)
        height = int(im.size[1] * bili)
    im = im.resize((width, height), Image.ANTIALIAS)
    im = im.convert('RGB')
    output = io.BytesIO()
    im.save(output, 'JPEG', quality=90)
    output.seek(0, 0)
    return output


def get_json_from_fever(endpoint: str, params: dict, api: str):
    r = requests.post(endpoint + '?api' + api, params=params)
    return r.json()
