# -*- coding:utf-8 -*-

import requests
from lxml import etree
import click
import json
import sys
import time


DEBUG = False
GET_CERTAIN_ROLL = True
ROLL_MAX = 1
PIC_ROLL = 0

WITH_PROXY = False

RETRY_AFTER = 3600

#https://www.instagram.com/graphql/query/?query_hash=58b6785bea111c67129decbe6a448951&variables=%7B%22id%22%3A%225951385086%22%2C%22first%22%3A12%2C%22after%22%3A%22QVFEREJaVmNlcDJfTUI4bmlhRjlUZVhNTHNoZ1ZBY3JRYXR1QW1wWmxWNVNHMG82MjJDRlZZaGNieTVQaVVESGc4WlpVV3U4b05VTVVISzhKQ3dIY29Beg%3D%3D%22%7D
#https://www.instagram.com/graphql/query/?query_hash=58b6785bea111c67129decbe6a448951&variables=%7B%22id%22%3A%225951385086%22%2C%22first%22%3A12%2C%22after%22%3A%22QVFDVXpDT3l1S0dIRFp5cWY0MVZXVEloYlQyUnBSSkF2MWtrU0x6TkZyS25Kdkk4MEFNVFdWWWxpQllhZEl6Q0VTcVVRZ1AxNU5KOFotYURSRW1oUDBnWA%3D%3D%22%7D
#https://www.instagram.com/graphql/query/?query_hash=58b6785bea111c67129decbe6a448951&variables=%7B%22id%22%3A%225951385086%22%2C%22first%22%3A12%2C%22after%22%3A%22QVFBRktGVktDNHQyOHBZNVMyY2VFWDVVR3pJVEJMYmE1eUVCRTBPblFMTllqd2VmOWtFdzd3QzV5LTFOcVY1X0dnUVNqdmN6Z0tsZW9ZRDBlS2s3MUVvWQ%3D%3D%22%7D
HEADER = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
    'cookie': 'mid=XXtloAAEAAFPDIVBwVQCwlLVlXzB; csrftoken=nVAS2jad5L90qVFEYkHArcD6fmU5GUEn; shbid=12365; shbts=1568607008.3552365; ds_user_id=1285777283; sessionid=1285777283%3AUWUWkFMel6xecU%3A25; rur=FRC; urlgen="{\"45.63.51.0\": 20473}:1iA9FD:UCJzQ03-A-j9c-PuNt8wjncDJbA"',
    'referer': 'https://www.instagram.com/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
}

proxy = {
    'http': 'http://127.0.0.1:',
    'https': 'http://127.0.0.1:',
}

BASE_URL = 'https://www.instagram.com/jaychou/'

img_urls = []
video_urls = []

NAME_REFE = '?_nc_ht='

TARGET_STR = '{end_cursor}'
PAGE_URL = 'https://www.instagram.com/graphql/query/?query_hash=58b6785bea111c67129decbe6a448951&variables=%7B%22id%22%3A%225951385086%22%2C%22first%22%3A12%2C%22after%22%3A%22'+TARGET_STR+'%3D%3D%22%7D'

TARGET_SHORTCODE_STR = '{shortcode}'
SIDECAR_URL = 'https://www.instagram.com/graphql/query/?query_hash=865589822932d1b43dfe312121dd353a&variables=%7B%22shortcode%22%3A%22'+TARGET_SHORTCODE_STR+'%22%2C%22child_comment_count%22%3A3%2C%22fetch_comment_count%22%3A40%2C%22parent_comment_count%22%3A24%2C%22has_threaded_comments%22%3Atrue%7D'


def getNextURL(str_source):
    #click.echo(str_source)
    return PAGE_URL.replace(TARGET_STR, str_source[:-2])

def open_json(tar):
    js = None
    try:
        js = json.loads(tar, encoding='utf-8')
    except:
        pass

    return js

def single_download(type_name):

    download_urls = {
        'pic': img_urls,
        'video': video_urls,
    }

    urls = download_urls.get(type_name)

    pic_name = ''

    for single_url in urls:
        pic_name = single_url.split(NAME_REFE)[0].split('/')[-1]

        if WITH_PROXY is True:
            res = requests.get(single_url, headers=HEADER, proxies=proxy)
        else:
            res = requests.get(single_url, headers=HEADER)

        if DEBUG is False:

            with open(pic_name, 'wb') as f:
                f.write(res.content)
                f.close()

            click.echo('save '+pic_name+' finished!')

def resource_download():

    single_download('pic')
    single_download('video')


def getJSONDataFromURL(cur_url):

    js_data = None
