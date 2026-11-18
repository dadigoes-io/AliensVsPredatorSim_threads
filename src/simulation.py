from environment import Environment
from individuals import *
import time
import queue

class Simulation:

    def __init__(self, enviroment: Environment):
        self.enviroment = enviroment
        self.queue = queue.Queue()
        self.aliens = {}    # individual.id, individual
        self.predators = {}
        self.humans = {}
        self.next_alien = 0
        self.next_predator = 0
        self.next_human = 0
        self.game_over = False

    def get_environment(self):
        return self.enviroment

    def get_game_over(self):
        return self.game_over

    def gen_queen_alien(self):
        id = f"QA{self.next_alien:01d}"

        self.aliens[id] = AlienQueen(id,
                                     self.enviroment.get_random_empty_pos(),
                                     self)

        if self.enviroment.add_individual(self.aliens[id]):
            self.next_alien += 1
        else:
            self.aliens.pop(id)
        

    def gen_alien(self):
        id = f"A{self.next_alien:02d}"
        self.aliens[id] = AlienSoldier(id,
                                       self.enviroment.get_random_empty_pos(),
                                       self)
        
        if self.enviroment.add_individual(self.aliens[id]):
            self.next_alien += 1
        else:
            self.aliens.pop(id)

    def gen_predator(self):
        id = f"P{self.next_predator:02d}"
        self.predators[id] = Predator(id,
                                      self.enviroment.get_random_empty_pos(),
                                      self)

        if self.enviroment.add_individual(self.predators[id]):
            self.next_predator += 1
        else:
            self.predators.pop(id)

    def gen_human(self):
        id = f"H{self.next_human:02d}"
        self.humans[id] = Human(id,
                                self.enviroment.get_random_empty_pos(),
                                self)

        if self.enviroment.add_individual(self.humans[id]):
            self.next_human += 1
        else:
            self.humans.pop(id)

    def remove_individual(self, target):
            pass    # Un remove para todos los indivs o un remove para cada indiv?

    def init(self):
        self.gen_queen_alien()
        for _ in range(2):
            self.gen_alien()

        for _ in range(5):
            self.gen_predator()

        for _ in range(10):
            self.gen_human()


    def run(self):

        # Start threads execution
        for individuals in (self.aliens, self.predators, self.humans):
            for indiv in individuals.values():
                indiv.start()

        while not self.game_over:
            print("\033[H\033[J", end="", flush=True)
            self.enviroment.print_matrix()

            if (not self.aliens or not self.predators):
                self.game_over = True

            time.sleep(1)   # Sustituir por un count,
                            # no es buena idea dormir
                            # el hilo de ejecucion principal?

        if not self.aliens:
            print("Aliens eliminados")

        if not self.predators:
            print("Predators eliminados")

def main():
    environment = Environment(25)
    simulation = Simulation(environment)
    simulation.init()
    simulation.run()

main()