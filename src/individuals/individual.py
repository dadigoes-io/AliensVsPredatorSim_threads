import threading
import time

class Individual (threading.Thread):

    def __init__(self, id, pos, simulation):
        super().__init__()
        self.id = id
        self.pos = pos
        self.simulation = simulation
        self.alive = True

    def get_id(self):
        return self.id;

    def get_pos(self):
        return self.pos

    def update_pos(self, new_pos):
        self.pos = new_pos

    def run(self):

        while (self.alive):
            if (not self._attack()):
                self._move()

            time.sleep(self.sleep_time)

    def _attack(self):
        return False

    def _move(self):
        self.simulation.get_environment().move_individual(self)