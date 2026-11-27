from .individual import Individual
from .individual_type import IndividualType

class Predator (Individual):

    def __init__(self, id, pos, simulation):
        super().__init__(id, pos, simulation)
        self.resistance = 20
        self.strength = 5
        self.sleep_time = simulation.get_predator_sleep_time()
        self.individual_type = IndividualType.PREDATOR

    def _select_target(self, ady_indivs):
        aliens = []
        humans = []
            
        for indiv in ady_indivs:
            if indiv.get_individual_type() == IndividualType.ALIEN_QUEEN:
                return indiv

            if indiv.get_individual_type() == IndividualType.ALIEN_SOLDIER:
                aliens.append(indiv)

            if indiv.get_individual_type() == IndividualType.HUMAN:
                humans.append(indiv)

        if aliens:
            return min(aliens, key=lambda alien: alien.get_resistance())

        elif humans:
            return min(humans, key=lambda human: human.get_resistance())
            
        else:
            return None