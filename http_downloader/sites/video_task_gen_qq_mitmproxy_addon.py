import os
import sys
import re
import json

from mitmproxy import ctx

from http_downloader import video_task

start_id = int(sys.argv[sys.argv.index(os.path.basename(__file__)) + 1])

class Logger:
    def __init__(self):
        self.vids = set()
        self.id = start_id

    def response(self, flow):
        request = flow.request
        response = flow.response
        if request.url == 'https://vd6.l.qq.com/proxyhttp':
            response_str = response.content.decode(encoding='utf-8')
            response_json_obj = json.loads(response_str)
            if 'vinfo' in response_json_obj:
                post_data_str = request.content.decode(encoding='utf-8')
                post_data_json_obj = json.loads(post_data_str)
                vinfoparam = post_data_json_obj['vinfoparam']
                vid_pos0 = vinfoparam.index('&vid=') + len('&vid=')
                vid_pos1 = vinfoparam.index('&', vid_pos0)
                vid = vinfoparam[vid_pos0:vid_pos1]
                if vid not in self.vids:
                    self.vids.add(vid)
                    response_vinfo_json_obj = json.loads(response_json_obj['vinfo'])
                    ts_url_prefix = response_vinfo_json_obj['vl']['vi'][0]['ui'][-1]['url']
                    ts_url_prefix = ts_url_prefix[:ts_url_prefix.rindex('/')+1]
                    m3u8_str = response_vinfo_json_obj['vl']['vi'][0]['ul']['m3u8']
                    assert '#EXTM3U' in m3u8_str
                    part_urls = []
                    discontinuity = False
                    for m3u8_line in m3u8_str.splitlines():
                        if m3u8_line == '#EXT-X-DISCONTINUITY':
                            discontinuity = not discontinuity
                        else:
                            if not discontinuity and '.ts' in m3u8_line:
                                part_urls.append(ts_url_prefix + m3u8_line)
                    dir_path = str(self.id)
                    task = video_task.VideoTask(dir_path)
                    task.init(str(self.id), 'ts', None, part_urls)
                    task.flush()
                    with open(os.path.join(dir_path, 'info.txt'), 'w', encoding='utf-8') as f:
                        print('url:', file=f)
                        print(request.url, file=f)
                        print('post_data:', file=f)
                        print(post_data_str, file=f)
                        print('response:', file=f)
                        print(response_str, file=f)
                    print('{} vid={}'.format(self.id, vid))
                    self.id += 1

addons = [
    Logger()
]
