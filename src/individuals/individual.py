from simulation import Simulation
import threading
import time
import random

class Individual (threading.Thread):

    def __init__(self, id, pos, simulation: Simulation):
        super().__init__()
        self.id = id
        self.pos = pos
        self.simulation = simulation
        self.alive = True

    def get_id(self):
        return self.id;

    def get_pos(self):
        return self.pos

    def run(self):

        while (self.alive):
            if (not self._attack()):
                self._move()

            time.sleep(self.sleep_time)

    def _attack(self):
        return False

    def _move(self):
        next_pos_list = []
        matrix_size = self.simulation.get_environment().get_size()
        
        for aux_row in range(-1,2):
            for aux_col in range(-1,2):
                aux_pos = (self.pos[0] + aux_row, self.pos[1] + aux_col)
                if (aux_pos[0] in range(0, matrix_size)) and (aux_pos[1] in range(0, matrix_size)):
                    next_pos_list.append(aux_pos)

        old_pos = next_pos_list.pop(random.randrange(len(next_pos_list)))

        if not self.simulation.get_environment().update_individual_pos(self,old_pos):
            pass # Excepcion?


    def _update_pos(self, new_pos):
        old_pos = self.pos
        self.pos = new_pos
        return old_pos