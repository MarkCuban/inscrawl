# -*- coding:utf-8 -*-
import requests
import asyncio

from lxml import etree

PAGE_NUM = 0

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

HEADER = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
    'cookie': 'mid=XXtloAAEAAFPDIVBwVQCwlLVlXzB; csrftoken=nVAS2jad5L90qVFEYkHArcD6fmU5GUEn; ds_user_id=1285777283; sessionid=1285777283%3AUWUWkFMel6xecU%3A25; shbid=12365; shbts=1570324023.8633752; rur=FRC; urlgen="{\"45.32.251.0\": 20473}:1iHrqf:sYnjYctwHDIoLIb5kAWfWzuQxUE"',
    'referer': 'https://www.instagram.com/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
}

TARGET_STR = '{end_cursor}'
TARGET_ID_STR = '{user_id}'
PAGE_URL = 'https://www.instagram.com/graphql/query/?query_hash=58b6785bea111c67129decbe6a448951&variables=%7B%22id%22%3A%22'+TARGET_ID_STR+'%22%2C%22first%22%3A12%2C%22after%22%3A%22'+TARGET_STR+'%3D%3D%22%7D'

TARGET_SHORTCODE_STR = '{shortcode}'
SIDECAR_URL = 'https://www.instagram.com/graphql/query/?query_hash=865589822932d1b43dfe312121dd353a&variables=%7B%22shortcode%22%3A%22'+TARGET_SHORTCODE_STR+'%22%2C%22child_comment_count%22%3A3%2C%22fetch_comment_count%22%3A40%2C%22parent_comment_count%22%3A24%2C%22has_threaded_comments%22%3Atrue%7D'


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

def request_url(url):
    yield 

    print('url {} request start'.format(url))
    if url is not None:    
        res = requests.get(url, headers=HEADER, proxies=proxy)
    
        if res.status_code == 200:
            return res.content.decode()
        else:
            pass   

    return None  

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

def parse_url(content):
    yield

    print('url {} parse start'.format(url))
    js_data = open_json(content)

    if js_data == None:
        js_data = parse_html(content)

    parseJSON(None, js_data)

@asyncio.coroutine
def request_and_parse(url):
 
    while True:
        try:
            res_list = yield from request_url(url)
        except Exception as e:
            print(e)

        if res_list is None:
            continue

        yield from parse_url(res_list)
        print('url is parsed over', url)
        break 
    url_list.popitem(url)

def initial():
    for url in URLS:
        url_list[url] = url

def crawl():

    initial()
    loop = asyncio.get_event_loop()

    tasks = []

    print(url_list)
    while True:

        if len(url_list) == 0:
            break

        for key in url_list.keys():
            gen = request_and_parse(key)
            tasks.append(gen)

        loop.run_until_complete(asyncio.wait(tasks))

    loop.stop()    

def main():  
    crawl()

if __name__ == "__main__":
    main()
