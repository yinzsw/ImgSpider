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
import threading


def main():
    global proxy
    global threads_num

    threads_num = 6  # 控制线程数,不宜过大, 不建议修改

    proxy = "http://127.0.0.1:1080"  # SS, SSR, Clash等本地代理

    save_path = "D://ImgSpider/"  # 文件保存路径

    page_urls = get_page_urls()

    download(save_path, page_urls)


def download(save_path, page_urls):
    """
    开始下载
    :param save_path: 保存路径
    :param threads_num: 线程数
    :param page_urls: 页面链接
    :return:
    """
    for page_index, page_url in enumerate(page_urls):
        print(f"正在获取第{page_index + 1}页套图信息...", end=" ")
        res_page = ask_url(page_url).decode()
        set_infos = re.findall(r'<span.*?"(http.*?)".*?>(.*?)</a>.*?class="time">(\d.*?)</span>', res_page)
        print("获取完毕!\n\t开始下载...")
        for set_info in set_infos:
            img_title = set_info[2] + " " + re.sub(r"/|\\|:|\*|\"|<|>|\?|\|", " ", set_info[1]).rstrip()
            save_path_ = f'{save_path}/{img_title}/'
            img_urls = get_img_urls(set_info)
            if not os.path.exists(save_path_):
                os.makedirs(save_path_)
                print(f"\t正在下载: {img_title} | 共计{len(img_urls)}张 |", end=' ')
                start_time = time.time()
                multi_thread(save_path_, img_urls)
                print(f'耗时: {round(time.time() - start_time, 3)}s')
            else:
                print("\t你已经下载过啦!")
            break
        break


def multi_thread(save_path, img_urls):
    """
    开启多线程
    :param save_path: 保存路径
    :param threads_num: 线程数
    :param img_urls: 图片链接组
    :return:
    """
    threads = []
    try:
        lock = threading.BoundedSemaphore(threads_num)
    except NameError:
        lock = threading.BoundedSemaphore(4)
    except Exception:
        print('******未知错误!检查线程数******')
        exit()

    for img_url in img_urls:
        threads.append(threading.Thread(target=multi_thread_save_img, args=(save_path, lock, img_url)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


def multi_thread_save_img(save_path, lock, img_url):
    """
    多线程下载
    :param save_path: 保存路径
    :param lock: 线程锁
    :param img_url: 图片链接
    :return:
    """
    lock.acquire()
    img_name = img_url.split('/')[-1]
    img = ask_url(img_url)
    if b"404 Not Found" not in img:
        with open(f'{save_path}/{img_name}', "wb") as file:
            time.sleep(0.1)
            file.write(img)
    lock.release()


def get_img_urls(set_info):
    """
    获取或构造图片链接
    :param set_info: 套图信息
    :return img_urls: 图片链接组
    """
    res_img = ask_url(set_info[0]).decode()
    img_num = re.findall(r'<span>(\d.*?)</span>', res_img)[-1]
    img_time = re.sub(r'\D', "", set_info[2])
    if int(img_time) > 20140207:
        base_img_url = re.findall(r'<img class="blur" src="(.*?)"', res_img)[0]
        if "imgpc" in base_img_url:
            base_img_url = re.sub("imgpc", "imgapp", base_img_url)
            img_urls = [
                f'{base_img_url[:-6]}%02d{base_img_url[-4:]}' % (num + 1)
                for num in range(int(img_num))
            ]
    else:
        img_urls = []
        for num in range(1, int(img_num) + 1):
            img_page_url = set_info[0] + "/" + num
            res_img_page = ask_url(img_page_url)
            img_url = re.findall(r'<img class="blur" src="(.*?)"', res_img_page)[0]
            if "imgpc" in img_url:
                img_url = re.sub("imgpc", "imgapp", img_url)
            img_urls.append(img_url)
    return img_urls


def get_page_urls():
    """
    选择要下载的数量
    :return:下载套图数量, 页面总数
    """
    start_url = "https://www.mzitu.com/"

    # 获取总数
    print("下载套图页面信息获取中...", end=' ')
    res_start_page = ask_url(start_url).decode()
    max_page_num = re.findall(r'page.*?>(\d+)</a>', res_start_page)[-1]
    print(f'共计{max_page_num}页', end=', ')
    res_end_page = ask_url(f"{start_url}/page/{max_page_num}").decode()
    total_set_num = len(re.findall(r'<span class="time">(.*?)</span>', res_end_page)) + (int(max_page_num) - 1) * 24
    print(f'共计{total_set_num}套... 获取完毕!')

    page_urls = [
        f'{start_url}/page/{page_index}'
        for page_index in range(1, int(max_page_num) + 1)
    ]
    return page_urls


def ask_url(url):
    """
    模拟用户请求网页
    :param url: 网址 <class 'str'>
    :return: 网页内容 <class 'str'>
    """
    headers = {
        "Referer": "https://app.mmzztt.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        http = urllib3.ProxyManager(proxy)
    except NameError:
        http = urllib3.PoolManager()
    except Exception:
        print('******未知错误!检查代理******')
        exit()
    return http.request('GET', url=url, headers=headers).data


if __name__ == '__main__':
    main()
