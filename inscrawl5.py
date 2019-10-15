# -*- coding:utf-8 -*-
import requests
import asyncio
import json
import collections
from collections.abc import Awaitable
from requests import Response
import signal
import os
from lxml import etree
import aiohttp
import click
import time
from enum import Enum


PAGE_NUM = 0

WITH_PROXY = False

MAX_XIECHENG_NUM = 200

URLS = [    'https://www.instagram.com/JayChou/',
            'https://www.instagram.com/b_b_j.j/',
            #'https://www.instagram.com/cosmosdrone/',
            #'https://www.instagram.com/emiliaclarkee/',
            'https://www.instagram.com/nasa/',
            'https://www.instagram.com/hannah_quinlivan/',
            #'https://www.instagram.com/stephencurry30/',
            'https://www.instagram.com/ashleybenson/',
            #'https://www.instagram.com/diawboris/',
            #'https://www.instagram.com/rogerfederer/',
            #'https://www.instagram.com/sleepinthegardn/',
            'https://www.instagram.com/chloegmoretz/',
            #'https://www.instagram.com/victoriassecret/',

    ]

DIR_REFE = 'https://www.instagram.com/'

HEADER = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
    #'cookie': 'mid=XXtloAAEAAFPDIVBwVQCwlLVlXzB; csrftoken=nVAS2jad5L90qVFEYkHArcD6fmU5GUEn; ds_user_id=1285777283; sessionid=1285777283%3AUWUWkFMel6xecU%3A25; shbid=12365; shbts=1570324023.8633752; rur=FRC; urlgen="{\"45.32.251.0\": 20473}:1iHrqf:sYnjYctwHDIoLIb5kAWfWzuQxUE"',
    'cookie':'mid=XYGS8AALAAH12IYJnCT-JypBze3K; csrftoken=0uEQ7aLA7MF6t63qRz7xSyRgJqFEMMyG; ds_user_id=1285777283; sessionid=1285777283%3AyBt1gTgrOB5kiA%3A1; shbid=12365; shbts=1571031009.7997015; rur=FRC; urlgen="{\"122.248.18.6\": 4352}:1iJwhC:XubXTHx6aTsDMaZwcTf1iPcu0Ok"',
    'referer': 'https://www.instagram.com/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
}

TARGET_STR = '{end_cursor}'
TARGET_ID_STR = '{user_id}'
PAGE_URL = 'https://www.instagram.com/graphql/query/?query_hash=58b6785bea111c67129decbe6a448951&variables=%7B%22id%22%3A%22'+TARGET_ID_STR+'%22%2C%22first%22%3A12%2C%22after%22%3A%22'+TARGET_STR+'%3D%3D%22%7D'

TARGET_SHORTCODE_STR = '{shortcode}'
SIDECAR_URL = 'https://www.instagram.com/graphql/query/?query_hash=865589822932d1b43dfe312121dd353a&variables=%7B%22shortcode%22%3A%22'+TARGET_SHORTCODE_STR+'%22%2C%22child_comment_count%22%3A3%2C%22fetch_comment_count%22%3A40%2C%22parent_comment_count%22%3A24%2C%22has_threaded_comments%22%3Atrue%7D'

NAME_REFE = '?_nc_ht='

url_list = {}

img_urls = {}
video_urls = {}

Img_Statistics = {}
Video_Statistics = {}

Error_Statistics = []

user_id = {}
PAGE_IDX = {}

proxy = {
    'http': 'http://127.0.0.1:1087',
    'https': 'http://127.0.0.1:1087',
}

loop = None
task_num = 0
xchelper = []

class XIECHENG_STATE(Enum):
    STATE_IDLE = 0
    STATE_BUSY = 1

class XIECHENG_Helper():
    
    def __init__(self, id):
        self.id = id
        self.state = XIECHENG_STATE.STATE_IDLE
        self.running = True

    def getID(self):
        return self.id    

    def setState(self, state):
        self.state = state

    def getState(self):
        return self.state

    def isBusy(self):
        return True if self.state == XIECHENG_STATE.STATE_BUSY else False

    def setRunning(self, running):
        self.running = running
    
    def getRunning(self):
        return self.running

def open_json(tar):
    js = None
    try:
        js = json.loads(tar, encoding='utf-8')
    except:
        #click.echo('json open failed')
        pass

    return js

