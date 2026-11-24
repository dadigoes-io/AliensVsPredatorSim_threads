from abc import ABC, abstractmethod
from .individual import Individual
from .individual_type import IndividualType

class Alien (Individual, ABC):

    @abstractmethod
    def __init__(self, id, pos, simulation):
        super().__init__(id, pos, simulation)
        self.sleep_time = 1

    def get_splatter_damage(self):
        return 1

    def _select_target(self, ady_indivs):
        predators = []
        humans = []

        for indiv in ady_indivs:
            if indiv.get_individual_type() == IndividualType.PREDATOR:
                predators.append(indiv)

            if indiv.get_individual_type() == IndividualType.HUMAN:
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
        self.individual_type = IndividualType.ALIEN_QUEEN

class AlienSoldier (Alien):

    def __init__(self, id, pos, simulation):
        super().__init__(id, pos, simulation)
        self.resistance = 5
        self.strength = 4
        self.individual_type = IndividualType.ALIEN_SOLDIER