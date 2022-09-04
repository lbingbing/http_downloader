import os
import sys
import multiprocessing.pool

from Crypto.Cipher import AES

from . import video_task
from . import term_color

def decrypt_part(args):
    task, part_id = args
    part_path = os.path.join(task.dir_path, task.get_part_file_name(part_id))
    if os.path.isfile(part_path):
        ret = 1
    else:
        with open(os.path.join(task.dir_path, task.get_encrypted_part_file_name(part_id)), 'rb') as f:
            data_enc = f.read()
        iv = b'0000000000000000'
        cipher = AES.new(task.key, AES.MODE_CBC, iv)
        try:
            data = cipher.decrypt(data_enc)
            with open(part_path, 'wb') as f:
                f.write(data)
            ret = 0
        except Exception as e:
            ret = 2
    return ret

def decrypt_parts(task, mp, clean=False):
    if task.decrypt_done:
        print(term_color.yellow('video {} parts decryption already done'.format(task.dir_path)))
        return True
    else:
        print('decrypting video {} parts'.format(task.dir_path))
        part_ids = task.get_part_ids()
        if mp:
            success = True
            with multiprocessing.pool.Pool(mp) as pool:
                arg_list = [(task, part_id) for part_id in part_ids]
                success_num = 0
                fail_num = 0
                total_num = task.get_part_num()
                for ret in pool.imap(decrypt_part, arg_list, chunksize=8):
                    if ret in (0, 1):
                        success_num += 1
                    else:
                        fail_num += 1
                        success = False
                    print('\rdecrypting: {}/{}/{} success/error/total ...'.format(success_num, fail_num, total_num), end='', file=sys.stderr)
                print(file=sys.stderr)
        else:
            success = True
            for part_id in part_ids:
                print('decrypting part {}/{}'.format(part_id, task.get_part_num()))
                ret = decrypt_part((task, part_id))
                if ret == 0:
                    pass
                elif ret == 1:
                    print(term_color.yellow('part {}/{} already decrypted'.format(part_id, task.get_part_num())))
                else:
                    print(term_color.red('fail to decrypt part {}/{}'.format(part_id, task.get_part_num())))
                    success = False
        if success:
            task.decrypt_done = True
            task.flush()
            if clean:
                for part_id in part_ids:
                    os.remove(os.path.join(task.dir_path, task.get_encrypted_part_file_name(part_id)))
        return success

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('video_id_range', help='video id range, e.g. 1,2')
    parser.add_argument('--mp', type=int, default=0, help='multiprocessing')
    parser.add_argument('--clean', action='store_true', help='clean up on success')
    args = parser.parse_args()

    start_video_id, end_video_id = map(int, args.video_id_range.split(','))

    success_video_ids = []
    failed_video_ids = []
    missing_video_ids = []
    for video_id in range(start_video_id, end_video_id+1):
        if os.path.isdir(str(video_id)):
            task = video_task.VideoTask(str(video_id))
            task.load()
            success = decrypt_parts(task, args.mp, args.clean)
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
