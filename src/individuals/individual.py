import threading

class Individual (threading.Thread):

    def __init__(self, id, pos, simulation):
        super().__init__()
        self.id = id
        self.pos = pos
        self.simulation = simulation
        self.alive = True

    def get_id(self):
        return self.id;
