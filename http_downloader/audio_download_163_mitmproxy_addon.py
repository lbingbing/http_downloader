import os
import sys

from mitmproxy import ctx

import http_downloader.http_downloader

start_id = int(sys.argv[sys.argv.index(os.path.basename(__file__)) + 1])

class Logger:
    def __init__(self):
        self.audio_urls = set()
        self.id = start_id

    def response(self, flow):
        request = flow.request
        response = flow.response
        if request.url.endswith(('m4a', 'mp3')):
            audio_url = request.url
            if audio_url not in self.audio_urls:
                self.audio_urls.add(audio_url)
                for i in range(4):
                    ctx.log.info('*' * 60)
                ctx.log.info(request.url)
                for i in range(4):
                    ctx.log.info('*' * 60)
                ext = audio_url[audio_url.rindex('.'):]
                http_downloader.http_downloader.download_url(audio_url, '{}{}'.format(self.id, ext))
                print('{} audio_url={}'.format(self.id, audio_url))
                self.id += 1

addons = [
    Logger()
]
