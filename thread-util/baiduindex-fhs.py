#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import threading
from queue import Queue

import requests
import time


class CheckThread(threading.Thread):
    def __init__(self, queue, csvwriter):
        super(CheckThread, self).__init__()
        self.queue = queue
        self.csvwriter = csvwriter

    def run(self):
        while True:
            url = self.queue.get()
            data = self.get_result(url)
            self.extract_data(url, data)
            self.queue.task_done()

    def get_result(self, url, retry=3):
        url = "https://www.baidu.com/s?wd={0}&tn=json".format(url)
        headers = {
            "Host": "www.baidu.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.44 Safari/537.36"
        }
        try:
            r = requests.get(url, headers=headers, timeout=30)
            # r.encoding = 'utf-8'
        except Exception as e:
            print(e.args)
            result = {}
            if retry > 0:
                return self.get_result(url, retry - 1)
        else:
            try:
                result = r.json()
                print(result)
            except Exception as e:
                print(e.args)
                time.sleep(6)  # 出现验证码，程序暂停10分钟重新查询
                return self.get_result(url, retry - 1)
        return result

    def extract_data(self, source_url, data):
        try:
            result_data = data['feed']['entry']
        except KeyError:
            title = ''
            url_indexed = source_url
            ctime = ''
            isindex = '查询出错'
            self.csvwriter.writerow([title, url_indexed, ctime, isindex])
        else:
            if result_data[0]:
                for item in result_data[:-1]:
                    url_indexed = item['url']
                    if url_indexed.find(source_url) > -1:
                        title = item['title']
                        indextime = item['time']
                        ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(indextime))
                        if indextime == 0:
                            isindex = '未索引'
                        else:
                            isindex = '已索引'
                        print(title, url_indexed, ctime, isindex)
                        self.csvwriter.writerow([title, url_indexed, ctime, isindex])
                        break
                else:
                    title = ''
                    url_indexed = source_url
                    ctime = ''
                    isindex = '未收录'
                    self.csvwriter.writerow([title, url_indexed, ctime, isindex])
            else:
                title = ''
                url_indexed = source_url
                ctime = ''
                isindex = '未收录'
                self.csvwriter.writerow([title, url_indexed, ctime, isindex])


if __name__ == '__main__':
    url_list = [url.strip() for url in open('urllist.txt')]  # 待查询url列表，文件必须是utf-8编码，每行一条
    queue = Queue()
    save_file = open('check_url_index.csv', 'a')  # 查询结果保存文件
    fields = ['title', 'url', 'indextime', 'isindex']
    csvwriter = csv.writer(save_file)
    csvwriter.writerow(fields)
    for url in url_list:
        queue.put(url)

    for i in range(15):  # 15为线程数量
        t = CheckThread(queue, csvwriter)
        t.setDaemon(True)
        t.start()
    queue.join()
    save_file.close()
