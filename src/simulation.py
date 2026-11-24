from environment import Environment
from query_type import QueryType
from individuals import *
from individuals.individual_type import IndividualType
import time
import queue
from collections import deque


class Simulation:

    def __init__(self, enviroment: Environment):
        self.enviroment = enviroment
        self.threads = []
        self.queue = queue.Queue()
        self.aliens = {}    # individual.id, individual
        self.predators = {}
        self.humans = {}
        self.queen_id = None
        self.next_alien = 0
        self.next_predator = 0
        self.next_human = 0
        self.init_num_predators = 3
        self.alien_eggs = 0
        self.event_buffer = deque(maxlen=15)
        self.timer = time.monotonic()
        self.predator_gen_buffer = deque()
        self.game_over = False

    def get_environment(self):
        return self.enviroment

    def get_game_over(self):
        return self.game_over

    def add_query(self, query, queri_info):
        self.queue.put((query, queri_info))

    def gen_queen_alien(self):
        self.queen_id = f"QA{self.next_alien:01d}"

        self.aliens[id] = AlienQueen(self.queen_id,
                                     self.enviroment.get_random_empty_pos(),
                                     self)

        if self.enviroment.add_individual(self.aliens[self.queen_id ], locked=False):
            self.next_alien += 1
        else:
            self.aliens.pop(id)
        
    def gen_alien(self, pos):
        pos_locked = pos is not None
        if pos is None:
            pos = self.enviroment.get_random_empty_pos()

        id = f"A{self.next_alien:02d}"
        self.aliens[id] = AlienSoldier(id, pos, self)
        if self.enviroment.add_individual(self.aliens[id], locked=pos_locked):
            self.next_alien += 1
            return id
        else:
            self.aliens.pop(id)
            return None

    def gen_predator(self):
        id = f"P{self.next_predator:02d}"
        self.predators[id] = Predator(id,
                                      self.enviroment.get_random_empty_pos(),
                                      self)

        if self.enviroment.add_individual(self.predators[id], locked=False):
            self.next_predator += 1
            return id
        else:
            self.predators.pop(id)
            return None

    def gen_human(self):
        id = f"H{self.next_human:02d}"
        self.humans[id] = Human(id,
                                self.enviroment.get_random_empty_pos(),
                                self)

        if self.enviroment.add_individual(self.humans[id], locked=False):
            self.next_human += 1
            return id
        else:
            self.humans.pop(id)
            return None

    def gen_alien_egg(self, pos):

        new_pos = self.enviroment.get_random_ady_pos(pos)

        if new_pos is None:
            return None
        
        try:
            return self.gen_alien(new_pos)
        
        finally:
            # Release lock after generate new alien in gen_alien()
            self.enviroment.get_mutex_matrix()[new_pos[0]][new_pos[1]].release()
    
    def init(self):
        self.gen_queen_alien()
        for _ in range((self.init_num_predators * 5) - 1):
            generated = self.gen_alien(None) is not None
            while not generated:
                generated = self.gen_alien(None)

        for _ in range(self.init_num_predators):
            generated = self.gen_predator() is not None
            while not generated:
                generated = self.gen_predator()

        for _ in range(self.init_num_predators * 10):
            generated = self.gen_human() is not None
            while not generated:
                generated = self.gen_human()

    def run(self):

        # Start threads execution
        for individuals in (self.aliens, self.predators, self.humans):
            for indiv in individuals.values():
                indiv.start()
                self.threads.append(indiv)

        while not self.game_over:

            # Gen predators
            if self.predator_gen_buffer and self.predators:
                predator_timer = self.predator_gen_buffer[0] 
                while (time.monotonic() - predator_timer > 5):

                    # Remove predator timer
                    self.predator_gen_buffer.popleft()
                    
                    # Generate new predator
                    predator_id = self.gen_predator()
                    while predator_id is None:
                        predator_id = self.gen_predator()

                    # Start new thread
                    predator = self.predators[predator_id]
                    predator.start()
                    self.threads.append(predator)

                    predator_timer = self.predator_gen_buffer[0]
                    self.event_buffer.append(f"Humano {predator_id} generado")

            # Hatch alien eggs
            if self.alien_eggs > 0:
                self._hatch_alien_egg()

            # Check queries from queue
            if queue:
                self.queue_queries()

            # Prints
            if time.monotonic() - self.timer >= 1:
                # Print matrix
                print("\033[H\033[J", end="", flush=True)
                self.enviroment.print_matrix()
                # Print buffer
                for event in self.event_buffer:
                    print(event)

                self.timer = time.monotonic()

            if (not self.aliens or not self.predators):
                self.game_over = True

        if not self.aliens and not self.predators:
            print("Aliens and Predators terminated\n Nobody wins")

        if not self.aliens:
            print("Aliens terminated\n Predators wins")

        if not self.predators:
            print("Predators terminated\n Aliens wins")

        for thread in self.threads:
            thread.join()

    def queue_queries(self):
        while self.queue:
            query_type, data = self.queue.get()
            match query_type:
                case QueryType.ATTACK:
                    # data = attacker.id, target.id, target.pos
                    attacker_id = data[0]
                    target_id = data[1]
                    target_pos = data[2]
                    self.event_buffer.append(f"{attacker_id} ha atacado a {target_id} en {target_pos}")

                    # Añadir mensaje a buffer

                case QueryType.DEATH:
                    # data = attacker.id, target.id, target.pos, target.type, splatter_death
                    attacker_id = data[0]
                    target_id = data[1]
                    target_pos = data[2]
                    target_type = data[3]
                    splatter_death = data[4]

                    if splatter_death:
                        self.event_buffer.append(f"{target_id} ha muerto por el ácido de {attacker_id} en {target_pos}")
                    else:
                        self.event_buffer.append(f"{attacker_id} ha matado a {target_id} en {target_pos}")
                        
                    match target_type:
                        case IndividualType.ALIEN_QUEEN:
                            self.alien_eggs = 0
                            self.aliens.pop(target_id)

                        case IndividualType.ALIEN_SOLDIER:
                            self.aliens.pop(target_id)

                        case IndividualType.PREDATOR:
                            self.predators.pop(target_id)
                            # Add predator generation timer
                            self.predator_gen_buffer.append(time.monotonic())

                        case IndividualType.HUMAN:
                            self.humans.pop(target_id)

                            # Generate new human
                            human_id = self.gen_human()
                            while human_id is None:
                                human_id = self.gen_human()

                            # Start new thread
                            human = self.humans[human_id]
                            human.start()
                            self.threads.append(human)

                            self.event_buffer.append(f"Humano {human_id} generado")

                case QueryType.HATCH_EGG:
                    # data = None
                    self.alien_eggs += 1

    def _hatch_alien_egg(self):
        alien_queen = self.aliens.get(self.queen_id)
        if alien_queen and alien_queen.is_individual_alive():
            pos = alien_queen.get_pos()
            try:
                # Locking queen position to avoid her to move while hatching eggs
                lock = self.enviroment.get_mutex_matrix()[pos[0]][pos[1]]
                if lock.acquire(blocking=False):

                    # Attempting to generate new alien
                    alien_id = self.gen_alien_egg(self.aliens.get(self.queen_id).get_pos())

                    if alien_id is not None:

                        self.alien_eggs -= 1
                        self.event_buffer.append(f"Ha eclosionado alien {alien_id}")

                        # Start new thread
                        alien = self.aliens[alien_id]
                        alien.start()
                        self.threads.append(alien)
            finally:
                lock.release()

def main():
    environment = Environment(50)
    simulation = Simulation(environment)
    simulation.init()
    simulation.run()

main()