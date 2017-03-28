#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time


class BaiduRecord(object):
    def __init__(self, url, title=None, is_recorded='未收录', record_time='--'):
        self.url = url
        self.title = title
        self.is_recorded = is_recorded
        self.record_time = record_time
        self.record_count = 0

    def set_record_time(self, record_time):
        if isinstance(record_time, int):
            self.record_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record_time))
            if record_time > 0:
                self.is_recorded = '已索引'
                self.record_count += 1
        else:
            raise Exception("时间格式不正确：", record_time)


def get_result(url, retry=3):
    url = "https://www.baidu.com/s?wd={0}".format(url)
    headers = {
        "Host": "www.baidu.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.44 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=30)
    except Exception as e:
        print(e)
        result = {}
        if retry > 0:
            return get_result(url, retry - 1)
    else:
        try:
            result = r.json()
            # print(result)
        except Exception as e:
            print(e)
            time.sleep(6)  # 出现验证码，程序暂停一会重新查询
            return get_result(url, retry - 1)
    return result


def query_recorded(source_url):
    data = get_result(source_url)
    baidu_record = BaiduRecord(source_url)
    try:
        result_data = data['feed']['entry']
    except KeyError:
        baidu_record.is_recorded = '查询出错'
    else:
        if result_data[0]:
            for item in result_data[:-1]:
                # print(item)
                url_indexed = item['url']
                if url_indexed.find(source_url) > -1:
                    baidu_record.url = url_indexed
                    baidu_record.title = item['title']
                    baidu_record.set_record_time(item['time'])
                    break

    return baidu_record

if __name__ == '__main__':
    dou = query_recorded('www.liepin.com/zpphp/')
    print(dou.is_recorded)
