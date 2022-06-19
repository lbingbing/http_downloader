import argparse
import os

from . import video_task

parser = argparse.ArgumentParser()
parser.add_argument('name_list_file', help='name list file')
args = parser.parse_args()

task_ids = set()
new_names = set()
mapping = []
with open(args.name_list_file, encoding='utf-8') as f:
    for line in f:
        task_id, name = line.strip().split('|')
        assert task_id not in task_ids, "duplicated task id '{}'".format(task_id)
        assert name not in names, "duplicated name '{}'".format(name)
        task_ids.add(task_id)
        names.add(name)
        mapping.append((task_id, name))

for task_id, name in mapping:
    task = video_task.VideoTask(task_id)
    task.name = name
    task.flush()
