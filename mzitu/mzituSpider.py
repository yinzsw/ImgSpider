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
from mzitu.CustomFunction import function


def main():
    filePath = "D://User\\IMG\\"

    startUrl = "https://www.mzitu.com"

    typeUrl = getBaseUrl(startUrl)

    downloadInfo = getDownloadPageInfo(typeUrl)

    download(filePath, typeUrl, downloadInfo)


def download(filePath, typeUrl, downloadInfo):
    # 解析下载类型并创建类型路径
    typeDict = {
        "xinggan": "性感", "mm": "清纯",
        "japan": "日本", "taiwan": "台湾",
        "hot": "最热", "best": "推荐"
    }
    fileType = typeDict[typeUrl[typeUrl.rfind("/") + 1:]]
    fileTypePath = filePath + fileType + "\\"
    if not os.path.exists(fileTypePath):
        os.mkdir(fileTypePath)

    # 构造页面链接
    basePageUrl = typeUrl + "/page/{page}"
    pageUrls = [
        basePageUrl.format(page=page)
        for page in range(1, downloadInfo[0] + 1)
    ]

    # 请求链接页面得到图片相关信息
    for pageUrl in pageUrls:
        resPage = askUrl(pageUrl).decode()

        # [(图片链接, 图片时间, 图片标题)]
        imgInfo = re.findall(r'<span><a href="(h.*?)".*?"_blank">(.*?)</a></span>.*?class="time">(.*?)</span>', resPage)

        # 构造图片链接标题并创建标题路径
        for info in imgInfo:
            imgTitle = re.sub(r"/|\\|:|\*|\"|<|>|\?|\|", " ", info[1]).rstrip()
            imgTitle = info[2] + " " + imgTitle
            imgTitlePath = fileTypePath + imgTitle + "\\"
            if not os.path.exists(imgTitlePath):
                os.mkdir(imgTitlePath)

                # 开始下载
                print("\t正在下载: " + imgTitle)
                downloadImg(info, imgTitlePath)
                if function.counter() == downloadInfo[1]:
                    return 0
            else:
                print("\t已下载过: " + imgTitle)


def downloadImg(info, imgTitlePath):
    # 获取图片数量和图片时间
    resBaseImgPage = askUrl(info[0])
    imgNum = re.findall(r'<span>(\d.*?)</span>', resBaseImgPage)[-1]
    imgTime = re.sub(r'\D', "", info[1])

    # 获取图片连接池
    imgUrls = []
    if int(imgTime) > 20140207:
        baseImgUrl = re.findall(r'<img class="blur" src="(.*?)"', resBaseImgPage)[0]
        imgUrlsList = [
            baseImgUrl[:-6] + "%02d" % (num + 1) + baseImgUrl[-4:]
            for num in range(int(imgNum))
        ]
        imgUrls.extend(imgUrlsList)
    else:
        for num in range(1, int(imgNum) + 1):
            imgPageUrl = info[0] + "/" + num
            resImgPage = askUrl(imgPageUrl)
            imgUrl = re.findall(r'<img class="blur" src="(.*?)"', resImgPage)[0]
            imgUrls.append(imgUrl)

    # 启动线程下载图片
    # downloadMultiThread(imgUrls)


# def downloadMultiThread(imgUrls):
#     threads = []
#     for imgUrl in imgUrls:
#         threads.append(
#             threading.Thread(target=saveImg, args=(imgUrl,))
#         )
#     for thread in threads:
#         thread.start()
#
#     for thread in threads:
#         thread.join()

#
# def saveImg(imgUrl):
#     imgName = imgUrl.split('/')[-1]
#     img = askUrl(imgUrl)
#     if b"404 Not Found" not in img:
#         with open(folderName + "\\" + imgTitle + "\\" + imgName, "wb+") as file:
#             file.write(img)
#             file.close()


def getDownloadPageInfo(typeUrl):
    '''
    得到用户需要下载的套图的数量数量信息
    :param typeUrl: 类型链接 <class 'str'>
    :return: downloadInfo 下载信息列表=[页面总数, 下载套图数] <class 'list'> <class 'int'>
    '''
    downloadInfo = []

    # 判断是否为推荐
    if "best" in typeUrl:
        print("推荐套图仅有24套, 但每天可能不同")

        downloadInfo.extend([1, 24])
        return downloadInfo

    # 获取套总数
    resStartPage = askUrl(typeUrl).decode()
    pageTotalNum = re.findall(r'page.*?>(\d+)</a>', resStartPage)[-1]
    endPageUrl = typeUrl + "/page/" + pageTotalNum
    resEndPage = askUrl(endPageUrl).decode()
    totalImgNum = len(re.findall(r'<span class="time">(.*?)</span>', resEndPage)) + int(pageTotalNum) * 24

    # 提示信息
    print("请输入你想下载的套图数量(1-%s): " % totalImgNum, end="")
    num = inputIntCheck(totalImgNum)

    downloadInfo.extend([int(pageTotalNum), num])
    return downloadInfo


def askUrl(url):
    '''
    模拟用户请求网页
    :param url: 网址 <class 'str'>
    :return: 网页内容 <class 'str'>
    '''
    header = {
        "Referer": "https://www.mzitu.com",
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
    print("分类列表: "
          "\n\t1: 性感\t\t2: 清纯"
          "\n\t3: 日本\t\t4: 台湾"
          "\n\t5: 最热\t\t6: 推荐")
    print("请输入你想下载的分类索引(1-6): ", end="")

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
