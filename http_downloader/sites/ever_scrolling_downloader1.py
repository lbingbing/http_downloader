import os
import time
import random

urls = [] + \
       ['"http://blowjobhdpics.com/?force_template=page&page=' + str(i) + '"' for i in range(14, 21)]

for url in urls:
    os.system('python -B http_downloader.py pg -d images2 .jpg '+url)
    time.sleep(random.randint(1,6))
