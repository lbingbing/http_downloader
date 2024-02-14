import os

def run(cmd):
    if isinstance(cmd, str):
        print(cmd)
        os.system(cmd)
    elif isinstance(cmd, list):
        for c in cmd:
            print(c)
            ret = os.system(c)
            if ret:
                break
    else:
        assert 0

run('python setup.py bdist_wheel')
run('pip install --force-reinstall dist/'+next(e for e in os.listdir('dist') if e.startswith('http_downloader') and e.endswith('.whl')))
