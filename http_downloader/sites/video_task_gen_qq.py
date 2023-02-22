import argparse
import os
import json

from http_downloader import video_task

parser = argparse.ArgumentParser()
parser.add_argument('dir_path', help='dir path')
args = parser.parse_args()

with open(os.path.join(args.dir_path, 'resp.txt'), encoding='utf-8') as f:
    response_json_obj = json.load(f)
response_vinfo_json_obj = json.loads(response_json_obj['vinfo'])
ts_url_prefix = response_vinfo_json_obj['vl']['vi'][0]['ul']['ui'][-1]['url']
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
task = video_task.VideoTask(args.dir_path)
task.init(args.dir_path, 'ts', None, part_urls)
task.flush()
