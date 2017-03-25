#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import os

import xlrd
import xlwt


async def read_book(file_name, row_call_back=None, col_call_back=None, start=None, limit=None):
    """
    读取Excel文件
    :param start: 开始位置
    :param limit: 结束位置
    :param col_call_back: 按列处理回调函数
    :param row_call_back: 按行处理回调函数
    :param file_name: 读取的文件名
    :return:
    """
    bk = xlrd.open_workbook(file_name)
    for sh_i in range(bk.nsheets):
        sh = bk.sheet_by_index(sh_i)
        await read_sheet(sh, row_call_back=row_call_back, col_call_back=col_call_back, start=start,
                         limit=limit)


async def read_sheet(worksheet, row_call_back=None, col_call_back=None, start=None, limit=None):
    # 获取行数
    nrows = worksheet.nrows
    # 获取列数
    ncols = worksheet.ncols
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
            await row_call_back(index=rowx, cells=worksheet.row_values(rowx))
        await row_call_back(index=None, cells=None)

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
            await col_call_back(index=colx, cells=worksheet.col_values(colx))
        await col_call_back(index=None, cells=None)

    else:
        for rowx in range(nrows):
            print(worksheet.row_values(rowx))


index = 1


def get_row_callback(file_name='result.xls', titles=['序号', '内容']):
    """
    异步写入文件
    :param file_name: 文件名称
    :param titles: 标题内容
    :return:
    """
    workbook = xlwt.Workbook(encoding='UTF-8')
    worksheet = workbook.add_sheet('sheet1')
    cols = len(titles)
    for colx in range(cols):
        worksheet.write(0, colx, titles[colx])
    global index
    index = 1

    async def write_next_row(**kwargs):
        read_index = kwargs.get('index', None)
        cells = kwargs.get('cells', None)
        if not read_index and not cells:
            workbook.save(file_name)
            return
        global index
        print('等待写入文件。', index, cells, worksheet.first_visible_row)
        for i in range(len(cells)):
            worksheet.write(index, i, cells[i])

        index += 1
        return worksheet

    return write_next_row


if __name__ == '__main__':
    # # 获取EventLoop:
    loop = asyncio.get_event_loop()
    # 执行coroutine
    path = os.path.abspath(os.path.join(os.path.dirname("__file__"), '../resource/关键词测试数据.xls'))
    tasks = [read_book(path, row_call_back=get_row_callback(file_name=path.replace('resource', 'output')))]
    print("执行了吗？")
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()
