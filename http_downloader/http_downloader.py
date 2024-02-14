import configparser
import sys
import os
import time
import random
import urllib.request
import urllib.parse
import gzip
import subprocess

from . import proxy
from . import http_connection_pool
from . import multithreaded_jobs

def init():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), 'http_downloader.ini')))
    is_global_proxy_on = config['DEFAULT']['is_global_proxy_on'] == '1'
    global_proxy = config['DEFAULT']['global_proxy']
    is_proxy_pool_on = config['DEFAULT']['is_proxy_pool_on'] == '1'
    proxy_pool_file = config['DEFAULT']['proxy_pool_file']

    proxy_pool = None
    if is_global_proxy_on and is_proxy_pool_on:
        print("can't set both global proxy and proxy pool on", file=sys.stderr)
        sys.exit(1)
    elif is_global_proxy_on:
        p = proxy.str_to_proxy(global_proxy)
        proxy_handler = urllib.request.ProxyHandler({p.protocol: p.ip+':'+p.port})
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
        print('setup global proxy:', p.get_url())
    elif is_proxy_pool_on:
        proxy_pool = proxy.get_proxies_from_file(os.path.join(os.path.dirname(__file__), proxy_pool_file))
        if not proxy_pool:
            print("can't find legal proxy in file", proxy_pool_file, file=sys.stderr)
            sys.exit(1)
        print('setup proxy pool of size {} from {}'.format(len(proxy_pool), proxy_pool_file))

    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())

    return opener, is_global_proxy_on, is_proxy_pool_on, proxy_pool

opener, is_global_proxy_on, is_proxy_pool_on, proxy_pool = init()

def get_fake_headers():
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8;en-US,en;q=0.8,zh-Hans-CN;q=0.5,zh-Hans;q=0.3',
        'Connection': 'Keep-Alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': random.choice((
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
            )),
        }
    return headers

def delay():
    time.sleep(random.uniform(1, 3))

def get_remote_data_progress(done, total, progressing):
    if total is None:
        suffix = '{} bytes'.format(done)
    else:
        suffix = 'total {} bytes, {:.0f}% done'.format(total, done/total*100)
    print('\rdownloading, {}'.format(suffix), end='' if progressing else '\n', file=sys.stderr, flush=True)

def get_remote_data(url, data=None, headers=None, try_num=60, use_wget=False, verbose=False):
    #urlparse = urllib.parse.urlparse(url)
    #urlparse_l = list(urlparse)
    #urlparse_l[2] = urllib.parse.quote(urllib.parse.unquote(urlparse_l[2]))
    #url = urllib.parse.urlunparse(urlparse_l)

    all_headers = get_fake_headers()
    #all_headers['Host'] = urlparse.netloc
    if headers is not None:
        all_headers.update(headers)
    if is_proxy_pool_on:
        try_num *= 2

    if use_wget:
        cmd = ['wget', '-q', '-O-', '--compression=auto', '--tries='+str(try_num), '"' + url + '"']
        if verbose:
            cmd.append('--show-progress')
        for header_name, header_value in all_headers.items():
            cmd.append('--header="{}: {}"'.format(header_name, header_value.replace('"', '\\"')))
        if data is not None:
            cmd.append('--post-data='+data.decode())
        res = subprocess.run(' '.join(cmd), stdout=subprocess.PIPE, shell=True, check=True)
        return res.stdout
    else:
        req = urllib.request.Request(url, data, all_headers)
        while True:
            if is_proxy_pool_on:
                p = random.choice(proxy_pool)
                req.set_proxy(p.ip+':'+p.port, p.protocol)
            try:
                with opener.open(req, timeout=5) as resp:
                    data_len_str = resp.getheader('Content-Length')
                    if data_len_str is None:
                        data_len = None
                    else:
                        data_len = int(data_len_str)
                    blocks = []
                    done = 0
                    if verbose:
                        get_remote_data_progress(done, data_len, True)
                    for b in iter(lambda: resp.read(1048576), b''):
                        blocks.append(b)
                        done += len(b)
                        if verbose:
                            get_remote_data_progress(done, data_len, True)
                    if verbose:
                        get_remote_data_progress(done, data_len, False)
                    data = b''.join(blocks)
                    if resp.getheader('Content-Encoding') == 'gzip':
                        data = gzip.decompress(data)
                    return data
            except Exception as e:
                try_num -= 1
                if try_num == 0:
                    e.url = url
                    raise e
                delay()

def get_remote_data_http_conn(conn, url, method='GET', body=None, headers=None, try_num=60):
    while True:
        try:
            all_headers = get_fake_headers()
            #all_headers['Host'] = conn.host
            if headers is not None:
                all_headers.update(headers)
            conn.request(method, url, body, all_headers)
            with conn.getresponse() as resp:
                b = resp.read()
                if resp.getheader('Content-Encoding') == 'gzip':
                    b = gzip.decompress(b)
                return b
        except Exception as e:
            conn.close()
            try_num -= 1
            if try_num == 0:
                e.url = conn.host + url
                raise e
            delay()

