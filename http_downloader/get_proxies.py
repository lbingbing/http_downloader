import argparse
import time
import random
import urllib.request
import gzip
import html.parser

import proxy
import http_downloader
import multithreaded_jobs

class HTMLNode:
    def __init__(self, tag=None, attrs=[]):
        self.tag = tag
        self.attrs = attrs
        self.data = None
        self.children = []

    def print(self):
        self.print_helper(self,0)

    def print_helper(self, node, depth):
        print('{0}{1} '.format(' '*depth*2,node.tag),end='')
        for attr in node.attrs:
            print('{0}="{1}" '.format(attr[0],attr[1]),end='')
        print('data={0}'.format(node.data))
        print()
        for child in node.children:
            self.print_helper(child,depth+1)

class HTMLParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()

        self.stack = []
        self.start = False
        self.stop = False
        self.start_level = None
        self.result = HTMLNode()
        self.result_stack = [self.result]

    def is_node_match(self, node_t, node_p):
        self.stack[-1]==('div',[('class','wlist')])
        if node_t[0]!=node_p[0]:
            return False
        if node_p[1]!=None:
            if len(node_t[1])!=len(node_p[1]):
                return False
            for attr_t,attr_p in zip(node_t[1],node_p[1]):
                if attr_t[0]!=attr_p[0]:
                    return False
                if attr_p[1]!=None and attr_t[1]!=attr_p[1]:
                    return False
        return True

    def is_nodes_match(self, nodes_t, nodes_p):
        for node_t,node_p in zip(nodes_t,nodes_p):
            if not self.is_node_match(node_t,node_p):
                return False
        return True

    def handle_starttag(self, tag, attrs):
        if self.stop:
            return

        self.stack.append((tag,attrs))

        if not self.start and \
           len(self.stack)>=len(self.start_pattern) and \
           self.is_nodes_match(self.stack[-len(self.start_pattern):],self.start_pattern):
            self.start = True
            self.start_level = len(self.stack)

        if self.start:
            node = HTMLNode(tag,attrs)
            self.result_stack[-1].children.append(node)
            self.result_stack.append(node)

    def handle_data(self, data):
        if self.stop:
            return

        if self.start and data:
            self.result_stack[-1].data = data.strip()

    def handle_endtag(self, tag):
        if self.stop:
            return

        if not self.stack:
            raise Exception
        #if self.stack[-1][0]!=tag:
        #    print(self.getpos())
        #    raise Exception

        if self.start and len(self.stack)==self.start_level:
            self.stop = True

        if self.stack:
            self.stack.pop()
        if self.start:
            self.result_stack.pop()

    def get_result(self):
        return self.result

class Data5UHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()

        self.start_pattern = [
            ('div',[('class','wlist')]),
            ]

    def parse_root(self, root):
        proxies = []
        for node in root.children[0].children[1].children[1:]:
            protocol = 'https' if 'https' in node.children[3].children[0].children[0].data.lower() else 'http'
            ip = node.children[0].children[0].data
            port = node.children[1].children[0].data
            proxies.append(proxy.Proxy(protocol,ip,port))

        return proxies

class Proxy360HTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()

        self.start_pattern = [
            ('table',None),
            ('tr',None),
            ('td',None),
            ('div',None),
            ]

    def parse_root(self, root):
        proxies = []
        for node in root.children[0].children:
            if node.attrs==[('class','proxylistitem'),('name','list_proxy_ip')]:
                protocol = 'http'
                ip = node.children[0].children[0].data
                port = node.children[0].children[1].data
                proxies.append(proxy.Proxy(protocol,ip,port))

        return proxies

class KuaiDaiLiHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()

        self.start_pattern = [
            ('table',None),
            ('tbody',None),
            ]

    def parse_root(self, root):
        proxies = []
        for node in root.children[0].children:
            protocol = 'https' if 'https' in node.children[3].data.lower() else 'http'
            ip = node.children[0].data
            port = node.children[1].data
            proxies.append(proxy.Proxy(protocol,ip,port))

        return proxies

is_get_proxies_logging = True

def get_proxies(page_urls, headers, htmlparsertype):
    def worker(page_url):
        page_content = http_downloader.get_remote_data(page_url,headers=headers).decode()

        htmlparser = htmlparsertype()
        htmlparser.feed(page_content)
        htmlparser.close()
        root = htmlparser.get_result()
        #root.print()
        proxies = htmlparser.parse_root(root)

        http_downloader.delay()

        return proxies

    jobs = [multithreaded_jobs.Job(worker,page_url) for page_url in page_urls]
    for job,page_url in zip(jobs,page_urls):
        job.page_url = page_url

    success_msg = lambda job: '{0} [done]'.format(job.page_url)
    failure_msg = lambda job: '{0} [Error: {1}]'.format(job.page_url,job.result)
    multithreaded_jobs.submit_jobs(jobs,worker_num=5,is_echo=True,label='analyzing page',is_log=is_get_proxies_logging,log_name='get_proxies.log',success_msg=success_msg,failure_msg=failure_msg)

    proxies = [p for job in jobs if job.success for p in job.result]
    return proxies

