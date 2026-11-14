from individual import Individual

class Human (Individual):

    def __init__(self, simulation):
        super.__init__(simulation)
        self.id = ""
        self.resistance = 3
        self.strength = 2