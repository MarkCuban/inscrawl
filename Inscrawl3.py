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

PAGE_NUM = 1

WITH_PROXY = True

URLS = [    'https://www.instagram.com/JayChou/',
            #'https://www.instagram.com/b_b_j.j/',
            #'https://www.instagram.com/cosmosdrone/',
            #'https://www.instagram.com/emiliaclarkee/',
            #'https://www.instagram.com/nasa/',
            'https://www.instagram.com/hannah_quinlivan/',
            #'https://www.instagram.com/stephencurry30/',
            #'https://www.instagram.com/ashleybenson/',
            #'https://www.instagram.com/diawboris/',
            #'https://www.instagram.com/rogerfederer/',
            #'https://www.instagram.com/sleepinthegardn/',
            #'https://www.instagram.com/chloegmoretz/',
    ]

DIR_REFE = 'https://www.instagram.com/'

HEADER = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
    #'cookie': 'mid=XXtloAAEAAFPDIVBwVQCwlLVlXzB; csrftoken=nVAS2jad5L90qVFEYkHArcD6fmU5GUEn; ds_user_id=1285777283; sessionid=1285777283%3AUWUWkFMel6xecU%3A25; shbid=12365; shbts=1570324023.8633752; rur=FRC; urlgen="{\"45.32.251.0\": 20473}:1iHrqf:sYnjYctwHDIoLIb5kAWfWzuQxUE"',
    'cookie':'mid=XXtloAAEAAFPDIVBwVQCwlLVlXzB; csrftoken=nVAS2jad5L90qVFEYkHArcD6fmU5GUEn; shbid=12365; shbts=1568607008.3552365; ds_user_id=1285777283; sessionid=1285777283%3AUWUWkFMel6xecU%3A25; rur=FRC; urlgen="{\"45.63.51.0\": 20473}:1iA9FD:UCJzQ03-A-j9c-PuNt8wjncDJbA"',
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

user_id = {}
PAGE_IDX = {}

proxy = {
    'http': 'http://127.0.0.1:1087',
    'https': 'http://127.0.0.1:1087',
}

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

    return None

parse_JSON_approches = [parse_page_json, parse_index_json, parse_video_json, parse_data_jason]


def parseJSON(dict_idx, json):

    for approch in parse_JSON_approches:

        try:
            approch(json, dict_idx)
            click.echo('json parsed by ' + approch.__name__)
        except KeyboardInterrupt as e:
            raise e            
        except:
           #click.echo('cant parse, find next parse function')
            pass

    return None

def parse_url(content, url):
    
    print('url {} parse start'.format(url))
    js_data = open_json(content)

    if js_data == None:
        js_data = parse_html(content)

    parseJSON(url, js_data)

def requestPointGet(url, header, proxy):
    return requests.get(url, headers=HEADER, proxies=proxy)

async def request_url(url):
    print('url {} request start'.format(url))

    loop = asyncio.get_event_loop()
    if url is not None:  

        if WITH_PROXY == True: 
            res = await loop.run_in_executor(None, requestPointGet, url, HEADER, proxy)
        else:
            res = await loop.run_in_executor(None, requests.get, url, HEADER)
    return res
'''
        if res.status_code == 200:
            return res.content.decode()
        else:
            pass
'''
    
   
async def request_and_parse(url, idx):
    res = None
    while True:
        try:
            res = await request_url(url)
        except Exception as e:
            print(e)

        if isinstance(res, Response):
            if res.status_code == 200:
                parse_url(res.content.decode(), idx)
            else:
                print('not 200, try again')
        else:
            continue

        break
        
    print('url is parsed over', url)     
    url_list.pop(url)

def save_img(con, fname, folder):

    if not folder.endswith('/'):
        folder += '/'
    with open(folder+fname, 'wb') as f:
        f.write(con)


async def download_single(url, idx):
    res = None

    fname = url.split(NAME_REFE)[0].split('/')[-1]
    dirname = getdirname(idx)
    folder = os.getcwd() + '/' + dirname

    while True:

        try:
            res = await request_url(url)
        except Exception as e:
            print(e)

        if isinstance(res, Response):
            if res.status_code == 200:
                save_img(res.content, fname, folder)
            else:
                print('not 200, try again')            

def initial():

    for url in URLS:
        url_list[url] = url
        img_urls[url] = []
        video_urls[url] = []
        user_id[url] = []
        PAGE_IDX[url] = 0    

def showParseRes():

    global img_urls, video_urls

    print('-------------------- crawl ins result --------------------')
    
    for key in img_urls.keys():
        print('------------------'+key+'------------------')
        print('Images: '+str(len(img_urls[key]))+' Videos: '+str(len(video_urls[key])))
        print('-------------------------------------------')             

def my_handler():
    print('stopping')
    for task in asyncio.Task.all_tasks():
        task.cancel()

def write_json_files(src, filename):
    with open(filename, 'w+') as f:
        js_str = json.dumps(src, indent=4)
        f.write(js_str)   

def url_save():
    global img_urls, video_urls

    #write_json_files(url_list, 'urls.json')
    write_json_files(img_urls, 'img_urls.json')
    write_json_files(video_urls, 'video_urls.json')

def crawl(loop):

    initial()
    tasks = []

    print(url_list)
    while True:

        if len(url_list) == 0:
            break

        for key in url_list.keys():
            gen = request_and_parse(key, url_list[key])
            tasks.append(gen)
        
        try:
            
            loop.run_until_complete(asyncio.wait(tasks))
             
        except Exception as e:
            print(e)

    
    showParseRes()  

def down_init():
    pass

def getdirname(url):
    res = url.split(DIR_REFE)[1]
    res = res.split('/')[0]
    return res

def makedir(key):
    dirname = getdirname(key)
    folder = os.getcwd() + '/' + dirname
    if not os.path.exists(folder):
        os.makedirs(folder)



def url_down(loop):

    down_init()
    tasks = []

    for urls in img_urls, video_urls:
        for key in urls.keys():
            makedir(key)
            for url in urls[key]:
                gen = download_single(url, key)
                tasks.append(gen)

        try: 
            loop.run_until_complete(asyncio.wait(tasks))  
        except Exception as e:
            print(e)

def main(): 

    loop = asyncio.get_event_loop()

    crawl(loop)
    url_save()
    url_down(loop)

    loop.close()

if __name__ == "__main__":
    main()
