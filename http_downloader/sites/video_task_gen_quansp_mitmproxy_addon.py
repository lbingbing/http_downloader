import os
import sys
import re

from mitmproxy import ctx

from http_downloader import video_task

start_id = int(sys.argv[sys.argv.index(os.path.basename(__file__)) + 1])

class Logger:
    def __init__(self):
        self.video_ids = set()
        self.id = start_id

    def response(self, flow):
        request = flow.request
        response = flow.response
        #m = re.search(r'/(\d+).m3u8\?vkey=', request.url)
        m = re.search(r'/(\w+).m3u8', request.url)
        if m:
            response_str = response.content.decode(encoding='utf-8')
            assert '#EXTM3U' in response_str
            video_id = m.group(1)
            if video_id not in self.video_ids:
                self.video_ids.add(video_id)
                for i in range(4):
                    ctx.log.info('*' * 60)
                ctx.log.info(request.url)
                for i in range(4):
                    ctx.log.info('*' * 60)
                dir_path = str(self.id)
                part_urls = [e.strip() for e in response_str.split('\n')]
                part_urls = list(filter(lambda e: e.startswith('http'), part_urls))
                task = video_task.VideoTask(dir_path)
                task.init(None, 'ts', part_urls)
                task.flush()
                with open(os.path.join(dir_path, 'info.txt'), 'w', encoding='utf-8') as f:
                    print('url:', file=f)
                    print(request.url, file=f)
                    print('response:', file=f)
                    print(response_str, file=f)
                print('{} video_id={}'.format(self.id, video_id))
                self.id += 1

addons = [
    Logger()
]
