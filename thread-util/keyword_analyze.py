#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import xlrd
import xlwt
from baidu_record import query_recorded

IS_RUNNING = False


def read_keyword_info_from_excel(file_name, row_call_back=None, col_call_back=None, start=None, limit=None,
                                 to_put_queue=Queue(), pool_run=None):
    """
    读取Excel文件
    :param pool_run:
    :param to_put_queue:
    :param product_queue:
    :param pool: 线程池
    :param start: 开始位置
    :param limit: 结束位置
    :param col_call_back: 按列处理回调函数
    :param row_call_back: 按行处理回调函数
    :param file_name: 读取的文件名
    :return:
    """
    bk = xlrd.open_workbook(file_name)
    shxrange = range(bk.nsheets)

    try:
        sh = bk.sheet_by_name("sheet1")
    except Exception as e:
        print("读取Excel异常", e)
    else:
        # 获取行数
        nrows = sh.nrows
        # 获取列数
        ncols = sh.ncols
        futures = []
        print("总计行数： %d, 总计列数： %d" % (nrows, ncols))
        if row_call_back and callable(row_call_back):
            print("按行处理数据")
            if start and start > nrows:
                raise Exception("start > row count")
            if not start and not limit:
                rg = range(nrows)
            elif start and not limit:
                rg = range(start, nrows)
            elif start and limit:
                rg = range(start, nrows if start + limit > nrows else start + limit)
            elif not start and limit:
                rg = range(nrows if limit > nrows else limit)

            for rowx in rg:
                if not pool_run:
                    row_call_back(rowx, sh.row_values(rowx))
                else:
                    futures.append(pool.submit(row_call_back, row_index=rowx, row_cells=sh.row_values(rowx)))

        elif col_call_back and callable(col_call_back):
            if start and start > ncols:
                raise Exception("start > col count")
            if not start and not limit:
                lg = range(ncols)
            elif start and not limit:
                lg = range(start, ncols)
            elif start and limit:
                lg = range(start, ncols if start + limit > ncols else start + limit)
            elif not start and limit:
                lg = range(ncols if limit > ncols else limit)

            for colx in lg:
                if not pool_run:
                    col_call_back(colx, sh.col_values(colx))
                else:
                    futures.append(pool.submit(col_call_back, col_index=colx, col_cells=sh.col_values(colx)))

        else:
            for rowx in range(nrows):
                print(sh.row_values(rowx))
        # 遍历结果，将已完成的结果添加到队列
        while True:
            if len(futures) == 0:
                break
            for future in futures:
                try:
                    if future.done():
                        result = future.result(timeout=10)
                        if result:
                            to_put_queue.put(result, timeout=0.01)
                            futures.remove(future)
                except Exception as e:
                    print('等待结果发生异常', e)
                    futures.remove(future)
            time.sleep(3)

        global IS_RUNNING
        IS_RUNNING = False
        print("生产完成")


def query_and_write(site='www.liepin.com'):
    """
    查询并写入文件
    TODO 改为多线程的，开启20个
    :param site:
    :return:
    """
    print("生成处理数据的函数")

    def deal_row(**kwargs):
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
                recorded = query_recorded(site + code + "/")
                return [row_cells[0], row_cells[2], recorded.is_recorded, recorded.title, recorded.record_time,
                        recorded.url, recorded.record_count]
            except Exception as e:
                raise e

    return deal_row


def write_result_to_excel(file_name='result.xls', to_get_queue=Queue()):
    workbook = xlwt.Workbook(encoding='UTF-8')
    worksheet = workbook.add_sheet('sheet1')
    worksheet.write(0, 0, "ID")
    worksheet.write(0, 1, "职位词")
    worksheet.write(0, 2, "收录情况")
    worksheet.write(0, 3, "收录页Title")
    worksheet.write(0, 4, "收录时间")
    worksheet.write(0, 5, "收录URL")
    worksheet.write(0, 6, "收录数量")
    index = 1
    global IS_RUNNING
    while True:
        if not IS_RUNNING and to_get_queue.empty():
            break
        try:
            result = to_get_queue.get(block=False)
        except Exception as e:
            print("获取结果异常", e, '歇息一下')
            time.sleep(1)
        else:
            if not result:
                continue
            print("结果文件正在写入 index = ", index, result)
            for i in range(len(result)):
                worksheet.write(index, i, result[i])
            index += 1
            to_get_queue.task_done()
    workbook.save(file_name)
    print("写入文件完成")

if __name__ == '__main__':
    pool = ThreadPoolExecutor(max_workers=18)
    product_queue = Queue()
    IS_RUNNING = True
    consumer = pool.submit(write_result_to_excel, file_name='全国职位词PC收录情况.xls', to_get_queue=product_queue)
    producer = pool.submit(read_keyword_info_from_excel, "测试.xls",
                           row_call_back=query_and_write(site="www.liepin.com/zp"),
                           to_put_queue=product_queue,
                           start=1,
                           limit=1000,
                           pool_run=pool)
    running_seconds = 0
    while True:
        if producer.done() and consumer.done():
            print("处理完成")
            break
        print("已经休息", running_seconds, producer.done(), consumer.done())
        running_seconds += 1
        time.sleep(1)
