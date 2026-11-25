from environment import Environment
from query_type import QueryType
from individuals import *
from individuals.individual_type import IndividualType
from collections import deque
import time
import queue
import os


class Simulation:

    def __init__(self, enviroment: Environment):
        self.enviroment = enviroment
        self.queue = queue.Queue()
        self.threads = []
        
        self.aliens = {}    # individual.id, individual
        self.predators = {}
        self.humans = {}
        
        self.next_alien = 0
        self.next_predator = 0
        self.next_human = 0

        self.queen_id = None
        self.init_num_predators = 3
        self.alien_eggs = 0
        self.game_over = False

        self.predator_gen_buffer = deque()
        self.event_buffer = deque(maxlen=15)
        self.timer = time.monotonic()

    def get_environment(self):
        return self.enviroment

    def get_game_over(self):
        return self.game_over

    def add_query(self, query, queri_info):
        self.queue.put((query, queri_info))

    def init(self):

        # Generate AlienQueen
        self.gen_alien_queen()
        if self.queen_id is None:
            return False

        # Generate AlienSoldiers
        for _ in range((self.init_num_predators * 5) - 1):
            if self.gen_alien(None) is None:
                return False

        # Generate Predators
        for _ in range(self.init_num_predators):
            if self.gen_predator() is None:
                return False

        # Generate Humans
        for _ in range(self.init_num_predators * 10):
            if self.gen_human() is None:
                return False

        return True

    def run(self):

        # Start threads execution
        for individuals in (self.aliens, self.predators, self.humans):
            for indiv in individuals.values():
                indiv.start()
                self.threads.append(indiv)

        while not self.game_over:

            # Check queries from queue
            self.queue_queries()

            if (not self.aliens or not self.predators):
                self.game_over = True

            if not self.game_over:

                # Gen predators
                if self.predator_gen_buffer and self.predators:
                    predator_timer = self.predator_gen_buffer[0] 
                    while (self.predator_gen_buffer and (time.monotonic() - predator_timer > 5)):

                        # Generate new predator
                        predator_id = self.gen_predator()
                        if predator_id is not None:
                            # Start new thread
                            predator = self.predators[predator_id]
                            predator.start()
                            self.threads.append(predator)

                            self.event_buffer.append(f"Predator {predator_id} generado")
                        else:
                            self.event_buffer.append("ERROR: No space for generating predator")

                        # Remove predator timer
                        self.predator_gen_buffer.popleft()

                        # Get another predator timer
                        if self.predator_gen_buffer:
                            predator_timer = self.predator_gen_buffer[0]

                # Hatch alien eggs
                if self.alien_eggs > 0:
                    self._hatch_alien_egg()

            # Prints
            if time.monotonic() - self.timer >= 1:
                # Print matrix
                os.system("clear")
                self.enviroment.print_matrix()
                # Print buffer
                for event in self.event_buffer:
                    print(event)

                self.timer = time.monotonic()
                self._update_alive_threads_list()

            # Avoid busy waiting
            time.sleep(0.01)

        if not self.aliens and not self.predators:
            print("Aliens and Predators terminated\n Nobody wins")

        elif not self.aliens:
            print("Aliens terminated\n Predators wins")

        elif not self.predators:
            print("Predators terminated\n Aliens wins")

        self._update_alive_threads_list()
        for thread in self.threads:
            thread.join()
  
    def gen_alien_queen(self):
        
        pos = self.enviroment.get_random_empty_pos()

        if pos is None:
            return None

        try:
            self.queen_id = f"QA{self.next_alien:01d}"
            self.aliens[self.queen_id] = AlienQueen(self.queen_id, pos, self)

            if self.enviroment.add_individual(self.aliens[self.queen_id], locked=True):
                self.next_alien += 1
            else:
                self.aliens.pop(self.queen_id)
                self.queen_id = None
                
        finally:
            self.enviroment.get_mutex_matrix()[pos[0]][pos[1]].release()
        
    def gen_alien(self, pos):
        # pos can have a value generated from _gen_alien_egg()
        if pos is None:
            pos = self.enviroment.get_random_empty_pos()
            if pos is None:
                return None
        
        try:
            id = f"A{self.next_alien:02d}"
            self.aliens[id] = AlienSoldier(id, pos, self)
            if self.enviroment.add_individual(self.aliens[id], locked=True):
                self.next_alien += 1
                return id
            else:
                self.aliens.pop(id)
                return None
        finally:
            self.enviroment.get_mutex_matrix()[pos[0]][pos[1]].release()

    def gen_predator(self):
    
        pos = self.enviroment.get_random_empty_pos()
        
        if pos is None:
            return None
        try:
            id = f"P{self.next_predator:02d}"
            self.predators[id] = Predator(id, pos, self)

            if self.enviroment.add_individual(self.predators[id], locked=True):
                self.next_predator += 1
                return id
            else:
                self.predators.pop(id)
                return None
        finally:
            self.enviroment.get_mutex_matrix()[pos[0]][pos[1]].release()

    def gen_human(self):

        pos = self.enviroment.get_random_empty_pos()
        
        if pos is None:
            return None
        try:
            id = f"H{self.next_human:02d}"
            self.humans[id] = Human(id, pos, self)

            if self.enviroment.add_individual(self.humans[id], locked=True):
                self.next_human += 1
                return id
            else:
                self.humans.pop(id)
                return None
        finally:
            self.enviroment.get_mutex_matrix()[pos[0]][pos[1]].release()

    def gen_alien_egg(self, pos):

        new_pos = self.enviroment.get_random_ady_pos(pos)

        if new_pos is None:
            return None
        
        return self.gen_alien(new_pos)
          
    def queue_queries(self):

        while not self.queue.empty():

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
                            if human_id is not None:
                                # Start new thread
                                human = self.humans[human_id]
                                human.start()
                                self.threads.append(human)

                                self.event_buffer.append(f"Humano {human_id} generado")
                            else:
                                self.event_buffer.append("ERROR: No space for generating human")

                case QueryType.HATCH_EGG:
                    # data = None
                    queen = self.aliens.get(self.queen_id)

                    if queen and queen.is_individual_alive():
                        self.alien_eggs += 1
 
    def _hatch_alien_egg(self):
        alien_queen = self.aliens.get(self.queen_id)
        if alien_queen and alien_queen.is_individual_alive():
            pos = alien_queen.get_pos()

            # Locking queen position to avoid her to move while hatching eggs
            lock = self.enviroment.get_mutex_matrix()[pos[0]][pos[1]]
            lock_acquired = lock.acquire(blocking=False)

            try:
                
                if lock_acquired:

                    # Checking queen didnt move while locking her position, and also didnt die
                    if self.enviroment.get_matrix()[pos[0]][pos[1]] is alien_queen and alien_queen.is_individual_alive():

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
                if lock_acquired:
                    lock.release()

    def _update_alive_threads_list(self):

        alive_threads = []

        for thread in self.threads:
            if thread.is_alive():
                alive_threads.append(thread)
            else:
                thread.join()

        self.threads = alive_threads

def main():
    environment = Environment(50)
    simulation = Simulation(environment)
    if simulation.init():
        simulation.run()
    else:
        print("ERROR: Initial individual generation size is over max size")

if __name__ == "__main__":
    main()