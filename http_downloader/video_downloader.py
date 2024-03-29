import os

from . import video_task
from . import video_parts_downloader
from . import video_parts_decrypt
from . import video_parts_merge
from . import term_color

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('video_id_range', help='video id range, e.g. 1,2')
    parser.add_argument('--use_wget', action='store_true', help='use wget download')
    parser.add_argument('--mp', type=int, default=0, help='multiprocessing')
    parser.add_argument('--use_ffmpeg', action='store_true', help='use ffmpeg concat')
    parser.add_argument('--clean', action='store_true', help='clean up on success')
    parser.add_argument('--ignore_error', action='store_true', help='ignore_error')
    args = parser.parse_args()

    start_video_id, end_video_id = map(int, args.video_id_range.split(','))

    success_video_ids = []
    failed_video_ids = []
    missing_video_ids = []
    for video_id in range(start_video_id, end_video_id+1):
        if os.path.isdir(str(video_id)):
            task = video_task.VideoTask(str(video_id))
            task.load()
            success = False
            for i in range(5):
                success = video_parts_downloader.download_parts(task, args.use_wget, args.mp)
                if success:
                    break
            if task.key is not None:
                success = success and video_parts_decrypt.decrypt_parts(task, args.mp, args.clean)
            success = success and video_parts_merge.merge_parts(task, args.use_ffmpeg, args.clean, args.ignore_error)
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
