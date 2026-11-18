from .individual import Individual
from alien import AlienQueen, AlienSoldier
from predator import Predator

class Human (Individual):

    def __init__(self, id, pos, simulation):
        super().__init__(id, pos, simulation)
        self.resistance = 3
        self.strength = 2
        self.sleep_time = 3

    def _select_target(self, ady_indivs):
        targets = []

        for indiv in ady_indivs:
            if isinstance(indiv, AlienQueen):
                return indiv

            if isinstance(indiv, AlienSoldier):
                targets.append(indiv)

            if isinstance(indiv, Predator):
                targets.append(indiv)

        if targets:
            return min(targets, key=lambda target: target.get_resistance())
                
        else:
            return None