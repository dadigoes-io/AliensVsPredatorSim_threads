from environment import Environment

class Simulation:

    def __init__(self, enviroment: Environment):
        self.enviroment = enviroment
        self.individuals = {}    # indidivual.id, individual




def main():
    environment = Environment(10)
    simulation = Simulation(environment)