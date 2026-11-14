from individual import Individual
from abc import ABC, abstractmethod

class Alien (Individual,ABC):

    @abstractmethod
    def __init__(self, simulation):
        super().__init__(simulation)

class AlienQueen (Alien):

    def __init__(self, simulation):
        super().__init__(simulation)
        self.resistance = 100
        self.strength = 15

class AlienSoldier (Alien):

    def __init__(self, simulation):
        super().__init__(simulation)
        self.resistance = 5
        self.strength = 4