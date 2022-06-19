import os
import sys
import re

from mitmproxy import ctx

from http_downloader import video_url_parse_iqiyi
from http_downloader import video_task

start_id = int(sys.argv[sys.argv.index(os.path.basename(__file__)) + 1])

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
                part_urls = video_url_parse_iqiyi.get_part_urls(response_str)
                task = video_task.VideoTask(dir_path)
                task.init(None, 'ts', part_urls)
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
