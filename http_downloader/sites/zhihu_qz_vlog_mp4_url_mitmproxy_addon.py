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
        m = re.search(r'mp4\?', request.url)
        if m:
            m3u8_url = request.url
            if m3u8_url not in self.m3u8_urls:
                self.m3u8_urls.add(m3u8_url)
                for i in range(4):
                    ctx.log.info('*' * 60)
                ctx.log.info(request.url)
                for i in range(4):
                    ctx.log.info('*' * 60)
                print('{} m3u8_url={}'.format(self.id, m3u8_url))
                self.id += 1

addons = [
    Logger()
]