def parse_html(raw):
        
    html = etree.HTML(raw)
    all_tags = html.xpath('//script[@type="text/javascript"]/text()')
    
    for tag in all_tags:
        if tag.strip().startswith('window._sharedData'):
            data = tag.split(' = ')[1][:-1]
            #print('tag is ', data)
            js_data = open_json(data)
            if js_data is not None:
                break
        else:
            continue 
    return js_data

def get_jsDataFromShortCode(node):

    shortcode = node['shortcode']
    next_url = SIDECAR_URL.replace(TARGET_SHORTCODE_STR, shortcode)
    return next_url

def getNextURL(id, str_source):
    #click.echo(str_source)
    res = PAGE_URL.replace(TARGET_STR, str_source[:-2])
    res = res.replace(TARGET_ID_STR, id)
    return res  

def parse_sidecar(*arg):
    node = arg[0]
    idx = arg[1]
    next_url = get_jsDataFromShortCode(node)

    url_list[next_url] = idx
    print('parse_sidecar')

def parse_image(*arg):    
    global img_urls

    node = arg[0]
    idx = arg[1]
    print('parse_img')  
    img_url = node['display_url']
    img_urls[idx].append(img_url)


def parse_video(*arg):

    node = arg[0]
    idx = arg[1]

    next_url = get_jsDataFromShortCode(node)
    
    url_list[next_url] = idx

def parse_typename(typename, node, dict_idx):
    methods = {
        'GraphSidecar': parse_sidecar,
        'GraphImage': parse_image,
        'GraphVideo': parse_video,
    }

    method = methods.get(typename)
    if method:
        method(node, dict_idx)

def parse_data_jason(json, dict_idx):

    edges = json['data']['shortcode_media']['edge_sidecar_to_children']['edges']
        
    for edge in edges:
        node = edge['node']
        typename = node['__typename']
        parse_typename(typename, node, dict_idx)

    return None   

def parse_video_json(json, dict_idx):
     
    video_url = json['data']['shortcode_media']['video_url']
    video_urls[dict_idx].append(video_url)

    return None

def parse_index_json(json, dict_idx):
    
    global user_id, PAGE_IDX

    user = json['entry_data']['ProfilePage'][0]['graphql']['user']
    edges = user['edge_owner_to_timeline_media']['edges']
    page_info = user['edge_owner_to_timeline_media']['page_info']    
    user_id[dict_idx] = user['id']

    for edge in edges:
        typename = edge['node']['__typename']
        parse_typename(typename, edge['node'], dict_idx)

    if page_info is not None:
        if page_info['has_next_page'] == True:

            if PAGE_NUM == 0 or PAGE_NUM > 1:
                nextUrl = getNextURL(user_id[dict_idx], page_info['end_cursor'])
                url_list[nextUrl] = dict_idx
                PAGE_IDX[dict_idx] += 1 
                print('page idx is', PAGE_IDX)

    return page_info

def parse_page_json(json, dict_idx):

    global PAGE_IDX, PAGE_NUM

    edges = json['data']['user']['edge_owner_to_timeline_media']['edges']
    page_info = json['data']['user']['edge_owner_to_timeline_media']['page_info']

    for edge in edges:
        typename = edge['node']['__typename']
        parse_typename(typename, edge['node'], dict_idx)

    #click.echo('parse_page_json') 
    if page_info is not None:
        if page_info['has_next_page'] == True:
            nextUrl = getNextURL(user_id[dict_idx], page_info['end_cursor'])
            print('The {} {} page has been parsed'.format(dict_idx, PAGE_IDX[dict_idx]+1))

            if PAGE_NUM > 0:
                if PAGE_NUM == 1:
                    pass
                else:
                    if PAGE_IDX[dict_idx] < PAGE_NUM-1:
                        url_list[nextUrl] = dict_idx
                        PAGE_IDX[dict_idx] += 1
            else:
                url_list[nextUrl] = dict_idx
                PAGE_IDX[dict_idx] += 1       

    return None

parse_JSON_approches = [parse_page_json, parse_index_json, parse_video_json, parse_data_jason]


def parseJSON(dict_idx, json):

    for approch in parse_JSON_approches:

        try:
            approch(json, dict_idx)
            click.echo('json parsed by ' + approch.__name__)
        except KeyboardInterrupt as e:
            raise e            
        except Exception as ec:
           # print(ec)
           #click.echo('cant parse, find next parse function')
            pass

    return None

