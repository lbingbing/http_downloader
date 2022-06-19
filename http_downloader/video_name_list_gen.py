import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('name_list_file', help='name list file')
parser.add_argument('file_num', type=int, help='file num')
args = parser.parse_args()

with open(args.name_list_file, 'w', encoding='utf-8') as f:
    for file_id in range(1, args.file_num + 1):
        print('{}|'.format(file_id), file=f)
