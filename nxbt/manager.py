from multiprocessing import Process
from multiprocessing import Queue

from .controller import ControllerServer
from .controller import ControllerTypes


class Nxbt():

    def __init__(self):

        self.task_queue = Queue()
