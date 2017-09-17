from django_q.monitor import Stat
from django.db.models import ObjectDoesNotExist

import datetime
import time
from kinksorter_app.models import CurrentTask


def get_current_task():
    clusters = Stat.get_all()
    current_tasks = CurrentTask.objects.filter(subtasks=0)
    parent_task = CurrentTask.objects.get(subtasks__gt=0)

    if clusters and clusters[0].status != 'Stopped':
        cluster = clusters[0]
    else:
        cluster = None
        [c.delete() for c in current_tasks]
        parent_task.delete()

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    tasks = []
    for task in current_tasks:
        running_for = (now - task.started).seconds
        if not task.ended:
            tasks.append({'action': task.name, 'running_for': running_for})

    if not tasks or not cluster:
        return {'queue': '0/0', 'tasks': [{'action': 'Idle', 'status': '-'}]}

    done = current_tasks.filter(ended=True).count()
    queue = '{}/{}'.format(done, parent_task.subtasks)

    if done == parent_task.subtasks:
        [c.delete() for c in current_tasks]
        parent_task.delete()

    return {'queue': queue, 'tasks': tasks}


def hook_set_task_ended(task):
    try:
        current_task = CurrentTask.objects.get(task_id=task.id)
        current_task.ended = True
        current_task.save()
    except ObjectDoesNotExist:
        time.sleep(1)
        # Race Condition, if cluster finishes task before CurrentTask is saved into the database
        if CurrentTask.objects.filter(task_id=task.id).exists():
            hook_set_task_ended(task)
