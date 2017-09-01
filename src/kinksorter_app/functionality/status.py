from django.dispatch import receiver
from django_q.signals import pre_enqueue, pre_execute
from django_q.monitor import Stat


class CurrentTask:
    def __init__(self, cluster):
        self.action = None
        self.status = None
        self.cluster = cluster

    def set(self, func, status, queue):
        self.action = func
        self.status = status

    def __bool__(self):
        return self.action is not None

    def to_dict(self):
        action = self.action if self.action else 'Idle'
        status = self.status if self.status else '-'
        queue = '{}/{}'.format(self.cluster.done_q_size, self.cluster.task_q_size + self.cluster.done_q_size)
        return {'action': action, 'status': status + queue}

stat = Stat.get_all()[0]
CURRENT_TASK = CurrentTask(stat)


@receiver(pre_execute)
def my_pre_execute_callback(sender, func, task, **kwargs):
    print("Task {} will be executed by calling {}".format(
          task["name"], func))
    print(task)
    print(func)
    print(type(sender))
    CURRENT_TASK.set(task['name'], func, None)
