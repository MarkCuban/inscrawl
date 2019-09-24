# -*- coding:utf-8 -*-


import requests
import asyncio
import sys
import InsCrawl
from lxml import etree
import click

from InsCrawl import img_urls, video_urls

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

url_list = []
res_list = []

img_urls = []
video_urls = []

user_id = ''

def request_url():

    url = ''

    while True:
        try:
            if url != None and url != '':
                url = yield requests.get(url, headers=HEADER)
            else:
                url = yield None
        except Exception as e:
            print('oops!')
#            raise e

def parse_html(raw):
        
    html = etree.HTML(raw)
    all_tags = html.xpath('//script[@type="text/javascript"]/text()')
    
    for tag in all_tags:
        if tag.strip().startswith('window._sharedData'):
            data = tag.split(' = ')[1][:-1]
            js_data = InsCrawl.open_json(data)
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
    next_url = get_jsDataFromShortCode(node)

    url_list.append(next_url)
    click.echo('parse_sidecar')
    return
    try:
    
        edges = js_data['data']['shortcode_media']['edge_sidecar_to_children']['edges']
        
        for edge in edges:
            node = edge['node']
            typename = node['__typename']
            parse_typename(typename, node)
    except:
        click.echo('something wrong, please check the shortcode, node is '+node['shortcode'])

def parse_image(*arg):    
    global img_urls

    node = arg[0]
    click.echo('parse_img')  
    img_url = node['display_url']
    img_urls.append(img_url)

def parse_video(*arg):
    global video_urls
    click.echo('parse_video')

    node = arg[0]
    next_url = get_jsDataFromShortCode(node)
    
    url_list.append(next_url)
    
    return

    try:
        video_url = js_data['data']['shortcode_media']['video_url']
        video_urls.append(video_url)
    except:
        click.echo('something wrong, please check the shortcode, node is '+node['shortcode'])

def parse_typename(typename, node):
    methods = {
        'GraphSidecar': parse_sidecar,
        'GraphImage': parse_image,
        'GraphVideo': parse_video,
    }

    method = methods.get(typename)
    if method:
        method(node)




parse_JSON_approches = ((parse_index_json, [arg1, arg2], ),
                        (parse_page_json),
                        (),
                        ())


def parse_index_json(json):
    
    global user_id

    user = json['entry_data']['ProfilePage'][0]['graphql']['user']
    edges = user['edge_owner_to_timeline_media']['edges']
    page_info = user['edge_owner_to_timeline_media']['page_info']    
    user_id = user['id']

    for edge in edges:
        typename = edge['node']['__typename']
        parse_typename(typename, edge['node'])

    return page_info  

def parse_page_json(json):

    edges = json['data']['user']['edge_owner_to_timeline_media']['edges']
    page_info = json['data']['user']['edge_owner_to_timeline_media']['page_info']

    for edge in edges:
        typename = edge['node']['__typename']
        parse_typename(typename, edge['node'])

    return page_info


def parseJSON(json):

    try:
        user = json['entry_data']['ProfilePage'][0]['graphql']['user']
        edges = user['edge_owner_to_timeline_media']['edges']
        page_info = user['edge_owner_to_timeline_media']['page_info']    
        user_id = user['id']
    except:
        edges = json['data']['user']['edge_owner_to_timeline_media']['edges']
        page_info = json['data']['user']['edge_owner_to_timeline_media']['page_info']

    for edge in edges:
        typename = edge['node']['__typename']
        parse_typename(typename, edge['node']) 


    return page_info    

def prase_raw_data(raw):
    content = raw.content.decode()
    js_data = InsCrawl.open_json(content)

    if js_data == None:
        js_data = parse_html(content)

    page_info = parseJSON(js_data)

    user_id = InsCrawl.get_user_id()
    if page_info['has_next_page'] == True:
        print('get next url' + user_id)
        nextUrl = InsCrawl.getNextURL(user_id, page_info['end_cursor'])
        url_list.append(nextUrl)               



def parseURL(entre_url):

    global url_list

    print('enter url is '+entre_url)
    url_list.append(entre_url)
#    url_list.append('https://www.instagram.com/JayChou')
    req = request_url()
    res = req.send(None)

    for url in url_list:
        print('start====>{}'.format(url))
        res = req.send(url)
        print('res is ', res)
        prase_raw_data(res)


def showParseRes():

    global img_urls, video_urls

    img_urls = InsCrawl.getIMGURLs()
    video_urls = InsCrawl.getVideoURLS()

    click.echo('-------------------- crawl ins result --------------------')
    click.echo('Images: '+str(len(img_urls))+' Videos: '+str(len(video_urls)))



def download_url():
    global img_urls, video_urls


    pass

def main():

    print('ins crawl start')
    
    url = 'https://www.instagram.com/JayChou/'
    parseURL(url)
    showParseRes()

    download_url()

if __name__ == "__main__":
    main()
