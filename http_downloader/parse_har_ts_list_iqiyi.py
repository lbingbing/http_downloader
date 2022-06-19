import argparse

import video_parse_iqiyi

parser = argparse.ArgumentParser()
parser.add_argument('har_file', type=argparse.FileType('r', encoding='utf-8'), help='input har file')
parser.add_argument('out_file', type=argparse.FileType('w'), help='output file')
args = parser.parse_args()

lines = [line for line in args.har_file if 'm3u8\\":\\"#EXTM3U' in line]
assert len(lines), 'no match line found'

screen_sizes = []
for line in lines:
    m = re.search(r'scrsz\\":\\"(\d+)x\d+', line)
    screen_sizes.append((line, int(m.group(1))))
screen_sizes.sort(key=lambda e: -e[1])
line = screen_sizes[0][0]

file_urls = video_parse_iqiyi.get_file_urls(line)

args.out_file.write('\n'.join(file_urls))
