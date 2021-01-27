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
    filePath = "D://User\\IMG\\"  # 文件保存路径

    threadNum = 7  # 控制线程数,不宜过大, 不建议修改

    startUrl = "https://www.mzitu.com"

    typeUrl = getBaseUrl(startUrl)

    downloadInfo = getDownloadPageInfo(typeUrl)

    download(filePath, typeUrl, downloadInfo, threadNum)


def download(filePath, typeUrl, downloadInfo, threadNum):
    '''
    多线程下载图片并保存
    :param filePath: 保存路径 <class 'str'>
    :param typeUrl: 链接类型 <class 'str'>
    :param downloadInfo: 下载信息列表 <class 'list'>
    :param threadNum: 线程数量 <class 'int'>
    :return: 1 0 None 达到预期下载量  未完全达到预期下载量  完全没有下载
    '''
    # 构造页面链接
    basePageUrl = typeUrl + "/page/{page}"
    pageUrls = [
        basePageUrl.format(page=page)
        for page in range(1, downloadInfo[0] + 1)
    ]

    totalCounter = 0
    downloadCounter = 0

    for pageUrl in pageUrls:
        resPage = askUrl(pageUrl).decode()
        # [(图片链接, 图片时间, 图片标题)]
        imgInfo = re.findall(r'<span><a href="(h.*?)".*?"_blank">(.*?)</a></span>.*?class="time">(.*?)</span>', resPage)
        for info in imgInfo:
            totalCounter += 1
            # 解析下载类型 构造标题 创建路径
            typeDict = {
                "xinggan": "\u6027\u611f", "mm": "\u6e05\u7eaf",
                "japan": "\u65e5\u672c", "taiwan": "\u53f0\u6e7e",
                "hot": "\u6700\u70ed", "best": "\u63a8\u8350"
            }
            fileType = typeDict[typeUrl[typeUrl.rfind("/") + 1:]]
            imgTitle = re.sub(r"/|\\|:|\*|\"|<|>|\?|\|", " ", info[1]).rstrip()
            imgTitle = info[2] + " " + imgTitle
            imgTitlePath = filePath + fileType + "\\" + imgTitle + "\\"
            if not os.path.exists(imgTitlePath):
                os.makedirs(imgTitlePath)
                downloadCounter += 1

                print("\t\u6b63\u5728\u4e0b\u8f7d: %d " % downloadCounter + imgTitle, end=" ")
                imgUrls = getImgUrls(info)

                downloadStar = time.time()
                multiThread(imgTitlePath, imgUrls, threadNum)
                downloadEnd = time.time()

                print("| 耗时%ds" % (downloadEnd - downloadStar))

                if not os.listdir(imgTitlePath):
                    downloadCounter -= 1
                    os.rmdir(imgTitlePath)

                if downloadCounter == downloadInfo[2]:
                    print(
                        "%d\u5957\u5957\u56fe\u4e0b\u8f7d\u5b8c\u6bd5\u002c\u0020\u8bf7\u53bb\u8def\u5f84: %s \u4e0b\u67e5\u770b"
                        % (downloadInfo[2], filePath)
                    )
                    return 1
                elif totalCounter == downloadInfo[1]:
                    print("\u4eca\u5929\u5c31\u5230\u8fd9\u91cc\u5427\u002c\u0020\u8001\u8272\u6279")
                    return 0
            else:
                print("\t\u5df2\u4e0b\u8f7d\u8fc7: " + imgTitle)

    if downloadCounter == 0:
        print(
            "\u771f\u7684\u4e00\u5f20\u4e5f\u6ca1\u6709\u4e86\u002c\u0020\u8001\u8272\u6279\u7b49\u7b49\u518d\u6765\u5427"
        )
    return None


def getImgUrls(info):
    '''
    得到图片链接池
    :param info: 图片信息列表 (图片链接, 图片时间, 图片标题) <class 'tuple'>
    :return: 图片链接池 <class 'list'>
    '''
    # 获取图片数量和图片时间
    resBaseImgPage = askUrl(info[0]).decode()
    imgNum = re.findall(r'<span>(\d.*?)</span>', resBaseImgPage)[-1]
    imgTime = re.sub(r'\D', "", info[2])

    # 获取图片连接池
    imgUrls = []
    print("| 共计", end=" ")
    if int(imgTime) > 20140207:
        baseImgUrl = re.findall(r'<img class="blur" src="(.*?)"', resBaseImgPage)[0]
        if "imgpc" in baseImgUrl:
            baseImgUrl = re.sub("imgpc", "imgapp", baseImgUrl)
        imgUrlsList = [
            baseImgUrl[:-6] + "%02d" % (num + 1) + baseImgUrl[-4:]
            for num in range(int(imgNum))
        ]
        imgUrls.extend(imgUrlsList)
        print("%s张" % imgNum, end=" ")
    else:
        for num in range(1, int(imgNum) + 1):
            imgPageUrl = info[0] + "/" + num
            resImgPage = askUrl(imgPageUrl)
            imgUrl = re.findall(r'<img class="blur" src="(.*?)"', resImgPage)[0]
            if "imgpc" in imgUrl:
                imgUrl = re.sub("imgpc", "imgapp", imgUrl)
            imgUrls.append(imgUrl)
        print("%s张" % imgNum, end=" ")
    return imgUrls


