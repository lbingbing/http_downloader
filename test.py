import os
import subprocess

os.chdir('tests')

def run(cmd, timeout=None):
    print(' '.join(cmd))
    res = subprocess.run(cmd, timeout=timeout)
    return res.returncode == 0

def test_test_http_downloader():
    assert run(['python', 'test_http_downloader.py', '80', '1024'])

def test_test_http_downloader_use_wget():
    assert run(['python', 'test_http_downloader.py', '80', '1024', '--use_wget'])
