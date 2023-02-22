import os
import sys
import re
import collections

from mitmproxy import ctx

from http_downloader import video_task

start_id = int(sys.argv[sys.argv.index(os.path.basename(__file__)) + 1])

def get_part_urls(line, merge_part_urls=True):
    line = line.replace('\\\\/', '/').replace('\\/', '/')
    s = line.index('#EXTM3U')
    e = line.index('"', s)
    urls = line[s:e].split('\\n')
    urls = list(filter(lambda e: e.startswith('http://'), urls))

    if merge_part_urls:
        files = collections.OrderedDict()
        for url in urls:
            m = re.match(r'http:.*/(\w+)\.ts\?start=\d+&end=(\d+)&', url)
            assert m
            name = m.group(1)
            end = m.group(2)
            if name not in files:
                files[name] = {}
                files[name]['url'] = url
            files[name]['end'] = end
        urls = []
        for file_info in files.values():
            urls.append(re.sub(r'end=\d+', 'end={}'.format(file_info['end']), file_info['url']))

    return urls

class Logger:
    def __init__(self):
        self.tvids = set()
        self.id = start_id

    def response(self, flow):
        request = flow.request
        response = flow.response
        m = re.search(r'dash\?tvid=(\d+)', request.url)
        if m:
            response_str = response.content.decode(encoding='utf-8')
            assert 'm3u8":"#EXTM3U' in response_str
            tvid = m.group(1)
            if tvid not in self.tvids:
                self.tvids.add(tvid)
                for i in range(4):
                    ctx.log.info('*' * 60)
                ctx.log.info(request.url)
                for i in range(4):
                    ctx.log.info('*' * 60)
                dir_path = str(self.id)
                part_urls = get_part_urls(response_str)
                task = video_task.VideoTask(dir_path)
                task.init(str(self.id), 'ts', None, part_urls)
                task.flush()
                with open(os.path.join(dir_path, 'info.txt'), 'w', encoding='utf-8') as f:
                    print('url:', file=f)
                    print(request.url, file=f)
                    print('response:', file=f)
                    print(response_str, file=f)
                print('{} tvid={}'.format(self.id, tvid))
                self.id += 1

addons = [
    Logger()
]
