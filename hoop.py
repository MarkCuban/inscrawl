# -*- coding: utf-8 -*-
import requests
import re
from lxml import etree
import asyncio

URL = 'https://bbs.hupu.com/bxj'


HEADER = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6',
    'cookie': '_dacevid3=48041a02.6b00.c382.6294.dfaccfa98f7d; acw_tc=781bad0a15686074630481748e2f2ee8879e86d0d76b003f3ccc883a50a5c7; __gads=ID=838dee7eded8a702:T=1568607465:S=ALNI_MYRm-Fa5yv1Gw8Iv_PL09WVna722Q; _cnzz_CV30020080=buzi_cookie%7C48041a02.6b00.c382.6294.dfaccfa98f7d%7C-1; PHPSESSID=f9dc03ce43265476931ef9e1426c42b9; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2216d384abfab4a3-0efce491273bb3-38657501-1296000-16d384abfac9fe%22%2C%22%24device_id%22%3A%2216d384abfab4a3-0efce491273bb3-38657501-1296000-16d384abfac9fe%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_referrer_host%22%3A%22%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%7D%7D; _fmdata=8gagdUb59obRPu%2BO450nIoRSgrVzWDAelhMablGm6QaTHwCR4jqjP12zikHBbeJlrar48%2BfujLT1JLAIjbI%2Fsn5LU%2Be5izIpOpwuW%2FK7LYY%3D; _HUPUSSOID=4f40d233-dd06-4a46-9730-de83d7c77021; _CLT=868ae16f150cf61ab926af24b4aa60be; u=30231353|5LqP5pys5Lmw5Y2W6ams5YyW6IW+|5863|3d5a6caabd1debddda38e74993903e55|bd1debddda38e749|aHVwdV83NjY2MTk1NjFjZDk1Y2Zh; us=59686f0178485e3d5352faebc64f03f8dbacc1ff7cc0bba6283d21afcd175e223bb3dc3d75ec46f43a2c25077f7a554b24d95d2f1f2143a1f786da3f0c87f515; ua=29064413; Hm_lvt_39fc58a7ab8a311f2f6ca4dc1222a96e=1569477274,1569478332,1569478341,1569478347; __dacevst=4223e93f.f006ce28|1569480823284; Hm_lpvt_39fc58a7ab8a311f2f6ca4dc1222a96e=1569479024',
    'referer': 'https://www.hoopchina.com/bxj',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
}

COMPARE_STR_START = '步行街主干道共'
COMPARE_STR_END = '主题'

file_list = []

PARSE_TITLE_STR = '//a[@class="truetit"]'

def request_url():
    url = None

#    while True:
    if url == None:
        url = yield None

    if url is not None:    
        res = requests.get(url, headers=HEADER)
    
        if res.status_code == 200:
            yield res
        else:
            yield None

def request_url_test(url):
#   url = None

#    while True:
    if url == None:
        yield None

    if url is not None:    
        res = requests.get(url, headers=HEADER)
    
        if res.status_code == 200:
            yield res
        else:
            yield None            

        
def detectindex():

    gen = request_url()

    while True:
        gen.send(None)
        res = None

        try:
            res = gen.send(URL)
        except StopIteration:
            pass

        gen.close()
        raw = res.content.decode()
        html = etree.HTML(raw)

        if html is not None:
            break

    tags = html.xpath('//div[@class="pageright"]/text()')

    for tag in tags:
        tag = tag.strip('\r\n')
        if tag.startswith(COMPARE_STR_START):
            tag = tag.split(COMPARE_STR_START)[1]
            tag = tag.split(COMPARE_STR_END)[0]
            title_sum = tag

    tags = html.xpath(PARSE_TITLE_STR)
          
    return title_sum, len(tags)

def requestGen(url):
    yield from request_url_test(url)

def parse_titile(raw, idx):
    
    html = etree.HTML(raw)
    tags = html.xpath(PARSE_TITLE_STR)

    print('page {} has {} titles'.format(idx, len(tags)))
    f = file_list[0]
    try:
#        f.write('page {} has {} titles'.format(idx, len(tags)))
        for tag in tags:
            if tag.text is not None:
                if len(tag.text) > 0 and tag.text != '\n':
                    print(tag.text)
#                f.write(tag.text)
    except Exception as e:
        raise e
    

            
@asyncio.coroutine
def requestURL(url):
    print('url is ', url)
    f_name = url.split('-')[1]
    html = b''

    try:
        res_list = requestGen(url)
        print('yield res is ', res_list)
    except Exception as e:
        print(e)
    print('url is parsed over', url)

def crawl(t_sum, t_page):
    print('sum title is ', t_sum)
    print('one page has {} titles'.format(t_page)) 

    pages = int(t_sum)//int(t_page)
    filename_lst = ['title']
    open_files(filename_lst)
    tasks = []
    for i in range(2):
        url = URL+'-{}'.format(str(i+1))
        gen = requestURL(url)
        tasks.append(gen)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.stop()
    close_files()

def open_files(filename_lst):
    for f in filename_lst:
        with open(f+'.txt', 'w+') as fl:
            file_list.append(fl)

def close_files():
    for f in file_list:
        f.close()

def main():
    title_sum, title_page = detectindex()
    crawl(title_sum, title_page)


if __name__ == "__main__":
    main()
