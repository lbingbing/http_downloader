import argparse
import sys
import http.client

import http_downloader

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('album_url',help='album url')
arg_parser.add_argument('-p','--print',action='store_true',help="just print urls")
arg_parser.add_argument('-s','--subject',help="album subject",metavar='album_subject')
args = arg_parser.parse_args()

#http_downloader.setup_global_proxy('http','124.42.7.103','80')

try:
    page_content = http_downloader.get_remote_data(args.album_url).decode()
except Exception as e:
    print('{0} [Error: {1}]'.format(e.url,e))
    sys.exit(1)

if args.subject==None:
    args.subject = http_downloader.extract(page_content,'<div class="inline">','</div>')[0]
print(args.subject)

page_num = int(http_downloader.extract(page_content,'<span class="count">(',')</span>')[0][1:-1])

page_urls = [args.album_url]
pos = args.album_url.rfind('.html')
for i in range(2,page_num+1):
    page_urls.append(args.album_url[:pos]+'-'+str(i)+args.album_url[pos:])

element_ext = 'jpg'
if args.print:
    http_downloader.print_page_element_urls(page_urls,element_ext)
else:
    http_downloader.download_page_elements(element_ext,args.subject,page_urls)
