# -*- coding:utf-8 -*-

import requests
from lxml import etree
import click
import json

#https://www.instagram.com/graphql/query/?query_hash=58b6785bea111c67129decbe6a448951&variables=%7B%22id%22%3A%225951385086%22%2C%22first%22%3A12%2C%22after%22%3A%22QVFEREJaVmNlcDJfTUI4bmlhRjlUZVhNTHNoZ1ZBY3JRYXR1QW1wWmxWNVNHMG82MjJDRlZZaGNieTVQaVVESGc4WlpVV3U4b05VTVVISzhKQ3dIY29Beg%3D%3D%22%7D
#https://www.instagram.com/graphql/query/?query_hash=58b6785bea111c67129decbe6a448951&variables=%7B%22id%22%3A%225951385086%22%2C%22first%22%3A12%2C%22after%22%3A%22QVFDVXpDT3l1S0dIRFp5cWY0MVZXVEloYlQyUnBSSkF2MWtrU0x6TkZyS25Kdkk4MEFNVFdWWWxpQllhZEl6Q0VTcVVRZ1AxNU5KOFotYURSRW1oUDBnWA%3D%3D%22%7D
#https://www.instagram.com/graphql/query/?query_hash=58b6785bea111c67129decbe6a448951&variables=%7B%22id%22%3A%225951385086%22%2C%22first%22%3A12%2C%22after%22%3A%22QVFBRktGVktDNHQyOHBZNVMyY2VFWDVVR3pJVEJMYmE1eUVCRTBPblFMTllqd2VmOWtFdzd3QzV5LTFOcVY1X0dnUVNqdmN6Z0tsZW9ZRDBlS2s3MUVvWQ%3D%3D%22%7D
HEADER = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
    'cookie': 'mid=XXtloAAEAAFPDIVBwVQCwlLVlXzB; csrftoken=nVAS2jad5L90qVFEYkHArcD6fmU5GUEn; shbid=12365; shbts=1568607008.3552365; ds_user_id=1285777283; sessionid=1285777283%3AUWUWkFMel6xecU%3A25; rur=FRC; urlgen="{\"45.63.51.0\": 20473}:1iA9FD:UCJzQ03-A-j9c-PuNt8wjncDJbA"',
    'referer': 'https://www.instagram.com/jaychou/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
}

proxy = {
    'http': 'http://127.0.0.1:1087',
    'https': 'http://127.0.0.1:1087'
}

BASE_URL = 'https://www.instagram.com/jaychou/'

img_urls = []

NAME_REFE = '?_nc_ht='

TARGET_STR = '{end_cursor}'
PAGE_URL = 'https://www.instagram.com/graphql/query/?query_hash=58b6785bea111c67129decbe6a448951&variables=%7B%22id%22%3A%225951385086%22%2C%22first%22%3A12%2C%22after%22%3A%22'+TARGET_STR+'%3D%3D%22%7D'


def pic_download(u_download):
    pic_name = ''

    for img_url in img_urls:
        pic_name = img_url.split(NAME_REFE)[0].split('/')[-1]
#        res = requests.get(img_url, headers=HEADER, proxies=proxy)

#        with open(pic_name, 'wb') as f:
#            f.write(res.content)
#            f.close()
        click.echo('save '+pic_name+' finished!')
            
def js_process(js_data):
    
    try:
        edges = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']
        page_info = js_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['page_info']    
    
    except:
        edges = js_data['data']['user']['edge_owner_to_timeline_media']['edges']
        page_info = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']

    for edge in edges:
        img_url = edge['node']['display_url']
        img_urls.append(img_url)

    return page_info

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


def getJSONDataFromURL(cur_url):

    js_data = None
    click.echo(cur_url)
    try:
        res = requests.get(cur_url, headers=HEADER, proxies=proxy)
        click.echo(res)
    except Exception as e:
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

def parseURL(parse_url):
    
    js_data = getJSONDataFromURL(parse_url)

    while True:

        if js_data is None:
            click.echo('Json is empty, find what is wrong...')
            break

        page_info = js_process(js_data)
        if page_info['has_next_page'] == True:
            nextUrl = getNextURL(page_info['end_cursor'])
            js_data = getJSONDataFromURL(nextUrl)
            click.echo('not finished')
        else:
            click.echo('finished'+str(page_info['has_next_page']))
            break


if __name__ == "__main__":
    click.echo('start')
    parseURL(BASE_URL)
    pic_download(None)
    click.echo('end')
