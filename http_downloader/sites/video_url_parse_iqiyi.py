import re
import collections

def get_part_urls(line, merge_part_urls=True):
    line = line.replace('\\\\/', '/').replace('\\/', '/')
    s = line.index('#EXTM3U')
    e = line.index('"', s)
    urls = line[s:e].split('\\n')
    urls = list(filter(lambda e: e.startswith('http://'), urls))

    if merge_part_urls:
        files = collections.OrderedDict()
        for url in urls:
            m = re.match(r'http:.*/(\w+)\.ts\?start=\d+&end=(\d+)&', url)
            assert m
            name = m.group(1)
            end = m.group(2)
            if name not in files:
                files[name] = {}
                files[name]['url'] = url
            files[name]['end'] = end
        urls = []
        for file_info in files.values():
            urls.append(re.sub(r'end=\d+', 'end={}'.format(file_info['end']), file_info['url']))

    return urls
