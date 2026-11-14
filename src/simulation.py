from environment import Environment
from individuals import *

class Simulation:

    def __init__(self, enviroment: Environment):
        self.enviroment = enviroment
        self.aliens = {}    # individual.id, individual
        self.predators = {}
        self.humans = {}
        self.next_alien = 0
        self.next_predator = 0
        self.next_human = 0

    def init(self):
        self.add_queen_alien()
        for _ in range(4):
            self.gen_alien()

        for _ in range(5):
            self.gen_predator()

        for _ in range(10):
            self.gen_human()


    def run(self):

        while(1):
            pass

    def get_environment(self):
        return self.enviroment

    def gen_queen_alien(self):
        id = f"QA{self.next_alien:02d}"

        self.aliens[id] = AlienQueen(id,
                                     self.enviroment.get_random_empty_pos(),
                                     self.simulation)

        self.enviroment.add_individual(self.aliens[id])

    def gen_alien(self):
        id = f"A{self.next_alien:02d}"
        self.aliens[id] = AlienSoldier(id,
                                       self.enviroment.get_random_empty_pos(),
                                       self.simulation)
        
        self.enviroment.add_individual(self.aliens[id])

    def gen_predator(self):
        id = f"P{self.next_predator:02d}"
        self.predators[id] = Predator(id,
                                      self.enviroment.get_random_empty_pos(),
                                      self.simulation)

        self.enviroment.add_individual(self.predators[id])

    def gen_human(self):
        id = f"P{self.next_human:02d}"
        self.humans[id] = Human(id,
                                self.enviroment.get_random_empty_pos(),
                                self.simulation)

        self.enviroment.add_individual(self.humans[id])

def main():
    environment = Environment(75)
    simulation = Simulation(environment)
    simulation.init()
    simulation.run()