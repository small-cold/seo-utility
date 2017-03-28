#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import aiohttp
import asyncio

from bs4 import BeautifulSoup

from common.orm import create_pool_


async def search_word_m(word, page=0, retry=3):
    """
    移动端搜索
    经测试，同一个条件最多到75页，每页10个，不可调，pn 每增加10，页码加1
    :param word:
    :param page:
    :param retry:
    :return:
    """
    # 返回的都是HTML，需要解析为为字典使用
    url = "https://m.baidu.com/s"
    headers = {
        "Host": "m.baidu.com",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1"
    }
    params = {'wd': word, 'pn': page * 10}

    try:
        # 这里也得使用异步框架，使用requests会造成协程堵塞
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                result = await response.text()
                return result
    except Exception as e:
        print(e)
        if retry > 0:
            return search_word_m(word, retry - 1)
    return result

async def parse_html(html):
    if not html:
        return
    soup = BeautifulSoup(html, "lxml")


async def main():
    html = await search_word_m('招聘网')
    print(html)

if __name__ == '__main__':
    # 获取EventLoop:
    loop = asyncio.get_event_loop()
    # create_pool_(loop)
    # 查询猎聘两个网站的收录情况，全部
    tasks = [
        main()
    ]
    loop.run_until_complete(asyncio.gather(*tasks))
    # loop.run_until_complete(get_all_recorded(debug=True))
    loop.close()