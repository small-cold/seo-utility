#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

from .baidu_record import query_recorded

"""
职位词收录分析工具，协程方式实现
"""
IS_RUNNING = False

async def import_excel_to_db():
    """
    从Excel表中将数据导入到数据库
    :return:
    """


async def query_and_write(site='www.liepin.com'):
    """
    读取文件，校验并写入数据库
    TODO 改为多线程的，开启20个
    :param site:
    :return:
    """
    print("生成处理数据的函数")

    async def deal_row(**kwargs):
        """
        每行信息的处理函数
        :param row_index: 第几行
        :param row_info: 当前行的数据
        :return:
        """
        print("正在处理数据", kwargs)
        try:
            row_cells = kwargs['row_cells']
            row_index = kwargs['row_index']
        except Exception as e:
            raise e
        else:
            if not row_index and len(row_cells) != 11:
                return
            try:
                if not re.findall("\d+", row_cells[0]):
                    print("格式不合法", row_index, row_cells)
                    return
                code = row_cells[3]
                recorded = await query_recorded(site + code + "/")
                return [row_cells[0], row_cells[2], recorded.is_recorded, recorded.title, recorded.record_time,
                        recorded.url, recorded.record_count]
            except Exception as e:
                raise e

    return deal_row


if __name__ == '__main__':
    pass