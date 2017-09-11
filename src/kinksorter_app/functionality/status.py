from django.dispatch import receiver
from django_q.signals import pre_execute
from django_q.models import Task
from django_q.monitor import Stat
from django.db.models import ObjectDoesNotExist


import datetime
from kinksorter_app.models import CurrentTask


def get_current_task():
    clusters = Stat.get_all()
    current_tasks = CurrentTask.objects.all()

    if clusters and clusters[0].status != 'Stopped':
        cluster = clusters[0]
    else:
        cluster = None
        [c.delete() for c in current_tasks]

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    tasks = []
    for task in current_tasks:
        running_for = (now - task.started).seconds
        print(task.func, ':', running_for, 'seconds')
        if task.ended or running_for > 300:    #TODO
            task.delete()
        else:
            tasks.append({'action': task.func, 'running_for': running_for})

    if not tasks or not cluster:
        return {'queue': '0/0', 'tasks': [{'action': 'Idle', 'status': '-'}]}

    queue = '{}/{}'.format(cluster.done_q_size, cluster.task_q_size + cluster.done_q_size)

    return {'queue': queue, 'tasks': tasks}


CURRENT_TASK = CurrentTask()


@receiver(pre_execute)
def my_pre_execute_callback(sender, func, task, **kwargs):
    print(task)
    task = CurrentTask(name=task['name'], task_id=task['id'],
                       func=task['func'].__qualname__, started=task['started'],
                       cluster_id=0)
    task.save()


def hook_set_task_ended(task):
    try:
        current_task = CurrentTask.objects.get(task_id=task.id)
        current_task.ended = True
        current_task.save()
    except ObjectDoesNotExist:
        pass