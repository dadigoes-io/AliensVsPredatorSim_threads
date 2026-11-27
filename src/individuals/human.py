from .individual import Individual
from .individual_type import IndividualType


class Human (Individual):

    def __init__(self, id, pos, simulation):
        super().__init__(id, pos, simulation)
        self.resistance = 3
        self.strength = 2
        self.sleep_time = simulation.get_human_sleep_time()
        self.individual_type = IndividualType.HUMAN

    def _select_target(self, ady_indivs):
        targets = []

        for indiv in ady_indivs:
            if indiv.get_individual_type() == IndividualType.ALIEN_QUEEN:
                return indiv

            if indiv.get_individual_type() == IndividualType.ALIEN_SOLDIER:
                targets.append(indiv)

            if indiv.get_individual_type() == IndividualType.PREDATOR:
                targets.append(indiv)

        if targets:
            return min(targets, key=lambda target: target.get_resistance())
                
        else:
            return None