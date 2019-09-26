# -*- coding:utf-8 -*-


import requests
import asyncio
import sys
from lxml import etree
import click
import time
import json
import threading

THREADING_SUM = 100

PAGE_NUM = 0


HEADER = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
    'cookie': 'mid=XXtloAAEAAFPDIVBwVQCwlLVlXzB; csrftoken=nVAS2jad5L90qVFEYkHArcD6fmU5GUEn; shbid=12365; shbts=1568607008.3552365; ds_user_id=1285777283; sessionid=1285777283%3AUWUWkFMel6xecU%3A25; rur=FRC; urlgen="{\"45.63.51.0\": 20473}:1iA9FD:UCJzQ03-A-j9c-PuNt8wjncDJbA"',
    'referer': 'https://www.instagram.com/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
}

#@asyncio.coroutine
TARGET_STR = '{end_cursor}'
TARGET_ID_STR = '{user_id}'
PAGE_URL = 'https://www.instagram.com/graphql/query/?query_hash=58b6785bea111c67129decbe6a448951&variables=%7B%22id%22%3A%22'+TARGET_ID_STR+'%22%2C%22first%22%3A12%2C%22after%22%3A%22'+TARGET_STR+'%3D%3D%22%7D'

TARGET_SHORTCODE_STR = '{shortcode}'
SIDECAR_URL = 'https://www.instagram.com/graphql/query/?query_hash=865589822932d1b43dfe312121dd353a&variables=%7B%22shortcode%22%3A%22'+TARGET_SHORTCODE_STR+'%22%2C%22child_comment_count%22%3A3%2C%22fetch_comment_count%22%3A40%2C%22parent_comment_count%22%3A24%2C%22has_threaded_comments%22%3Atrue%7D'

url_list = {}
con_request_list = {}
res_list = []

img_urls = {}
video_urls = {}

user_id = {}


PAGE_IDX = {}

REQUEST_IDX = 0

FINISHED_SIGNAL = 'FINISHED'
RETRY_SIGNAL = 'RETRY_LATER'



def open_json(tar):
    js = None
    try:
        js = json.loads(tar, encoding='utf-8')
    except:
        #click.echo('json open failed')
        pass

    return js

def request_url():

    url = ''

    while True:
        try:
            if url != None and url != '':
                res = requests.get(url, headers=HEADER, timeout=1)
                url = yield res
            else:
                url = yield None

#            click.echo('url in generator is '+url)
            if url == 'break':
                click.echo('interation break')
                return                
        except KeyboardInterrupt as e:
            raise e
        except BlockingIOError as e:
            print('Blocking IO error')
            raise e
        except:
            print('I dont know why is here')
#            print('oops!')
#            raise e

def getNextURL(id, str_source):
    #click.echo(str_source)
    res = PAGE_URL.replace(TARGET_STR, str_source[:-2])
    res = res.replace(TARGET_ID_STR, id)
    return res  

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

def parse_sidecar(*arg):
    node = arg[0]
    idx = arg[1]
    next_url = get_jsDataFromShortCode(node)

    url_list[next_url] = idx
    click.echo('parse_sidecar')

def parse_image(*arg):    
    global img_urls

    node = arg[0]
    idx = arg[1]
    click.echo('parse_img')  
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

def prase_raw_data(dict_idx, raw):

    content = raw.content.decode()
    js_data = open_json(content)

    if js_data == None:
        js_data = parse_html(content)

    parseJSON(dict_idx, js_data)

    return True
      
def gloabl_initial(urls):

    global url_list, user_id, PAGE_IDX, img_urls, video_urls
    
    for url in urls:
        url_list[url] = url
        img_urls[url] = []
        video_urls[url] = []
        user_id[url] = []
        PAGE_IDX[url] = 0 
 #       url_list[url].append(url) 


def getNextURL_fromList(index):

    global url_list

    keys = []
    for key in url_list.keys():
        keys.append(key)

    url = None
    idx = None

#    print('lenth of dict is', len(keys), index)

    if index < len(keys):
        url = keys[index]
        idx = url_list[url]
        #print('url and idx is ', url, idx)
    return url, idx

def requestURL():

    global REQUEST_IDX

    url = ''
#    while True:

    try:
        url, idx = getNextURL_fromList(REQUEST_IDX)
        if url is None and idx is None:
            print('yield None None')
            yield FINISHED_SIGNAL, None

#        print('what is going to get, idx is', url, idx)
        res = requests.get(url, headers=HEADER, timeout=1)
        if res.status_code == 200:
            REQUEST_IDX += 1
            #print('what is going to yield, idx is', res, idx)
            yield res, idx 
        else:
            yield RETRY_SIGNAL, idx
    except KeyboardInterrupt:
        raise
    except:
        pass


def requestGenerator():
    yield from requestURL()
       
@asyncio.coroutine
def parseURL(entre_url):

    global url_list, REQUEST_IDX

    print('enter url is ', entre_url)

    res = []

    while True:

        try:
            gen = requestGenerator()

            for res, dict_idx in gen:
#                print('gen is ', res)

                if res is not None:

                    if res == FINISHED_SIGNAL:
                        break
                    elif res == RETRY_SIGNAL:
                        click.echo(RETRY_SIGNAL)                        
                        click.echo('crawl will retry after 60s')
                        time.sleep(60)                        
                    else:   
                        con = prase_raw_data(dict_idx, res)
        except KeyboardInterrupt:
            raise
        except:
            print('I dont know what happend')

        if res == FINISHED_SIGNAL:
            return 

def showParseRes():

    global img_urls, video_urls

    click.echo('-------------------- crawl ins result --------------------')
    
    for key in img_urls.keys():
        click.echo('------------------'+key+'------------------')
        click.echo('Images: '+str(len(img_urls[key]))+' Videos: '+str(len(video_urls[key])))
        click.echo('-------------------------------------------')


def download_url():
    print(threading.current_thread().name+' is running!')

def download_resources():
    global img_urls, video_urls

    t_list = []
    for i in range(THREADING_SUM):
        t = threading.Thread(target=download_url)
        t.start()
        t_list.append(t)


def write_json_files(src, filename):
    with open(filename, 'w+') as f:
        js_str = json.dumps(src, indent=4)
        f.write(js_str)
        f.close()   

def url_save():
    global url_list, img_urls, video_urls

    write_json_files(url_list, 'urls.json')
    write_json_files(img_urls, 'img_urls.json')
    write_json_files(video_urls, 'video_urls.json')


def main():

    print('ins crawl start')
    
    urls = ['https://www.instagram.com/JayChou/',
            'https://www.instagram.com/b_b_j.j/',
            'https://www.instagram.com/cosmosdrone/',
            'https://www.instagram.com/emiliaclarkee/',
            'https://www.instagram.com/nasa/',
            ]

    gloabl_initial(urls)        

    tasks = [parseURL('')]

    loop = asyncio.get_event_loop()    
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

    showParseRes()

    url_save()

#    download_resources()

if __name__ == "__main__":
    main()
