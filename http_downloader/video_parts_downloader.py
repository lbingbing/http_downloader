import os

from . import http_downloader
from . import video_task
from . import term_color

def download_parts(task, use_wget, mp):
    if task.download_done:
        print(term_color.yellow('video {} parts download already done'.format(task.dir_path)))
        return True
    else:
        print('downloading video {} parts'.format(task.dir_path))
        if mp:
            enc_suffix = '' if task.key is None else '_enc'
            success = http_downloader.download_urls(task.part_urls, task.dir_path, file_name_pattern=('p', enc_suffix + '.' + task.ext, 1), use_wget=use_wget, worker_num=mp)
        else:
            success = True
            for part_id, url in enumerate(task.part_urls, 1):
                part_path = os.path.join(task.dir_path, 'p{}.{}'.format(part_id, task.ext))
                print('downloading part {}/{}'.format(part_id, task.get_part_num()))
                if os.path.isfile(part_path):
                    print(term_color.yellow('part {}/{} already exists'.format(part_id, task.get_part_num())))
                else:
                    try:
                        http_downloader.download_url(url, part_path, use_wget=use_wget, verbose=True)
                    except Exception as e:
                        print(term_color.red(e))
                        print(term_color.red('fail to download part {}/{}'.format(part_id, task.get_part_num())))
                        success = False
        if success:
            task.download_done = True
            task.flush()
        return success

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('video_id_range', help='video id range, e.g. 1,2')
    parser.add_argument('--use_wget', action='store_true', help='use wget download')
    parser.add_argument('--mp', type=int, default=0, help='multiprocessing')
    args = parser.parse_args()

    start_video_id, end_video_id = map(int, args.video_id_range.split(','))

    success_video_ids = []
    failed_video_ids = []
    missing_video_ids = []
    for video_id in range(start_video_id, end_video_id+1):
        if os.path.isdir(str(video_id)):
            task = video_task.VideoTask(str(video_id))
            task.load()
            success = download_parts(task, args.use_wget, args.mp)
            if success:
                print(term_color.green('video {} success'.format(video_id)))
                success_video_ids.append(video_id)
            else:
                print(term_color.red('video {} fail'.format(video_id)))
                failed_video_ids.append(video_id)
        else:
            print(term_color.yellow('video {} missing'.format(video_id)))
            missing_video_ids.append(video_id)

    print('summary:')
    for video_id in success_video_ids:
        print(term_color.green('video {} success'.format(video_id)))
    for video_id in failed_video_ids:
        print(term_color.red('video {} fail'.format(video_id)))
    for video_id in missing_video_ids:
        print(term_color.yellow('video {} missing'.format(video_id)))
