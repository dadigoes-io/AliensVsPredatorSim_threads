from .individual import Individual
from abc import ABC, abstractmethod

class Alien (Individual):

    @abstractmethod
    def __init__(self, id, pos, simulation):
        super().__init__(id, pos, simulation)

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