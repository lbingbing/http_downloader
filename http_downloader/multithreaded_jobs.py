import concurrent.futures
import sys
import time

class Job:
    def __init__(self, fn, *args):
        self.fn = fn
        self.args = args

        self.success = None
        self.result = None

    def get_success_msg(self):
        return '{} [done]'.format(self.args)

    def get_failure_msg(self):
        return '{} [Error: {}]'.format(self.args, self.result)

def submit_jobs(jobs, worker_num, is_progress=False, progress_label='progress', is_log=False, log_name='submit_jobs.log'):
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_num) as tpe:
        future_to_job = {tpe.submit(job.fn, *job.args): job for job in jobs}

        success_num, error_num, total = 0, 0, len(jobs)
        if is_progress:
            print_progress = lambda suffix: print('\r{}: {}/{}/{} success/error/total {}'.format(progress_label, success_num, error_num, total, suffix), end='', file=sys.stderr)
            print_progress('...')

        if is_log:
            log_f = open(log_name, 'a', buffering=1)
            print('['+time.ctime()+']', file=log_f)

        for future in concurrent.futures.as_completed(future_to_job):
            job = future_to_job[future]
            try:
                job.result = future.result()
                job.success = True
                success_num += 1
                if is_log:
                    print(job.get_success_msg(), file=log_f)
            except Exception as e:
                job.result = e
                job.success = False
                error_num += 1
                if is_log:
                    print(job.get_failure_msg(), file=log_f)

            if is_progress:
                print_progress('...')

        if is_progress:
            print_progress('done\n')

        if is_log:
            jobs_f = list(filter(lambda job: not job.success, jobs))
            jobs_s = list(filter(lambda job: job.success, jobs))
            if jobs_f:
                print('Failures:', file=log_f)
                for job in jobs_f:
                    print(job.get_failure_msg(), file=log_f)
                print(file=log_f)
            if jobs_s:
                print('Successes:', file=log_f)
                for job in jobs_s:
                    print(job.get_success_msg(), file=log_f)
                print(file=log_f)
            log_f.close()

    return success_num == total
