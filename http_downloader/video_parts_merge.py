import os
import re
import subprocess

from . import video_task
from . import term_color

def merge_parts(task, ffmpeg_path, clean=False):
    if task.merge_done:
        print(term_color.yellow('video {} parts merge already done'.format(task.dir_path)))
        
        return True
    else:
        print('merge video {} parts'.format(task.dir_path))
        part_ids = []
        for file_name in os.listdir(task.dir_path):
            m = re.match(r'^p(\d+).{}$'.format(task.ext), file_name)
            if m:
                part_id = int(m.group(1))
                part_ids.append(part_id)
        part_ids.sort()
        success = False
        if part_ids == list(range(1, len(task.part_urls)+1)):
            video_parts = [os.path.join(task.dir_path, 'p{}.{}'.format(part_id, task.ext)) for part_id in part_ids]
            video_file_path = '{}.{}'.format(task.dir_path, task.ext)
            if ffmpeg_path:
                list_file = '{}.list'.format(task.dir_path)
                with open(list_file, 'w') as f:
                    f.write('\n'.join(['file {}'.format(e.replace('\\', '/')) for e in video_parts]))
                success = True
                try:
                    subprocess.run(['{}/ffmpeg'.format(ffmpeg_path), '-xerror', '-f', 'concat', '-i', list_file, '-c', 'copy', video_file_path], check=True)
                    os.remove(list_file)
                except Exception as e:
                    print(term_color.red(e))
                    print(term_color.red('fail to merge video, ffmpeg error'))
                    if os.path.isfile(video_file_path):
                        os.remove(video_file_path)
                    success = False
                if success:
                    if task.name is not None:
                        try:
                            os.rename(video_file_path, '{}.{}'.format(task.name, task.ext))
                        except Exception as e:
                            print(term_color.red(e))
                            print(term_color.red('fail to rename video'))
                            success = False
            else:
                with open(video_file_path, 'wb') as dst_f:
                    for video_part in video_parts:
                        with open(video_part, 'rb') as src_f:
                            dst_f.write(src_f.read())
                success = True
            if success:
                task.merge_done = True
                task.flush()
                if clean:
                    for video_part in video_parts:
                        os.remove(video_part)
        else:
            print('fail to merge video, some video parts missing')
            success = False
        return success

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('video_id_range', help='video id range, e.g. 1,2')
    parser.add_argument('--ffmpeg_path', help='ffmpeg path, use ffmpeg concat')
    parser.add_argument('--clean', action='store_true', help='clean up on success')
    args = parser.parse_args()

    start_video_id, end_id = map(int, args.video_id_range.split(','))

    success_video_ids = []
    failed_video_ids = []
    missing_video_ids = []
    for video_id in range(start_video_id, end_id+1):
        if os.path.isdir(str(video_id)):
            task = video_task.VideoTask(str(video_id))
            task.load()
            success = merge_parts(task, args.ffmpeg_path, args.clean)
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
