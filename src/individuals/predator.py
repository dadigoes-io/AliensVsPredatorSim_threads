from .individual import Individual
from alien import AlienQueen, AlienSoldier
from human import Human

class Predator (Individual):

    def __init__(self, id, pos, simulation):
        super().__init__(id, pos, simulation)
        self.resistance = 20
        self.strength = 5
        self.sleep_time = 2

    def _select_target(self, ady_indivs):
        aliens = []
        humans = []
            
        for indiv in ady_indivs:
            if isinstance(indiv, AlienQueen):
                return indiv

                if isinstance(indiv, AlienSoldier):
                    aliens.append(indiv)

                if isinstance(indiv, Human):
                    humans.append(indiv)

            if aliens:
                return min(aliens, key=lambda alien: alien.get_resistance())

            elif humans:
                return min(humans, key=lambda human: human.get_resistance())
                
            else:
                return None