import threading
from abc import ABC, abstractmethod

class Individual (threading.Thread, ABC):

    @abstractmethod
    def __init__(self, simulation):
        super().__init__()
        self.simulation = simulation
        self.alive = True
