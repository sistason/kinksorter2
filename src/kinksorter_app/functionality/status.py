from django_q.monitor import Stat
from django.db.models import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned

import datetime
import time
from kinksorter_app.models import CurrentTask


def get_current_task():
    clusters = Stat.get_all()
    current_tasks = CurrentTask.objects.all()

    if not clusters or clusters[0].status == 'Stopped':
        [current_task.delete() for current_task in current_tasks]
        current_tasks = []

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    tasks = []
    for task in current_tasks:
        if task.ended:
            task.delete()
        else:
            running_for = (now - task.started).seconds
            progress = '{}/{}'.format(task.progress_current, task.progress_max)
            tasks.append({'action': task.name, 'running_for': running_for, 'progress': progress})
            if task.progress_current == task.progress_max:
                task.ended = True
                task.save()

    return tasks


def hook_set_task_ended(task, name=''):
    try:
        current_task = CurrentTask.objects.get(name=name)
        current_task.progress_current += 1
        current_task.save()
    except ObjectDoesNotExist:
        time.sleep(1)
        # Race Condition, if cluster finishes task before CurrentTask is saved into the database
        if CurrentTask.objects.filter(name=name).exists():
            hook_set_task_ended(task, name)
