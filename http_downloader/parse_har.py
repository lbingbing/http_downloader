import argparse
import json
import base64
import sys

MIME_TYPES = {
    'video': [
        'video/mp2t',
        ],
    'audio': [
        'audio/mp4',
        'audio/mpeg',
        'application/octet-stream',
        ],
    }

parser = argparse.ArgumentParser()
parser.add_argument('mime_type', choices = MIME_TYPES.keys(), help = 'output file')
parser.add_argument('har_file', type = argparse.FileType('r', encoding = 'utf-8'), help = 'input har file')
parser.add_argument('out_file', type = argparse.FileType('wb'), help = 'output file')
args = parser.parse_args()

mime_types = MIME_TYPES[args.mime_type]
json_obj = json.load(args.har_file)

num = 0
for entry in json_obj['log']['entries']:
    content = entry['response']['content']
    if content['mimeType'] in mime_types:
        b = base64.b64decode(content['text'])
        args.out_file.write(b)
        num += 1
        print('\r{0} {1} found'.format(num, args.mime_type), end = '', file = sys.stderr)

