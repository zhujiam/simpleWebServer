import asyncio
import os
import mimetypes
import requests
from parse_header import HTTPHeader

html_header = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>Index of /</title><body><h1>Index of /</h1><hr><pre><ul>'
html_a = '<li><a href=%s>%s</a></li>'
html_tail = '</ul></pre></hr></body></html>\r\n'

async def dispatch(reader, writer):
    header = HTTPHeader()
    i = 1
    requestType = ''
    while True:
        data = await reader.readline()
        print(data)
        dataArray = data.decode().split('\r\n')
        flag = dataArray[0].split(' ')
        while i:
            requestType = flag[0]
            i = i - 1
        message = data.decode()
        print(message)
        header.parse_header(message)
        if data == b'\r\n':  # 判断请求报文是否读取完全
            break
    # 拒绝除 get 和 head 之外的 http 请求
    if ((requestType.lower() != 'get') & (requestType.lower() != 'head')):
        writer.writelines([
            b'HTTP/1.0 405 OK\r\n',
            b'Content-Type:text/html; charset=utf-8\r\n',
            b'Connection: close\r\n',
            b'\r\n',
            b'<html><body>Method Not Allowed<body></html>\r\n',
            b'\r\n'
            ])
        return

    Path = './' + header.get('path')
    if (os.path.isfile(Path)):
        fileName = os.path.split(Path)[1]
        tyPe = mimetypes.guess_type(fileName)[0]
        f = open(Path, 'rb')
        size = os.path.getsize(Path)
        print(size)
        lines = f.read(size)
        
        writer.writelines([
            b'HTTP/1.0 200 OK\r\n',
            b'Content-Type:' + tyPe.encode('utf-8') + b'charset=utf-8\r\n',
            b'Content-Length: %d'%(size) + b'charset=utf-8\r\n',
            b'Connection: close\r\n',
            b'\r\n',
            lines,
            b'\r\n'
        ])
    else:
        try:
            content = ''
            dataArray = os.listdir('./' + header.get('path'))
            for item in dataArray:
                content += html_a%(Path + '/' + item, item)
            html = ''
            html += html_header
            html += content
            html += html_tail
            writer.writelines([
                b'HTTP/1.0 200 OK\r\n',
                b'Content-Type:text/html; charset=utf-8\r\n',
                b'Connection: close\r\n',
                b'\r\n',
                html.encode('utf-8'),
                b'\r\n'
            ])
        except FileNotFoundError:
            writer.writelines([
                b'HTTP/1.0 404 OK\r\n',
                b'Content-Type:text/html; charset=utf-8\r\n',
                b'Connection: close\r\n',
                b'\r\n',
                b'<html><body>404 NOT FOUND<body></html>\r\n',
                b'\r\n'
            ])
    await writer.drain()
    writer.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(dispatch, '127.0.0.1', 8080, loop=loop)
    server = loop.run_until_complete(coro)

    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
