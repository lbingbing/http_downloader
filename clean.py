import os
import shutil

def rmtree(dir_path):
    if os.path.isdir(dir_path):
        print('removing', dir_path)
        shutil.rmtree(dir_path)

rmtree('build')
rmtree('dist')
rmtree('http_downloader.egg-info')
