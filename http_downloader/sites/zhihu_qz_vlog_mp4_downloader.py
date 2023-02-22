import argparse
from http_downloader import http_downloader

parser = argparse.ArgumentParser()
parser.add_argument('url_file', help='url file')
args = parser.parse_args()

with open(args.url_file, encoding='utf-8') as f:
    urls = [line.strip() for line in f]

for url in urls:
    pos1 = url.index('.mp4?') + 4
    pos0 = url.rindex('/', 0, pos1) + 1
    file_path = url[pos0:pos1]
    print('downloading {} ...'.format(file_path))
    http_downloader.download_url(url, file_path, verbose=True)
