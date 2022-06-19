import urllib.parse

class Proxy:
    def __init__(self, protocol, ip, port):
        self.protocol = protocol
        self.ip = ip
        self.port = port

    def __eq__(self, other):
        return self.protocol == other.protocol and \
               self.ip == other.ip and \
               self.port == other.port

    def __hash__(self):
        return hash((self.protocol, self.ip, self.port))

    def get_url(self):
        return '{0}://{1}:{2}'.format(self.protocol, self.ip, self.port)

def str_to_proxy(url):
    url_parse = urllib.parse.urlparse(url)
    protocol = url_parse.scheme
    ip = url_parse.hostname
    port = str(url_parse.port)
    return Proxy(protocol, ip, port)

def get_proxies_from_file(proxy_file_name):
    proxies = []
    with open(proxy_file_name) as f:
        for line in f:
            url = line.strip()
            if url:
                proxies.append(str_to_proxy(url))
    return proxies
