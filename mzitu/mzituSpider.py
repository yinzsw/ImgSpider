# -*- coding = utf-8 -*-
# @Author: yinzs Wang
# @Time: 2020/12/29 23:08
# @File: mzituSpider.py
# @Software: PyCharm
# @SpiderWebSite: https://www.mzitu.com/

import re
import os
import time
import urllib3


def main(save_path):
    page_urls = get_page_urls()
    download(save_path, page_urls)


def download(save_path, page_urls):
    for page_index, page_url in enumerate(page_urls):
        print(f'第{page_index + 1}页,套图获取中...')
        for img_set in get_img_set(page_url):
            save_img(save_path, img_set)


def save_img(save_path, img_set):
    s_time = time.time()

    [img_title, img_time, img_num, img_urls] = get_img_info(img_set)
    print(f"\t{img_time} {img_title} 共计{img_num}张", end=' | ')
    img_path = f'{save_path}/{img_time} {img_title}'

    if not os.path.exists(img_path):
        os.makedirs(img_path)
    if os.path.exists(img_path) and len(os.listdir(img_path)) == int(img_num):
        return print('已经下载过了lsp!')

    for img in get_img(img_urls):
        [img_bin, img_name] = img
        if not img_bin:
            exit("IP被封,停止请求.请重启网络或待会再试")
        if b"404 Not Found" in img_bin:
            continue
        with open(f'{img_path}/{img_name}', 'wb') as file:
            file.write(img_bin)

    return print(f'耗时{round(time.time() - s_time, 2)}s')


def get_img(img_urls):
    for img_url in img_urls:
        response = ask_url(img_url)
        yield [response, img_url.split('/')[-1]]


def get_img_info(img_set):
    img_title = re.findall(r'<h2 class="main-title">(.*?)</h2>', img_set)[0]
    img_time = re.findall(r'<span>发布于 (\d.*?) ', img_set)[0]
    img_url = re.findall(r'<img class="blur" src="(http.*?)"', img_set)[0]
    img_num = re.findall(r'<span>(\d.*?)</span>', img_set)[-1]

    img_time_int = int(re.sub(r'\D', "", img_time))
    img_num_int = int(img_num)
    img_urls = get_img_urls(img_url, img_time_int, img_num_int)

    img_title = re.sub(r"/|\\|:|\*|\"|<|>|\?|\|", " ", img_title).rstrip()
    img_info = [img_title, img_time, img_num, img_urls]
    return img_info


def get_img_urls(img_url, img_time, img_num):
    img_type = ['imgpc', 'imgwap', 'imgapp', 'imgap']
    img_urls = []
    if img_time > 20140207:
        img_urls = [
            f'{img_url[:-6]}%02d{img_url[-4:]}' % (num + 1)
            for num in range(img_num)
        ]
    else:
        exit("远古套图,不支持下载")
    img_urls = [
        f'{re.sub("imgpc", f"{img_type[2]}", img_url)}'
        for i, img_url in enumerate(img_urls)
    ]
    return img_urls


def get_img_set(page_url):
    page = ask_url(page_url).decode()
    sets = re.findall(r'<li><a href="(http.*?)"', page)
    for set_ in sets:
        response = ask_url(set_)
        yield response.decode()


def get_page_urls():
    start_url = "https://www.mzitu.com"

    print("下载套图页面信息获取中...", end=' ')

    home_page = ask_url(start_url).decode()
    end_page_num = re.findall(r'page.*?>(\d+)</a>', home_page)[-1]
    print(f'共计{end_page_num}页', end=', ')

    end_page = ask_url(f"{start_url}/page/{end_page_num}").decode()
    total_img_set = len(re.findall(r'<span class="time">(.*?)</span>', end_page)) + (int(end_page_num) - 1) * 24
    print(f'共计{total_img_set}套... 获取完毕!')

    page_urls = [
        f'{start_url}/page/{page_index}'
        for page_index in range(1, int(end_page_num) + 1)
    ]
    return page_urls


def ask_url(url):
    """
    模拟用户请求网页
    :param url: 网址 <class 'str'>
    :return: 网页内容 <class 'str'>
    """
    http = ''
    headers = {
        "Referer": "https://app.mmzztt.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        http = urllib3.ProxyManager(proxy)
    except NameError:
        http = urllib3.PoolManager()
    except Exception:
        exit('******未知错误!检查代理******')

    while True:
        try:
            response = http.request('GET', url=url, headers=headers, timeout=4.5).data
        except Exception:
            exit('******请求错误!暂停请求******')
        else:
            if b"429 Too Many Requests" in response:
                print('\n!', end="")
                time.sleep(1.5)
            else:
                return response


if __name__ == '__main__':
    proxy = "http://127.0.0.1:1080"  # SS, SSR, Clash等本地代理

    path = "D:/User"  # 文件保存路径

    main(path)
