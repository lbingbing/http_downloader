from http_downloader import http_downloader

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='host')
    parser.add_argument('category', choices=['zxsp', 'yzdy', 'zbsp'], help='video category')
    parser.add_argument('page_num', type=int, help='page num')
    args = parser.parse_args()

    if args.category == 'zxsp':
        page_url_fmt = 'https://{}/vod/type/id/3/page/{}.html'
    elif args.category == 'yzdy':
        page_url_fmt = 'https://{}/vod/type/id/13/page/{}.html'
    elif args.category == 'zbsp':
        page_url_fmt = 'https://{}/vod/type/id/5/page/{}.html'

    for page_id in range(1, args.page_num+1):
        print('downloading page {}'.format(page_id))
        page_url = page_url_fmt.format(args.host, page_id)
        http_downloader.download_url(page_url, 'page{}.html'.format(page_id), verbose=True)
