import argparse
import sys
import configparser
import html.parser
import http.client
import urllib.parse

import http_downloader

class UGirlsHTMLParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()

        self.pattern = [
            ('div',[('class','gallary_item_album album')]),
            ('div',[('class','item')]),
            ('div',[('class','pic_box')]),
            ('table',[]),
            ('tr',[]),
            ('td',[]),
            ]
        self.stack = []
        self.result = []

    def handle_starttag(self, tag, attrs):
        self.stack.append((tag,attrs))
        if len(self.stack)>=8 and self.stack[-8:-2]==self.pattern:
            if self.stack[-2][1][0][0]!='href' or \
               self.stack[-1][1][0][0]!='alt':
                raise Exception('unexpected pattern')
            url_path = self.stack[-2][1][0][1]
            title = self.stack[-1][1][0][1]
            self.result.append((url_path,title))

    def handle_endtag(self, tag):
        #if not self.stack:
        #    raise Exception
        #if self.stack[-1][0]!=tag:
        #    print(self.getpos())
        #    raise Exception
        if self.stack:
            self.stack.pop()

    def get_result(self):
        return self.result

arg_parser = argparse.ArgumentParser()
arg_group = arg_parser.add_mutually_exclusive_group(required=True)
arg_group.add_argument('-p','--print',action='store_true',help="just print album urls")
arg_group.add_argument('-b','--batch',action='store_true',help="generate download batch file")
args = arg_parser.parse_args()

config = configparser.ConfigParser()
config.read('ugirls_parser.ini')
last_url_path = config['DEFAULT']['last_url_path']

host = 'www.xiumm.org'

albums = []
page_index = 0
msg = lambda: '\r{0} album(s), {1} page(s)'.format(len(albums),page_index)
print(msg(),'...',end='',file=sys.stderr,flush=True)
page_index += 1
conn = http.client.HTTPConnection(host,timeout=6)
while True:
    if page_index==1:
        page_url_path = '/'
    else:
        page_url_path = '/albums/page-'+str(page_index)+'.html'
    try:
        page_content = http_downloader.get_remote_data(conn,page_url_path).decode()
        http_downloader.delay()
    except Exception as e:
        print('{0} [Error: {1}]'.format(e.url,e))
        sys.exit(1)

    htmlparser = UGirlsHTMLParser()
    htmlparser.feed(page_content)
    done = False
    for album_url_path,album_name in htmlparser.get_result():
        if album_url_path==last_url_path:
            done = True
            break
        albums.append((album_url_path,album_name))
        print(msg(),'...',end='',file=sys.stderr,flush=True)
    htmlparser.close()
    if done:
        break

    if page_index==1:
        page_num = int(http_downloader.extract(page_content,'<span class="count">(',')</span>')[0][1:-1])
    page_index += 1
    if page_index>page_num:
        page_index -= 1
        break
conn.close()
print(msg(),'[done]',file=sys.stderr)

if albums:
    last_url_path = albums[0][0]

    albums = [(urllib.parse.urljoin('http://'+host,album_url_path),album_name) for album_url_path,album_name in albums]

    if args.print:
        print()
        for album_url,album_name in albums:
            print(album_url)
            #print(album_name)
            #print()
    elif args.batch:
        with open('ugirls_download_batch.bat','w') as bat_f:
            for album_url,album_name in albums:
                print('python -B ugirls_downloader.py '+album_url,file=bat_f)
            print('pause',file=bat_f)

        config['DEFAULT']['last_url_path'] = last_url_path
        with open('ugirls_parser.ini','w') as f_cfg:
            config.write(f_cfg)
