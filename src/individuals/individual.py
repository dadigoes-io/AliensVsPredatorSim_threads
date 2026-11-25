import threading
import time
from .individual_type import IndividualType
from abc import ABC, abstractmethod
from query_type import QueryType

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

    def get_individual_type(self):
        return self.individual_type

    def update_pos(self, new_pos):
        self.pos = new_pos

    def run(self):

        while (self.alive and not self.simulation.get_game_over()):
            if not self.simulation.get_environment().is_locked(self.get_pos()):
                if (not self._attack()):
                    self._move()
                if self.alive:
                    self._incubate_eggs()

            time.sleep(self.sleep_time)

    def _attack(self):

        old_pos = self.pos

        if not self.alive:
            return False

        environment = self.simulation.get_environment()

        # Checking game over before selecting target
        if self.simulation.get_game_over():
            return False

        # Select target
        target = environment.get_individual_target(self)

        if not target:
            return False

        target_pos = target.get_pos()
        
        try:
            # Checking game over before attacking target
            if self.simulation.get_game_over():
                return False
            
            # Attack target
            self._combat(target)

            # Move over target pos if self is alive and target is dead
            if not target.is_individual_alive() and self.alive:
                
                # Checking game over before moving (return True to avoid _move())
                if not self.simulation.get_game_over():
                    if not environment.move_individual_locked(self, target_pos):
                        raise ValueError(f"Move individual {self.get_id()} error")
            
            return True
        
        finally:
            environment.unlock_positions([old_pos, target_pos]) 
        
    def _combat(self, target):

        environment = self.simulation.get_environment()

        # Damage over target
        target._receive_damage(self.strength)
        if target.is_individual_alive():
            self.simulation.add_query(QueryType.ATTACK, (self.get_id(), target.get_id(), target.get_pos()))
        else:
            environment.remove_individual_locked(target)
            self.simulation.add_query(QueryType.DEATH, (self.get_id(),  target.get_id(), target.get_pos(), target.get_individual_type(), False))

        self._receive_damage(target.get_splatter_damage())
        if not self.alive:  # Because of splatter damage
            environment.remove_individual_locked(self)
            self.simulation.add_query(QueryType.DEATH, (target.get_id(),  self.get_id(), self.get_pos(), self.get_individual_type(), True))

    def _receive_damage(self, damage):
        self.resistance -= damage

        if self.resistance <= 0:
            self.alive = False

    def _move(self):
        # Checking game over before attacking
        if self.simulation.get_game_over():
            return False
        
        self.simulation.get_environment().move_individual_random(self)

    def get_splatter_damage(self):
        return 0
    
    @abstractmethod
    def _select_target(self, ady_indivs):
        pass

    def _incubate_eggs(self):
        pass
            