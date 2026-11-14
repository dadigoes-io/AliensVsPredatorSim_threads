from .individual import Individual

class Predator (Individual):

    def __init__(self, id, pos, simulation):
        super().__init__(id, pos, simulation)
        self.resistance = 20
        self.strength = 5