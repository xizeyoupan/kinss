import io
import re
from urllib import parse

import miniflux
import qrcode
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


def get_config(path: str):
    path = path + '/config'
    with open(path, 'a+', encoding='utf8') as f:
        f.seek(0)
        return f.read()


def get_client(server_url, username, password):
    client = miniflux.Client(server_url, username, password)
    try:
        client.me()
        return client
    except Exception as e:
        raise e


def set_config(path, url):
    path = path + '/config'
    with open(path, 'w', encoding='utf8') as f:
        f.write(url)


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
