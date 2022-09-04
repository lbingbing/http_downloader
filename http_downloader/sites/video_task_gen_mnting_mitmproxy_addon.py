import os
import sys
import re

from mitmproxy import ctx

from http_downloader import video_task

start_id = int(sys.argv[sys.argv.index(os.path.basename(__file__)) + 1])

class Logger:
    def __init__(self):
        self.m3u8_urls = set()
        self.id = start_id

    def response(self, flow):
        request = flow.request
        response = flow.response
        m = re.search(r'.com/(\S+/hls/index.m3u8)', request.url)
        if m:
            m3u8_url = m.group(1)
            if m3u8_url not in self.m3u8_urls:
                self.m3u8_urls.add(m3u8_url)
                for i in range(4):
                    ctx.log.info('*' * 60)
                ctx.log.info(request.url)
                for i in range(4):
                    ctx.log.info('*' * 60)
                pos = request.url.index('.com') + 4
                host = request.url[:pos]
                m3u8_url_path = m3u8_url[pos:]
                m3u8_content = response.content.decode(encoding='utf-8')
                part_urls = video_task.get_m3u8_part_urls(host, m3u8_content, None, None, False)
                task = video_task.VideoTask(str(self.id))
                task.init(None, 'ts', part_urls)
                task.flush()
                print('{} m3u8_url={}'.format(self.id, m3u8_url))
                self.id += 1

addons = [
    Logger()
]
