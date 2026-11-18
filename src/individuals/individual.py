import threading
import time
from abc import ABC, abstractmethod
from alien import Alien

class Individual (threading.Thread, ABC):

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

    def get_resistance(self):
        return self.resistance

    def get_alive(self):
        return self.alive

    def update_pos(self, new_pos):
        self.pos = new_pos

    def run(self):

        while (self.alive):
            if (not self._attack()):
                self._move()

            time.sleep(self.sleep_time)

    def receive_damage(self, damage):
        self.resistance -= damage

        if self.resistance <= 0:
            self.alive = False

        # incluir remove_individual()?

    def _attack(self):
        
        ady_indivs = self.simulation.get_environment().get_adyacents_individuals(self.pos)

        if not ady_indivs:
            return False

        target : Individual = self._select_target(ady_indivs)

        if target is None:
            return False

        self._combat(target)        

        return True

    def _combat(self, target):

        enviroment = self.simulation.get_environment()

        enviroment.lock_positions([self.get_pos(), target.get_pos()])

        target.receive_damage(self.strength)

        if not target.get_alive():
            enviroment.remove_individual(target)
            self.simulation.remove_individual(self)

        if isinstance(target, Alien):
            self.receive_damage(1)

        if not self.get_alive():
            enviroment.remove_individual(self)
            self.simulation.remove_individual(self)

        else:
            # Comprobar modularizacion o crear move para positions ya locked?
            enviroment.move_individual(self, self.simulation.get_game_over())

        enviroment.unlock_positions([self.get_pos(), target.get_pos()])

    def _move(self):
        self.simulation.get_environment().move_individual(self,
                                                          self.simulation.get_game_over()
                                                          )

    @abstractmethod
    def _select_target(self, ady_indivs):
        pass
            