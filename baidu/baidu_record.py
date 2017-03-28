#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import time
import hashlib

from common.orm import Model, IntField, StringField, TinyTextField, FloatField, TinyIntField, create_pool_

"""
百度收录查询工具，协程方式实现
"""


# 百度收录信息，对应table类
class BaiduRecordedEntity(Model):
    __table__ = 'recorded_baidu'

    id = IntField(primary_key=True, ddl='int(11)')
    # 收录的完整URL
    url = StringField(ddl='varchar(300)')
    # URL MD5
    url_encode = StringField(ddl='varchar(40)')
    # 收录标题
    title = TinyTextField(default='')
    # 百度返回的一段文本，看样子像是页面中的一些关键字
    abs = TinyTextField(default='')
    # 记录时间
    recorded_time = FloatField(default=0)
    # 域名，从URL中提取出来，做后续分析使用
    domain = StringField(ddl='varchar(150)', default='')
    # 记录状态，做后续分析使用
    kind = TinyIntField()

    create_at = FloatField(default=time.time)
    modify_at = FloatField(default=time.time)


class BaiduRecord(object):
    def __init__(self, url, title=None, is_recorded='未收录', record_time='--'):
        self.url = url
        self.title = title
        self.is_recorded = is_recorded
        self.record_time = record_time
        self.record_time_show = None
        self.record_count = 0

    def set_record_time(self, record_time):
        if isinstance(record_time, int):
            self.record_time = record_time
            self.record_time_show = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(record_time))
            if record_time > 0:
                self.is_recorded = '已收录'
                self.record_count += 1
        else:
            raise Exception("时间格式不正确：", record_time)


async def get_result(word, page=1, retry=3, mobile=False):
    """
    经测试，同一个条件最多到75页，每页10个，不可调，pn 每增加10，页码加1
    https://www.baidu.com/s?wd=site%3Awww.liepin.com
    &pn=40
    &oq=site%3Awww.liepin.com
    &tn=baiduhome_pg
    &ie=utf-8
    &usm=1
    &rsv_idx=2
    &rsv_pq=ea3cd4a000015995
    &rsv_t=7b63d8hiGSLtf4Q1yA6oQy3EnwTNaGAxkZc%2Fh1rE8ltAjOXcarGGbbDrKQAo4nqpR9yJ
    &rsv_page=1
    :param mobile: 是否移动端搜索
    :param word:
    :param page:
    :param retry:
    :return:
    """
    # 返回的都是HTML，需要解析为为字典使用
    if mobile:
        url = "https://m.baidu.com/s"
        headers = {
            "Host": "m.baidu.com",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1"
        }
        params = {'wd': word, 'pn': page}
    else:
        url = "https://www.baidu.com/s"
        headers = {
            "Host": "www.baidu.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.44 Safari/537.36"
        }
        params = {'wd': word, 'tn': 'json', 'pn': page}
    try:
        # 这里也得使用异步框架，使用requests会造成协程堵塞
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                result = await response.json()
                return result
                # r = await aiohttp.request('GET', url, params=params, headers=headers)
                # r = await loop.run_in_executor(None, requests.get, url, {'headers': headers, 'timeout': 30})
    except Exception as e:
        print(e)
        if retry > 0:
            return get_result(url, retry - 1)
    return result


async def get_all_recorded(word='site:www.baidu.com', page_num=0, page_size=10, is_mobile=False, debug=False):
    error_count = 0
    total = 0
    start_time = time.time()
    while (total == 0 or page_num < total + page_size) and error_count < 10:
        if debug and page_num == page_size * 3:
            break
        print('分页查询，当前进度:', str(page_num) + '/' + str(total), '关键词', word, '总计耗时：', time.time() - start_time, sep='，')
        data = await get_result(word, mobile=is_mobile, page=page_num)
        # print(data)
        # 如果为空，则继续等待
        if not data:
            error_count += 1
            continue
        try:
            feed = data['feed']  # 根节点feed
            total = feed['all']  # 总数
            recorded_list = feed['entry']
        except Exception as e:
            print('发生异常情况', e, '分页查询，当前页码:', page_num, '，分页数量:', page_size, ',错误次数:', error_count)
            error_count += 1
        else:
            if recorded_list and len(recorded_list) > 0:
                for item in recorded_list:
                    item_url = item.get('url', '')
                    if not item_url or item_url == '':
                        continue
                    baidu_record = BaiduRecordedEntity()
                    baidu_record.url = item_url
                    md5 = hashlib.md5()
                    md5.update(item_url.encode('utf-8'))
                    baidu_record.url_encode = md5.hexdigest()
                    baidu_record.title = item.get('title', '')
                    baidu_record.abs = item.get('abs', '')
                    baidu_record.recorded_time = item.get('time', '')
                    # print(baidu_record)
                    try:
                        await baidu_record.save()
                    except Exception as e:
                        print("保存失败", e, baidu_record, '分页查询，当前页码:', page_num, '分页数量:', page_size,
                              '错误次数:', error_count, sep='，')
            else:
                print("获得数据为空。", '，分页查询，当前页码:', page_num, '，分页数量:', page_size, ',错误次数:', error_count)
            page_num += page_size
    print('所有收录查询完成，关键词', word, '总计耗时：', (time.time() - start_time) / 60, '分钟', sep='--')


async def query_recorded(source_url):
    # await asyncio.sleep(3)  # 阻塞直到协程sleep(2)返回结果
    data = await get_result(source_url)
    baidu_record = BaiduRecord(source_url)
    if not data:
        return baidu_record
    try:
        # print(data)
        result_data = data['feed']['entry']
    except KeyError:
        baidu_record.is_recorded = '查询出错'
    else:
        if result_data[0]:
            for item in result_data[:-1]:
                print(item)
                url_indexed = item['url']
                if url_indexed.find(source_url) > -1:
                    baidu_record.url = url_indexed
                    baidu_record.title = item['title']
                    baidu_record.set_record_time(item['time'])
                    break

    return baidu_record


async def test(url):
    print("开始查询 word", url)
    dou = await query_recorded(url)
    print("查询结果", url, dou.is_recorded)

async def test():
    pass

if __name__ == '__main__':
    # 获取EventLoop:
    loop = asyncio.get_event_loop()
    create_pool_(loop)
    # 执行coroutine
    # 查询猎聘两个网站的收录情况，全部
    tasks = [
        # test()
        get_all_recorded(),
        #  get_all_recorded(word='site:m.liepin.com', is_mobile=True), # 还用不了，移动端返回的不是JSON
    ]
    loop.run_until_complete(asyncio.gather(*tasks))
    # loop.run_until_complete(get_all_recorded(debug=True))
    loop.close()
