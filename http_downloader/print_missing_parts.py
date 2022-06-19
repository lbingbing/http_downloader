import argparse
import os
import re

parser = argparse.ArgumentParser()
parser.add_argument('video_type', choices=['ts', 'm4s'], help='video type')
parser.add_argument('dest_dir', help='dest dir')
args = parser.parse_args()

with open(os.path.join(args.dest_dir, 'urls.txt'), encoding='utf-8') as f:
    urls = f.read().split('\n')
part_num = len(urls)

done_part_ids = set()
for file_name in os.listdir(args.dest_dir):
    m = re.match(r'^p(\d+).{}$'.format(args.video_type), file_name)
    if m:
        part_id = int(m.group(1))
        done_part_ids.add(part_id)
missing_part_ids = sorted(set(range(part_num)) - done_part_ids)

print('missing part num {}'.format(len(missing_part_ids)))
for part_id in missing_part_ids:
    print(part_id)
