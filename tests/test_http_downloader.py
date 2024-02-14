import multiprocessing
import subprocess
import os
import sys

import http_file_server

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, help='http file server port')
    parser.add_argument('file_size', type=int, help='file size')
    parser.add_argument('--use_wget', action='store_true', help='use wget download')
    args = parser.parse_args()

    test_file_name = 'test_file'

    server_p = multiprocessing.Process(target=http_file_server.start_file_server, args=(args.port, args.file_size))
    server_p.start()
    download_cmd = ['python', '-m', 'http_downloader.http_downloader', 'su', test_file_name, 'http://127.0.0.1:{}'.format(args.port), '--overwrite', '--verbose']
    if args.use_wget:
        download_cmd.append('--use_wget')
    subprocess.run(download_cmd, check=True)
    server_p.join()

    with open(test_file_name, 'rb') as f:
        file_content = f.read()
    os.remove(test_file_name)
    sys.exit(0 if http_file_server.get_file_bytes(args.file_size) == file_content else 1)