def get_proxies_Data5U():
    page_urls = [
        'http://www.data5u.com/',
        'http://www.data5u.com/free/',
        'http://www.data5u.com/free/gngn/',
        'http://www.data5u.com/free/gnpt/',
        'http://www.data5u.com/free/gwgn/',
        'http://www.data5u.com/free/gwpt/',
        ]

    headers = http_downloader.get_random_headers()
    headers['Host'] = 'www.data5u.com'
    headers['Referer'] = 'http://www.data5u.com/'

    try:
        http_downloader.get_remote_data(page_urls[0],headers=headers)
    except Exception as e:
        #print(e)
        #print(e.headers.items())
        cookie = e.headers.get('Set-Cookie')
        headers['Cookie'] = cookie

    return get_proxies(page_urls,headers,Data5UHTMLParser)

def get_proxies_proxy360():
    page_urls = [
        'http://www.proxy360.cn',
        'http://www.proxy360.cn/Region/Brazil',
        'http://www.proxy360.cn/Region/America',
        'http://www.proxy360.cn/Region/Taiwan',
        'http://www.proxy360.cn/Region/Japan',
        'http://www.proxy360.cn/Region/Thailand',
        'http://www.proxy360.cn/Region/Vietnam',
        'http://www.proxy360.cn/Region/bahrein',
        ]

    headers = http_downloader.get_random_headers()
    headers['Host'] = 'www.proxy360.cn'
    headers['Referer'] = 'http://www.proxy360.cn'

    return get_proxies(page_urls,headers,Proxy360HTMLParser)

def get_proxies_kuaidaili():
    page_urls = []
    page_urls += [
        'http://www.kuaidaili.com/proxylist/'+str(i) for i in range(1,11)
        ]
    page_urls += [
        'http://www.kuaidaili.com/free/inha/'+str(i) for i in range(1,11)
        ]
    page_urls += [
        'http://www.kuaidaili.com/free/intr/'+str(i) for i in range(1,11)
        ]
    page_urls += [
        'http://www.kuaidaili.com/free/outha/'+str(i) for i in range(1,11)
        ]
    page_urls += [
        'http://www.kuaidaili.com/free/outtr/'+str(i) for i in range(1,11)
        ]

    headers = http_downloader.get_random_headers()
    headers['Host'] = 'www.kuaidaili.com'
    headers['Referer'] = 'http://www.kuaidaili.com'
    headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393'

    return get_proxies(page_urls,headers,KuaiDaiLiHTMLParser)

def unique(l):
    unique_l = []
    seen = set()
    for e in l:
        if e not in seen:
            seen.add(e)
            unique_l.append(e)
    return unique_l

is_verify_proxies_logging = True

def verify_proxies(proxies, url):
    def worker(p):
        try_num = 3
        while True:
            headers = http_downloader.get_random_headers()
            req = urllib.request.Request(url,None,headers)
            req.set_proxy(p.ip+':'+p.port,p.protocol)
            try:
                with urllib.request.urlopen(req,timeout=5) as resp:
                    return p
            except Exception as e:
                try_num -= 1
                if try_num==0:
                    raise e
                http_downloader.delay()

    jobs = [multithreaded_jobs.Job(worker,p) for p in proxies]
    for job,p in zip(jobs,proxies):
        job.proxy_url = p.get_url()

    success_msg = lambda job: '{0} [done]'.format(job.proxy_url)
    failure_msg = lambda job: '{0} [Error: {1}]'.format(job.proxy_url,job.result)
    multithreaded_jobs.submit_jobs(jobs,worker_num=20,is_echo=True,label='verifying proxies',is_log=is_verify_proxies_logging,log_name='verify_proxies.log',success_msg=success_msg,failure_msg=failure_msg)

    available_proxies = [job.result for job in jobs if job.success]
    return available_proxies

#proxies = get_proxies_Data5U()
#proxies = get_proxies_proxy360()
proxies = get_proxies_kuaidaili()
#proxies = proxy.get_proxies_from_file('all_history_available_proxies.txt')

proxies = unique(proxies)
print(len(proxies),'proxies detected')

target_urls = [
        #('http://www.data5u.com','data5u'),
        #('http://www.proxy360.cn','proxy360'),
        ('http://www.kuaidaili.com','kuaidaili'),
        ('http://www.baidu.com','baidu'),
        ('http://www.xiumm.org','xiumm'),
        ('https://babesrater.com','babesrater'),
    ]

all_available_proxies = []

for target_url,name in target_urls:
    print('verifying proxies connection to',target_url)
    available_proxies = verify_proxies(proxies,target_url)
    all_available_proxies += available_proxies

    file_name = 'available_proxies('+name+').txt'
    with open(file_name,'w') as f:
        for p in available_proxies:
            print(p.get_url(),file=f)

with open('all_available(all).txt','w') as f:
    for p in all_available_proxies:
        print(p.get_url(),file=f)
