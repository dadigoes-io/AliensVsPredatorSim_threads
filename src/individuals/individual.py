import threading
from abc import ABC, abstractmethod

class Individual (threading.Thread, ABC):

    @abstractmethod
    def __init__(self, id, pos, simulation):
        super().__init__()
        self.id = id
        self.pos = pos
        self.simulation = simulation
        self.alive = True