def multiThread(imgTitlePath, imgUrls, threadNum):
    '''
    开启多线程进行下载
    :param imgTitlePath: 图片保存路径 <class 'str'>
    :param imgUrls: 图片链接池 <class 'list'>
    :param threadNum: 线程数量 <class 'int'>
    :return:
    '''
    threads = []
    sema = threading.BoundedSemaphore(threadNum)
    for imgUrl in imgUrls:
        threads.append(
            threading.Thread(target=saveImg, args=(imgTitlePath, imgUrl, sema,))
        )
    for index, thread in enumerate(threads):
        thread.start()
        time.sleep(0.05)

    for thread in threads:
        thread.join()


def saveImg(imgTitlePath, imgUrl, sema):
    '''
    保存图片
    :param imgTitlePath: 图片保存路径 <class 'str'>
    :param imgUrl: 图片链接 <class 'str'>
    :param sema: 用于控制线程数的锁 <class 'threading.BoundedSemaphore'>
    :return:
    '''
    sema.acquire()
    imgName = imgUrl.split('/')[-1]
    img = askUrl(imgUrl)
    if b"404 Not Found" not in img:
        with open(imgTitlePath + imgName, "wb") as file:
            time.sleep(0.03)
            file.write(img)
    sema.release()


def getDownloadPageInfo(typeUrl):
    '''
    得到用户需要下载的套图的数量数量信息
    :param typeUrl: 类型链接 <class 'str'>
    :return: downloadInfo 下载信息列表=[页面总数, 套图总数, 下载套图数] <class 'list'> <class 'int'>
    '''
    downloadInfo = []

    # 判断是否为推荐
    if "best" in typeUrl:
        print(
            "\u63a8\u8350\u5957\u56fe\u6709\u0032\u0034\u5957\u002c\u0020\u4f46\u6bcf\u5929\u4e0d\u4e00\u6837\u002c\u0020\u4f1a\u5168\u90e8\u4e0b\u8f7d"
        )

        downloadInfo.extend([1, 24, 24])
        return downloadInfo

    # 获取套总数
    resStartPage = askUrl(typeUrl).decode()
    pageTotalNum = re.findall(r'page.*?>(\d+)</a>', resStartPage)[-1]
    endPageUrl = typeUrl + "/page/" + pageTotalNum
    resEndPage = askUrl(endPageUrl).decode()
    totalImgNum = len(re.findall(r'<span class="time">(.*?)</span>', resEndPage)) + int(pageTotalNum) * 24

    # 提示信息
    print("\u8bf7\u8f93\u5165\u4f60\u60f3\u4e0b\u8f7d\u7684\u5957\u56fe\u6570\u91cf(1-%d): " % totalImgNum, end="")
    num = inputIntCheck(totalImgNum)

    downloadInfo.extend([int(pageTotalNum), totalImgNum, num])
    return downloadInfo


def askUrl(url):
    '''
    模拟用户请求网页
    :param url: 网址 <class 'str'>
    :return: 网页内容 <class 'str'>
    '''
    header = {
        "Referer": "https://app.mmzztt.com",
        "User-Agent": "Mozilla/5.0"
    }
    http = urllib3.PoolManager()
    response = http.request('GET', url=url, headers=header).data
    return response


def getBaseUrl(startUrl):
    '''
    得到需要类型的基础链接
    :param startUrl: 开始地址 <class 'str'>
    :return: baseUrl 需要类型的地址 <class 'str'>
    '''
    # 定义分类列表
    menuItem = [
        "xinggan", "mm",
        "japan", "taiwan",
        "hot", "best"]

    # 提示信息
    print("\u5206\u7c7b\u5217\u8868: "
          "\n\t1: \u6027\u611f\t\t2: \u6e05\u7eaf"
          "\n\t3: \u65e5\u672c\t\t4: \u53f0\u6e7e"
          "\n\t5: \u6700\u70ed\t\t6: \u63a8\u8350")
    print("\u8bf7\u8f93\u5165\u4f60\u60f3\u4e0b\u8f7d\u7684\u5206\u7c7b\u7d22\u5f15(1-6): ", end="")

    num = inputIntCheck(len(menuItem))

    baseUrl = startUrl + "/" + menuItem[num - 1]

    return baseUrl


def inputIntCheck(intMaxNum):
    '''
    输入一个数进行合法性检验
    :param intMaxNum: 最大值 <class 'int'>
    :return: num 输入的数字 <class 'int'>
    '''
    while True:
        try:
            num = int(input())
        except:
            print("--->这可能不是一个数, 请重新输入: ", end="")
        else:
            if num not in range(1, intMaxNum + 1):
                print("--->数不在给定范围内, 请重新输入: ", end="")
            else:
                return num


if __name__ == '__main__':
    main()
