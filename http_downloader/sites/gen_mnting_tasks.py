import os
import re
import json
import time
import multiprocessing.pool

from http_downloader import http_downloader
from http_downloader import video_task

page_file_fmt = 'page{}.html'
video_play_html_url_fmt = 'https://{}/vod/play/id/{}/sid/1/nid/1.html'
origin_url = 'https://api.xiusebf.com'
referer_url = 'https://api.xiusebf.com'

def worker(args):
    host, page_id, video_id, video_page_id, video_name = args
    dest_dir = str(video_id)
    success = False
    error_msg = ''
    if os.path.isdir(dest_dir):
        if os.path.isfile(os.path.join(dest_dir, 'task.json')):
            success = True
    else:
        os.mkdir(dest_dir)
    if not success:
        video_play_html_url = video_play_html_url_fmt.format(host, video_page_id)
        try:
            video_play_html = http_downloader.get_remote_data(video_play_html_url, try_num=5).decode('utf-8')
            with open(os.path.join(dest_dir, 'video_play.html'), 'w', encoding='utf-8') as f:
                f.write(video_play_html)
            success = True
        except Exception as e:
            success = False
            error_msg = '{}\n{}'.format(e, 'fail to download video play html')
        if success:
            m = re.search('"url":"((https://(\S+?.com))/(\S+?)/(\S+?)/index.m3u8)"', video_play_html.replace('\\/', '/'))
            m3u8_url1 = m.group(1)
            m3u8_host1 = m.group(2)
            m3u8_host2 = m.group(3)
            timestamp_suffix = ''
            #timestamp_suffix = '?_t={}'.format(int(time.time()))
            try:
                m3u8_content1 = http_downloader.get_remote_data(m3u8_url1+timestamp_suffix, headers={'Host': m3u8_host2, 'Origin': origin_url, 'Referer': referer_url}, try_num=5).decode('utf-8')
                with open(os.path.join(dest_dir, 'm3u8_1.txt'), 'w', encoding='utf-8') as f:
                    f.write(m3u8_content1)
                success = True
            except Exception as e:
                success = False
                error_msg = '{}\n{}'.format(e, 'fail to download m3u8 file 1')
            if success:
                m3u8_url2 = next(e for e in m3u8_content1.split('\n') if e.endswith('.m3u8'+timestamp_suffix))
                m3u8_url2 = m3u8_host1 + m3u8_url2
                try:
                    m3u8_content2 = http_downloader.get_remote_data(m3u8_url2, headers={'Host': m3u8_host2, 'Origin': origin_url, 'Referer': referer_url}, try_num=5).decode('utf-8')
                    with open(os.path.join(dest_dir, 'm3u8_2.txt'), 'w', encoding='utf-8') as f:
                        f.write(m3u8_content2)
                    success = True
                except Exception as e:
                    success = False
                    error_msg = '{}\n{}'.format(e, 'fail to download m3u8 file 2')
                if success:
                    if '#EXT-X-KEY' in m3u8_content2:
                        m = re.search(r'#EXT-X-KEY:METHOD=AES-128,URI="(.+?)"', m3u8_content2)
                        key_url = m3u8_host1 + m.group(1)
                        try:
                            key = http_downloader.get_remote_data(key_url, headers={'Host': m3u8_host2, 'Origin': origin_url, 'Referer': referer_url}, try_num=5)
                            success = True
                        except Exception as e:
                            success = False
                            error_msg = '{}\n{}'.format(e, 'fail to download m3u8 file 2')
                    else:
                        key = None
                        success = True
                    if success:
                        lines = m3u8_content2.split('\n')
                        urls = [line for line in lines if line.endswith('ts')]
                        urls = [m3u8_host1 + e for e in urls]
                        task = video_task.VideoTask(dest_dir)
                        task.init(video_name, 'ts', key, urls)
                        task.flush()
        time.sleep(0.1)
    return success, error_msg

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='host')
    parser.add_argument('page_num', type=int, help='page num')
    parser.add_argument('--mp', type=int, default=0, help='multiprocessing')
    args = parser.parse_args()

    tasks = []
    video_id = 1
    for page_id in range(1, args.page_num+1):
        page_file = page_file_fmt.format(page_id)
        with open(page_file, encoding='utf-8') as f:
            s = f.read()
        for video_page_id, video_name in re.findall('<a href="/vod/detail/id/(\w+?).html" target="_blank"><h3>(.+?)</h3>', s):
            tasks.append((args.host, page_id, video_id, video_page_id, video_name))
            video_id += 1
    if args.mp:
        with multiprocessing.pool.Pool(args.mp) as pool:
            for (host, page_id, video_id, video_page_id, video_name), (success, error_msg) in zip(tasks, pool.imap(worker, tasks, chunksize=8)):
                print('video {}, page {}, {}'.format(video_id, page_id, video_name))
                if not success:
                    print(error_msg)
    else:
        for host, page_id, video_id, video_page_id, video_name in tasks:
            success, error_msg = worker((host, page_id, video_id, video_page_id, video_name))
            print('video {}, page {}, {}'.format(video_id, page_id, video_name))
            if not success:
                print(error_msg)