def parse_url(content, url):
    
    #print('url {} parse start'.format(url))
    js_data = open_json(content)

    if js_data == None:
        js_data = parse_html(content)

    parseJSON(url, js_data)

def requestPointGet(url, header, proxy):
    return requests.get(url, headers=HEADER, proxies=proxy)

async def request_url(url):
    #print('url {} request start'.format(url))

    loop = asyncio.get_event_loop()
    if url is not None:  

        if WITH_PROXY == True: 
            res = await loop.run_in_executor(None, requestPointGet, url, HEADER, proxy)
        else:
            res = await loop.run_in_executor(None, requests.get, url, HEADER)
    return res
    
'''
    print('start ', idx)
    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.google.com') as resp:
            print('get resp ', idx, resp)
            data = await resp.read()
            print('data: ', data)
            
    url_list.pop(url)
'''   


def save_img(con, fname, folder):

    if not folder.endswith('/'):
        folder += '/'
    with open(folder+fname, 'wb') as f:
        f.write(con)


async def download_single(url, idx):

    fname = url.split(NAME_REFE)[0].split('/')[-1]
    dirname = getdirname(idx)
    folder = os.getcwd() + '/' + dirname

    while True:

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=HEADER) as resp:
                    data = await resp.read()
                    if resp.status == 200:
                        save_img(data, fname, folder)
                    elif resp.status == 404:
                        print('server error maybe, quit parse')
                        break
                    else:
                        for i in range(0, 40):
                            print('retry it after {} seconds'.format((40-i)*10))
                            await asyncio.sleep(10)
                        continue
                                        
        except Exception as e:
            print('something happend')
            print(e)
            continue
        break   

    print(fname+' is saved')         

def initial():

    for url in URLS:
        makedir(url)
        url_list[url] = url
        img_urls[url] = []
        Img_Statistics[url] = []
        video_urls[url] = []
        Video_Statistics[url] = []
        user_id[url] = []
        PAGE_IDX[url] = 0    

def showParseRes():

    global Img_Statistics, Video_Statistics

    print('-------------------- crawl ins result --------------------')
    
    for key in Img_Statistics.keys():
        print('------------------'+key+'------------------')
        print('Images: '+str(len(Img_Statistics[key]))+' Videos: '+str(len(Video_Statistics[key])))
        print('-------------------------------------------')             

def write_json_files(src, filename):
    with open(filename, 'w+') as f:
        js_str = json.dumps(src, indent=4)
        f.write(js_str)   

def url_save():
    global img_urls, video_urls

    #write_json_files(url_list, 'urls.json')
    write_json_files(img_urls, 'img_urls.json')
    write_json_files(video_urls, 'video_urls.json')


def getdirname(url):
    res = url.split(DIR_REFE)[1]
    res = res.split('/')[0]
    return res

def makedir(key):
    dirname = getdirname(key)
    folder = os.getcwd() + '/' + dirname
    if not os.path.exists(folder):
        os.makedirs(folder)



def interface():
    value = click.prompt('Start download? Y/N')

    if value == 'Y' or value == 'y':
        return True
    else:
        return False

class URL_TYPE(Enum):
    TYPE_URL = 0
    TYPE_IMG = 1
    TYPE_VIEDO = 2

def getURLFromURLPool():
    global url_list
    url = list(url_list.keys())[0]
    idx = url_list[url]
    url_list.pop(url)
    return url, idx, URL_TYPE.TYPE_URL

def getURLFromDownloadPool(urltype):
    global img_urls, video_urls
    
    if urltype == URL_TYPE.TYPE_IMG:
        urls = img_urls
        stat = Img_Statistics
    else:
        urls = video_urls
        stat = Video_Statistics

    url = None
    idx = None
    for lst in urls:
        if len(urls[lst]) > 0:
            url = urls[lst][0]
            urls[lst].remove(url)
            stat[lst].append(url)
            idx = lst
            break
    
    return url, idx, urltype

def getDownloadURLLength(urltype):

    if urltype == URL_TYPE.TYPE_IMG:
        urls = img_urls
    else:
        urls = video_urls

    length = 0
    for lst in urls:
        length += len(urls[lst])

    return length

def getURLFromPool():
    
    url = None
    idx = None
    urltype = None

    if len(url_list) > 0:
        url, idx, urltype = getURLFromURLPool()
    elif getDownloadURLLength(URL_TYPE.TYPE_IMG) > 0:
        url, idx, urltype =  getURLFromDownloadPool(URL_TYPE.TYPE_IMG)   
    elif getDownloadURLLength(URL_TYPE.TYPE_VIEDO) > 0:
        url, idx, urltype =  getURLFromDownloadPool(URL_TYPE.TYPE_VIEDO)

    return url, idx, urltype

