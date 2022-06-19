import configparser
import urllib.parse

import http_downloader
import http_connection_pool
import multithreaded_jobs

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'page_element_downloader.ini'))
is_log = config['DEFAULT']['is_log'] == '1'

def download_page_elements(element_ext, dest_dir, page_urls):
    element_urls = get_page_element_urls(page_urls, element_ext)
    http_downloader.download_urls(element_urls, dest_dir)

def get_page_element_urls(page_urls, element_ext):
    def worker(page_url):
        nonlocal element_ext

        page_str = http_downloader.get_remote_data(page_url).decode()
        delay()
        return extract_urls(page_str, page_url, element_ext)

    jobs = [multithreaded_jobs.Job(worker, page_url) for page_url in page_urls]
    multithreaded_jobs.submit_jobs(jobs, worker_num=4, is_progress=True, progress_label='analyzing page', is_log=is_log, log_name='page_url_analysis.log')

    element_urls = [url for job in jobs if job.success for url in job.result]
    return element_urls

def get_page_element_urls_http_conn(page_urls, element_ext):
    def worker(page_url):
        nonlocal element_ext
        nonlocal conn_pool

        page_url_path = http_downloader.get_url_path(page_url)
        conn = conn_pool.getconn()
        page_str = http_downloader.get_remote_data_http_conn(conn, page_url_path).decode()
        conn_pool.returnconn(conn)
        delay()
        return extract_urls(page_str, page_url, element_ext)

    host = http_downloader.get_url_host(page_urls[0])
    conn_pool = http_connection_pool.HTTPConnectionPool(host, worker_num)
    jobs = [multithreaded_jobs.Job(worker, page_url) for page_url in page_urls]
    multithreaded_jobs.submit_jobs(jobs, worker_num=4, is_progress=True, progress_label='analyzing page', is_log=is_log, log_name='page_url_analysis.log')
    conn_pool.close()

    element_urls = [url for job in jobs if job.success for url in job.result]
    return element_urls

def print_page_element_urls(page_urls, element_ext):
    element_urls = get_page_element_urls(page_urls, element_ext)
    print('detected elements:')
    for element_url in element_urls:
        print(element_url)
    print('====')
    print('{0} element(s) detected'.format(len(element_urls)))

preffix_and_suffix_s = (
    ('src="', '"'),
    ("src='", "'"),
    ('SRC="', '"'),
    ("SRC='", "'"),
    ('href="', '"'),
    ("href='", "'"),
    ('HREF="', '"'),
    ("HREF='", "'"),
    )

def extract_urls(s, base_url, url_ext):
    urls = []
    for preffix, suffix in preffix_and_suffix_s:
        temp_urls = extract_str(s, preffix, suffix)
        temp_urls = list(filter(lambda x:x.endswith(url_ext), temp_urls))
        temp_urls = list(map(lambda x: urllib.parse.urljoin(base_url, x), temp_urls))
        urls += temp_urls
    return urls

def extract_str(s, preffix, suffix):
    res = []
    start = 0
    while True:
        start = s.find(preffix, start)
        if start == -1:
            break
        start += len(preffix)
        end = s.find(suffix, start)
        if end == -1:
            break
        res.append(s[start:end].strip())
        start = end+len(suffix)
    return res

if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('element_ext', help='ext of elements to extract')
    arg_parser.add_argument('page_urls', nargs='+', help='page urls', metavar='page_url')
    arg_group = arg_parser.add_mutually_exclusive_group(required=True)
    arg_group.add_argument('-p','--print', action='store_true', help="just print element urls")
    arg_group.add_argument('-d','--dest_dir_path', help="dest dir path", metavar='dest_dir_path')
    args = arg_parser.parse_args()

    if args.print:
        print_page_element_urls(args.page_urls, args.element_ext)
    else:
        download_page_elements(args.element_ext, args.dest_dir_path, args.page_urls)
