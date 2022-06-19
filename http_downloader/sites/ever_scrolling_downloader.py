import sys
import os
import time
import random

if sys.argv[1]=='1':
    base_url = 'http://www.novostrong.com/great-outdoors'
elif sys.argv[1]=='2':
    base_url = 'https://www.morazzia.com/grace-c'
elif sys.argv[1]=='3':
    base_url = 'https://www.babesandgirls.com/ashley-zeitler'
elif sys.argv[1]=='4':
    base_url = 'http://www.sexykittenporn.com/galleries/megan-rain-enjoys-sex/'
else:
    print('unknown site')
    sys.exit()

i = 1
while i<100:
    print('pass',i)
    urls = []
    for j in range(5):
        urls.append('"'+base_url+'?more=1&from='+str(i*24)+'"')
        i += 1
    urls = ' '.join(urls)
    os.system('python -B http_downloader.py pg -d images .jpg '+urls)
    time.sleep(random.randint(1,6))