async def request_and_parse(url, idx):

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=HEADER) as resp:
#                    print('status: ', resp.status)
                    
                    if resp.status == 200:
                        data = await resp.read()
                        parse_url(data, idx)
                    elif resp.status == 404:
                        print('server error maybe, quit parse')
                        break    
                    else:
                        for i in range(0, 40):
                            print('retry it after {} seconds'.format((40-i)*10))
                            await asyncio.sleep(10)
                        continue

        except Exception as e:
            print('something happens on: ', url)
            print(e)
            await asyncio.sleep(5)

        break

async def request_and_parse_with_proxy(url, idx):

    while True:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.get(url, headers=HEADER, verify_ssl=False) as resp:
#                    print('status: ', resp.status)
                    
                    if resp.status == 200:
                        data = await resp.read()
                        parse_url(data, idx)
                    elif resp.status == 404:
                        Error_Statistics[idx].append(url)
                        print('server error maybe, quit parse')
                        break    
                    else:
                        for i in range(0, 40):
                            print('retry it after {} seconds'.format((40-i)*10))
                            await asyncio.sleep(10)
                        continue

        except Exception as e:
            Error_Statistics[idx].append(url)
            print('something happens on: ', url)
            print(e)
            await asyncio.sleep(5)

        break

async def download_single_with_proxy(url, idx):

    fname = url.split(NAME_REFE)[0].split('/')[-1]
    dirname = getdirname(idx)
    folder = os.getcwd() + '/' + dirname

    while True:

        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.get(url, headers=HEADER, verify_ssl=False) as resp:
                    data = await resp.read()
                    if resp.status == 200:
                        save_img(data, fname, folder)
                    elif resp.status == 404:
                        Error_Statistics[idx].append(url)
                        print('server error maybe, quit parse')
                        break
                    else:
                        for i in range(0, 40):
                            print('retry it after {} seconds'.format((40-i)*10))
                            await asyncio.sleep(10)
                        continue
                                        
        except Exception as e:
            Error_Statistics[idx].append(url)
            print('download error on: ', url)
            print(e)
            continue
        break   

    print(fname+' is saved')

def sendStopSignal():
    
    running = False
    res = False
    for xc in xchelper:
        if xc.isBusy():
            running = True
            break

    if running == False:
        if len(url_list) == 0 and getDownloadURLLength(URL_TYPE.TYPE_IMG) == 0 and getDownloadURLLength(URL_TYPE.TYPE_VIEDO) == 0:
            for xc in xchelper:
                xc.setRunning(False)
            res = True
        else:
            running = True

    return res
            

async def crawl_url(id):

    global loop

    while True:

        url, idx, url_type = getURLFromPool() 

        if url is not None:
            xchelper[id].setState(XIECHENG_STATE.STATE_BUSY)
            if WITH_PROXY == True:
                if url_type == URL_TYPE.TYPE_URL:
                    await request_and_parse_with_proxy(url, idx)
                else:
                    await download_single_with_proxy(url, idx)
            else:
                if url_type == URL_TYPE.TYPE_URL:
                    await request_and_parse(url, idx)
                else:
                    await download_single(url, idx)
        else:
            xchelper[id].setState(XIECHENG_STATE.STATE_IDLE)
            await asyncio.sleep(1)

        if id == 0:
            sendStopSignal()

        if xchelper[id].getRunning() == False:
            break
#                loop.stop()

def url_save():

    write_json_files(Error_Statistics, 'error.json')
    write_json_files(Img_Statistics, 'img_urls.json')
    write_json_files(Video_Statistics, 'video_urls.json')

def main(): 

    global loop

    tasks = []
    
    initial()

    for i in range(0, MAX_XIECHENG_NUM):
        xc = XIECHENG_Helper(i)
        gen = crawl_url(xc.getID())
        tasks.append(gen)
        xchelper.append(xc)

    loop = asyncio.get_event_loop()
#    loop.create_task(asyncio.wait(tasks)) 
#    loop.run_forever()
    loop.run_until_complete(asyncio.wait(tasks))
    showParseRes()
    url_save()
#    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()

if __name__ == "__main__":
    main()
