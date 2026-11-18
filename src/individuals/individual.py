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

    def is_individual_alive(self):
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

        if self.simulation.get_game_over():
            return False

        if not self.is_individual_alive():
            return False

        environment = self.simulation.get_environment()

        # Select target
        target = environment.get_individual_target(self)
        
        # Attack target
        self._combat(target)

        # Move over dead target
        if not target.is_individual_alive():
            if not self.environment.move_individual(self, target.get_pos(), self.simulation.get_game_over())
                raise ValueError(f"Move individual {self.get_id()} error")
            
        # Release individuals
        environment.unlock_positions([self, target])       

        return True

    def _combat(self, target):

        enviroment = self.simulation.get_environment()

        # Damage over target
        target.receive_damage(self.strength)
        if not target.get_alive():
            enviroment.remove_individual(target)
            self.simulation.remove_individual(self)

        if isinstance(target, Alien):
            self.receive_damage(target.get_splatter_damage())
            if not self.get_alive():
                enviroment.remove_individual(self)
                self.simulation.remove_individual(self)

    def _move(self):
        self.simulation.get_environment().move_individual_random(self,
                                                          self.simulation.get_game_over()
                                                          )

    @abstractmethod
    def _select_target(self, ady_indivs):
        pass
            