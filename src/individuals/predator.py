from individual import Individual

class Predator (Individual):

    def __init__(self, simulation):
        super.__init__(simulation)
        self.id = ""
        self.resistance = 20
        self.strength = 5