def write_file(file_path, data):
    with open(file_path, 'wb') as f:
        bytes_num = f.write(data)
        return bytes_num

def download_url(url, file_path, use_wget=False, overwrite=False, verbose=False):
    if not overwrite and os.path.isfile(file_path):
        raise Exception("file '{}' already exists".format(file_path))
    else:
        return write_file(file_path, get_remote_data(url, use_wget=use_wget, verbose=verbose))

def download_url_conn(conn, url, file_path):
    if os.path.isfile(file_path):
        raise Exception("file '{}' already exists".format(file_path))
    return write_file(file_path, get_remote_data_http_conn(conn, url))

def download_urls(urls, dest_dir, file_names=None, file_name_pattern=None, use_wget=False, overwrite=False, worker_num=4, is_log=False):
    assert file_names is None or file_name_pattern is None

    def worker(url, file_path):
        if os.path.isfile(file_path):
            bytes_num = os.stat(file_path).st_size
        else:
            bytes_num = download_url(url, file_path, use_wget=use_wget, overwrite=overwrite)
            delay()
        return bytes_num

    if not os.path.isdir(dest_dir):
        os.mkdir(dest_dir)

    if file_names:
        file_paths = [os.path.join(dest_dir, e) for e in file_names]
    elif file_name_pattern:
        prefix, suffix, start_id = file_name_pattern
        file_paths = [os.path.join(dest_dir, '{}{}{}'.format(prefix, i, suffix)) for i in range(start_id, start_id+len(urls))]
    else:
        file_paths = [os.path.join(dest_dir, gen_file_name_from_url(url)) for url in urls]
    jobs = [multithreaded_jobs.Job(worker, url, file_path) for url, file_path in zip(urls, file_paths)]
    return multithreaded_jobs.submit_jobs(jobs, worker_num=worker_num, is_progress=True, progress_label='downloading', is_log=is_log, log_name='download_urls.log')

def download_urls_http_conn(urls, dest_dir, is_log=False):
    def worker(conn_pool, url):
        url_path = get_url_path(url)
        file_path = os.path.join(dest_dir, gen_file_name_from_url(url))
        conn = conn_pool.getconn()
        try:
            bytes_num = download_url_conn(conn, url_path, file_path)
        finally:
            conn_pool.returnconn(conn)
            delay()
        return bytes_num

    if not os.path.isdir(dest_dir):
        os.mkdir(dest_dir)

    host = get_url_host(urls[0])
    with http_connection_pool.HTTPConnectionPool(host, worker_num) as conn_pool:
        jobs = [multithreaded_jobs.Job(worker, conn_pool, url) for url in urls]
        return multithreaded_jobs.submit_jobs(jobs, worker_num=4, is_progress=True, progress_label='downloading', is_log=is_log, log_name='download_urls.log')

def get_url_host(url):
    return urllib.parse.urlparse(url).hostname

def get_url_path(url):
    return urllib.parse.urlparse(url).path

def gen_file_name_from_url(url):
    url_parse = urllib.parse.urlparse(url)
    file_name = url_parse.path.replace('/','-').strip('-')
    return file_name

if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser()
    arg_subparsers = arg_parser.add_subparsers(title='modes', dest='mode')

    arg_parser1 = arg_subparsers.add_parser('su', help='single url')
    arg_parser1.add_argument('dest_file_path', help='dest file path')
    arg_parser1.add_argument('target_url', help='target url')
    arg_parser1.add_argument('--use_wget', action='store_true', help='use wget download')
    arg_parser1.add_argument('--overwrite', action='store_true', help='overwrite existing file')
    arg_parser1.add_argument('--verbose', action='store_true', help='verbose')

    arg_parser2 = arg_subparsers.add_parser('fu', help='urls from file')
    arg_parser2.add_argument('dest_dir_path', help='dest dir path')
    arg_parser2.add_argument('urls_file_path', help='urls file path')
    arg_parser2.add_argument('--use_wget', action='store_true', help='use wget download')
    arg_parser2.add_argument('--overwrite', action='store_true', help='overwrite existing file')
    arg_parser2.add_argument('--mp', type=int, default=1, help='multiprocessing')

    args = arg_parser.parse_args()

    if args.mode == 'su':
        try:
            download_url(args.target_url, args.dest_file_path, use_wget=args.use_wget, overwrite=args.overwrite, verbose=args.verbose)
        except Exception as e:
            print('{0} [Error: {1}]'.format(args.target_url, e), file=sys.stderr)
    elif args.mode == 'fu':
        try:
            with open(args.urls_file_path) as f:
                urls = f.read().split()
            download_urls(urls, args.dest_dir_path, use_wget=args.use_wget, overwrite=args.overwrite, worker_num=args.mp)
        except Exception as e:
            print(e, file=sys.stderr)
