from .individual import Individual
from abc import ABC, abstractmethod
from predator import Predator
from human import Human

class Alien (Individual, ABC):

    @abstractmethod
    def __init__(self, id, pos, simulation):
        super().__init__(id, pos, simulation)
        self.sleep_time = 1

    def _select_target(self, ady_indivs):
        predators = []
        humans = []

        for indiv in ady_indivs:
            if isinstance(indiv, Predator):
                predators.append(indiv)
                
            if isinstance(indiv, Human):
                humans.append(indiv)

        if predators:
            return min(predators, key=lambda predator: predator.get_resistance())

        elif humans:
            return min(humans, key=lambda human: human.get_resistance())
            
        else:
            return None

class AlienQueen (Alien):

    def __init__(self, id, pos, simulation):
        super().__init__(id, pos, simulation)
        self.resistance = 100
        self.strength = 15

class AlienSoldier (Alien):

    def __init__(self, id, pos, simulation):
        super().__init__(id, pos, simulation)
        self.resistance = 5
        self.strength = 4