#    click.echo(cur_url)

    while True:
        try:
            if WITH_PROXY is True:
                res = requests.get(cur_url, headers=HEADER, proxies=proxy)
            else:
                res = requests.get(cur_url, headers=HEADER)
#        

            if res.status_code != 200:
                click.echo('request is denied by server, retry after '+str(RETRY_AFTER))
                #click.echo(res.)
                time.sleep(RETRY_AFTER)
                continue
            else:
                break

        except Exception as e:
            click.echo('Check your url...')
            raise e
    
    data = res.content.decode()

    js_data = open_json(data)

    if js_data is None:

        html = etree.HTML(data)
        all_tags = html.xpath('//script[@type="text/javascript"]/text()')
    
        for tag in all_tags:
            #click.echo(tag)
            if tag.strip().startswith('window._sharedData'):
                data = tag.split(' = ')[1][:-1]
                js_data = open_json(data)
                break
            else:
                continue

    return js_data


def get_jsDataFromShortCode(node):

    shortcode = node['shortcode']
    next_url = SIDECAR_URL.replace(TARGET_SHORTCODE_STR, shortcode)
    js_data = getJSONDataFromURL(next_url)

    return js_data

def parse_sidecar(*arg):
    node = arg[0]
    js_data = get_jsDataFromShortCode(node)

    try:
    
        edges = js_data['data']['shortcode_media']['edge_sidecar_to_children']['edges']
        
        for edge in edges:
            node = edge['node']
            typename = node['__typename']
            parse_typename(typename, node, False)
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
    js_data = get_jsDataFromShortCode(node)

    try:
        video_url = js_data['data']['shortcode_media']['video_url']
        video_urls.append(video_url)
    except:
        click.echo('something wrong, please check the shortcode, node is '+node['shortcode'])
    



def parse_typename(typename, node, from_entry):
    methods = {
        'GraphSidecar': parse_sidecar,
        'GraphImage': parse_image,
        'GraphVideo': parse_video,
    }

    method = methods.get(typename)
    if method:
        method(node, from_entry)
            
def js_process(js_data):
    
    from_entry = True
    try:
        edges = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']
        page_info = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['page_info']    
    
    except:
        edges = js_data['data']['user']['edge_owner_to_timeline_media']['edges']
        page_info = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']
        from_entry = False

    for edge in edges:
        typename = edge['node']['__typename']
        parse_typename(typename, edge['node'], from_entry) 


    return page_info

def parseURL(parse_url):
    global PIC_ROLL

    js_data = getJSONDataFromURL(parse_url)
    
    while True:

        if js_data is None:
            click.echo('Json is empty, find what is wrong...')
            break

        page_info = js_process(js_data)

        if page_info['has_next_page'] == True and PIC_ROLL != ROLL_MAX:
            nextUrl = getNextURL(page_info['end_cursor'])
            js_data = getJSONDataFromURL(nextUrl)
            click.echo('one page finished, waiting for parse next page...')
            if GET_CERTAIN_ROLL is True:
                PIC_ROLL += 1
        else:
            click.echo('finished'+str(page_info['has_next_page']))
            break

def getProxy(proxy_port):

    global WITH_PROXY

    if proxy_port != 'None' and proxy_port != 'False':

        WITH_PROXY = True
        proxy['http'] = proxy.get('http')+proxy_port
        proxy['https'] = proxy.get('https')+proxy_port
        click.echo(proxy)
    else:
        WITH_PROXY = False

def getCrawlPages(pages):
    global GET_CERTAIN_ROLL
    global ROLL_MAX

    if pages != 'None' and pages != 'False':
        ROLL_MAX = int(pages)
        GET_CERTAIN_ROLL = True
    else:
        GET_CERTAIN_ROLL = False

def interface():

    click.echo('Images: '+str(len(img_urls))+' Videos: '+str(len(video_urls)))
    value = click.prompt('Start download? Y/N')

    if value == 'Y' or value == 'y':
        return True
    else:
        return False

def main(*arg):

    click.echo('-------------------- crawl ins start ------------------')
    click.echo('-------'+arg[0]+'-------')

    if len(arg) == 3:
        getProxy(arg[2])

    if len(arg) >= 2:
        getCrawlPages(arg[1])

    if len(arg) == 1:
        getProxy('None')
        getCrawlPages('None')
            
    parseURL(arg[0])

    click.echo('-------------------- crawl ins result --------------------')

    is_download = interface()

    if is_download is True:
        click.echo('-------------------- download source start ------------------')
        resource_download()
        click.echo('-------------------- download source end ------------------')
    else:
        click.echo('-------------------- crawl quit --------------------')
    

if __name__ == "__main__":

    if len(sys.argv) == 2:
        main(sys.argv[1])
    elif len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print('python pic.py [URL] [Proxy_port] [pages]')
        