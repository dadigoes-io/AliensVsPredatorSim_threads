from .individual import Individual

class Human (Individual):

    def __init__(self, id, pos, simulation):
        super().__init__(id, pos, simulation)
        self.resistance = 3
        self.strength = 2
        self.sleep_time = 3