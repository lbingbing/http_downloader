import os
import json
import urllib.parse

from . import http_downloader

class VideoTask:
    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.task_path = os.path.join(dir_path, 'task.json')
        self.name = None
        self.ext = None
        self.key = None
        self.part_urls = None
        self.download_done = None
        self.decrypt_done = None
        self.merge_done = None

    def init(self, name, ext, key, part_urls):
        assert all(urllib.parse.urlparse(e).path.endswith(ext) for e in part_urls), 'inconsistent ext and part_urls'
        if not os.path.isdir(self.dir_path):
            os.mkdir(self.dir_path)
        self.name = name
        self.ext = ext
        self.key = key
        self.part_urls = part_urls
        self.download_done = False
        self.decrypt_done = key is None
        self.merge_done = False

    def load(self):
        with open(self.task_path, encoding='utf-8') as f:
            task = json.load(f)
        self.name = task['name']
        self.ext = task['ext']
        self.key = None if task['key'] is None else bytes.fromhex(task['key'])
        self.part_urls = task['part_urls']
        self.download_done = task['download_done']
        self.decrypt_done = task['decrypt_done']
        self.merge_done = task['merge_done']

    def flush(self):
        task = {}
        task['name'] = self.name
        task['ext'] = self.ext
        task['key'] = None if self.key is None else self.key.hex()
        task['part_urls'] = self.part_urls
        task['download_done'] = self.download_done
        task['decrypt_done'] = self.decrypt_done
        task['merge_done'] = self.merge_done
        with open(self.task_path, 'w', encoding='utf-8') as f:
            json.dump(task, f, indent=4)

    def get_part_num(self):
        return len(self.part_urls)

    def get_part_ids(self):
        return [i for i in range(1, len(self.part_urls)+1)]

    def get_part_file_name(self, part_id):
        return 'p{}.{}'.format(part_id, self.ext)

    def get_encrypted_part_file_name(self, part_id):
        return 'p{}_enc.{}'.format(part_id, self.ext)

def get_m3u8_part_urls(host, m3u8_content, m3u8_file, m3u8_url, indirect_url):
    if m3u8_content:
        lines = m3u8_content.splitlines()
    elif m3u8_file:
        with open(m3u8_file) as f:
            lines = f.read().splitlines()
    elif m3u8_url:
        url = m3u8_url
        if host:
            url = host + '/' + url
        lines = http_downloader.get_remote_data(url).decode().splitlines()
    else:
        assert 0

    if indirect_url:
        part_urls = [line for line in lines if line.endswith('.m3u8')]
        assert len(part_urls) == 1
        url = part_urls[0]
        if host:
            url = host + '/' + url
        lines = http_downloader.get_remote_data(url).decode().splitlines()

    part_urls = [line for line in lines if urllib.parse.urlparse(line).path.endswith('ts')]
    if host:
        part_urls = [host + '/' + e for e in part_urls]

    return part_urls

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('task_dir', help='task dir')
    parser.add_argument('video_name', help='video name')
    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument('--m3u8_file', help='m3u8 file')
    src_group.add_argument('--m3u8_url', help='m3u8 url')
    parser.add_argument('--indirect_url', action='store_true', help='indirect m3u8 url')
    parser.add_argument('--host', help='host')
    args = parser.parse_args()

    part_urls = get_m3u8_part_urls(args.host, None, args.m3u8_file, args.m3u8_url, args.indirect_url)
    task = VideoTask(args.task_dir)
    task.init(args.video_name, 'ts', None, part_urls)
    task.flush()
