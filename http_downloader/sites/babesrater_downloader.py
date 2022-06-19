import argparse
import sys
import urllib.request
import time
import json
import queue
import threading

import http_downloader

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('person_id',help='person id')
arg_group = arg_parser.add_mutually_exclusive_group(required=True)
arg_group.add_argument('-p','--print',action='store_true',help="just print picture urls")
arg_group.add_argument('-n','--person_name',help="person name",metavar='person_name')
args = arg_parser.parse_args()

req_url = 'https://babesrater.com/PictureDetails/GetMoreInfinite'
resp_attr = 'picUrls'

page_num = 0
pic_urls = []
msg = lambda: '\rprobing album: {0} page(s), {1} picture(s)'.format(page_num,len(pic_urls))

q = queue.Queue()
mutex = threading.Lock()

def get_page_pic_urls(page_id):
    req_data = 'id={0}&page={1}'.format(args.person_id,page_id)
    resp_str = http_downloader.get_remote_data(req_url,data=req_data.encode()).decode()
    res_obj = json.loads(resp_str)
    urls = res_obj[resp_attr]
    return urls

def get_page_pic_urls_worker():
    global q
    global mutex
    global page_num
    global pic_urls

    while True:
        page_id = q.get()
        if page_id is None:
            break
        try:
            urls = get_page_pic_urls(page_id)
        except Exception as e:
            urls = None
        http_downloader.delay()
        if urls:
            with mutex:
                page_num = max(page_num,page_id)
                pic_urls += urls
                print(msg()+' ...',end='',file=sys.stderr)
        q.task_done()

worker_num = 20
thds = [threading.Thread(target=get_page_pic_urls_worker) for i in range(worker_num)]
for thd in thds:
    thd.start()

# probe valid page boundary in main thread

print(msg()+' ...',end='',file=sys.stderr)

l_page_id = 1
try_step = worker_num

while True:
    r_page_id = l_page_id+try_step

    for page_id in range(l_page_id,r_page_id):
        q.put(page_id)

    try:
        urls = get_page_pic_urls(r_page_id)
    except Exception as e:
        urls = None
    http_downloader.delay()

    if not urls:
        break

    with mutex:
        page_num = r_page_id
        pic_urls += urls
        print(msg()+' ...',end='',file=sys.stderr)

    l_page_id = r_page_id+1

q.join()
for i in range(worker_num):
    q.put(None)
for thd in thds:
    thd.join()
print(msg()+' [done]',file=sys.stderr)

pic_urls = ['https:'+pic_url for pic_url in pic_urls]

if args.print:
    print()
    for pic_url in pic_urls:
        print(pic_url)
    print()
    print(msg())
else:
    dest_dir = '[babesrater.com] '+args.person_name
    print(dest_dir)
    http_downloader.download_urls(pic_urls,dest_dir)
