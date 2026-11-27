from environment import Environment
from query_type import QueryType
from individuals import *
from individuals.individual_type import IndividualType
from collections import deque
import time
import queue
import os


class Simulation:

    def __init__(self, enviroment: Environment, config):
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
        self.init_num_predators = config["init_num_predators"]
        self.alien_predator_ratio = config["alien_predator_ratio"]
        self.alien_eggs = 0
        self.hatching_egg_time = config["hatching_egg_time"]
        self.game_over = False

        self.alien_sleep_time = config["alien_sleep_time"]
        self.predator_sleep_time = config["predator_sleep_time"]
        self.human_sleep_time = config["human_sleep_time"]

        self.predator_gen_buffer = deque()
        self.event_buffer = deque(maxlen=15)
        self.timer = time.monotonic()

    def get_environment(self):
        return self.enviroment

    def get_game_over(self):
        return self.game_over

    def get_alien_sleep_time(self):
        return self.alien_sleep_time

    def get_predator_sleep_time(self):
        return self.predator_sleep_time

    def get_human_sleep_time(self):
        return self.human_sleep_time

    def get_hatching_egg_time(self):
        return self.hatching_egg_time


    def add_query(self, query, queri_info):
        self.queue.put((query, queri_info))

    def init(self):

        # Generate AlienQueen
        self.gen_alien_queen()
        if self.queen_id is None:
            return False

        # Generate AlienSoldiers
        for _ in range((self.init_num_predators * self.alien_predator_ratio) - 1):
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

        # Print before simulations threads starts
        self._print_simulation(force=True)

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
                self._respawn_predators()

                # Hatch alien eggs
                if self.alien_eggs > 0:
                    self._hatch_alien_egg()

            # Prints
            self._print_simulation(force=False)

            self._update_alive_threads_list()

            # Avoid busy waiting
            time.sleep(0.01)

        if not self.aliens and not self.predators:
            print("Aliens y Predators eliminados\n Nadie gana")

        elif not self.aliens:
            print("Aliens eliminados\n Predators ganan")

        elif not self.predators:
            print("Predators eliminados\n Aliens ganan")

        self._update_alive_threads_list()
        for thread in self.threads:
            thread.join()
  
    def gen_alien_queen(self):
        
        pos = self.enviroment.get_random_empty_pos()

        if pos is None:
            return None

        try:
            self.queen_id = f"AQ{self.next_alien:01d}"
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

    def _respawn_predators(self):

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

    def _print_simulation(self, force):
        if force or (time.monotonic() - self.timer >= 1):
            
            # Print matrix
            os.system("clear")
            self.enviroment.print_matrix()

            # Print buffer
            for event in self.event_buffer:
                print(event)

            self.timer = time.monotonic()

def update_config():
    config = {}

    print("Inserte tamaño N de la matriz NxN:")
    aux_input = int(input())
    if aux_input <= 0:
        raise ValueError(f"Tamaño de la matriz debe ser mayor a 0")
    config["size"] = aux_input

    print("Inserte numero inicial de Predators:")
    aux_input = int(input())
    if aux_input <= 0:
        raise ValueError(f"Numero inicial de Predators debe ser mayor a 0")
    config["init_num_predators"] = aux_input

    print("Inserte numero de inicial de Aliens por cada Predator:")
    aux_input = int(input())
    if aux_input <= 0:
        raise ValueError(f"Numero inicial de Alien por cada predator debe ser mayor a 0")
    config["alien_predator_ratio"] = aux_input
    
    print("Inserte intervalo de tiempo entre puesta de huevos:")
    aux_input = int(input())
    if aux_input <= 0:
        raise ValueError(f"Intervalo de tiempo entre puesta de huevos debe ser mayor a 0")
    config["hatching_egg_time"]= aux_input

    print("Inserte tiempo de sleep de Aliens:")
    aux_input = int(input())
    if aux_input <= 0:
        raise ValueError(f"Tiempo de sleep de Aliens debe ser mayor a 0")
    config["alien_sleep_time"] = aux_input

    print("Inserte tiempo de sleep de Predators:")
    config["predator_sleep_time"] = int(input())
    if (config["alien_sleep_time"] >= config["predator_sleep_time"]):
        raise ValueError("Predators no pueden ser más rápidos que los Aliens")

    print("Inserte tiempo de sleep de Humanos:")
    config["human_sleep_time"] = int(input())
    if (config["predator_sleep_time"] >= config["human_sleep_time"]):
        raise ValueError("Humanos no pueden ser más rápidos que los Predators")

    return config

def simulation_config():

    config = {}
    config["size"] = 75
    config["init_num_predators"] = 3
    config["alien_predator_ratio"] = 5
    config["hatching_egg_time"]= 30
    config["alien_sleep_time"] = 1
    config["predator_sleep_time"] = 2
    config["human_sleep_time"] = 3

    do_config = True
    
    while do_config:
        print("===Configuración actual de la simulación===")
        print(f"Tamaño de la matriz: {config["size"]}")
        print(f"Numero inicial de Predators: {config["init_num_predators"]}")
        print(f"Proporción de Aliens por cada Predator: {config["alien_predator_ratio"]} a 1")
        print(f"Tiempo de puesta de huevos de la reina Alien: {config["hatching_egg_time"]} seg")
        print(f"Duracion de sleep de los Aliens: {config["alien_sleep_time"]} seg")
        print(f"Duracion de sleep de los Predators: {config["predator_sleep_time"]} seg")
        print(f"Duracion de sleep de los Humanos: {config["human_sleep_time"]} seg")
    
        print("¿Quiere configurar la simulacion (Y/N)?")
        str_input = input().strip().upper()
        do_input = True

        while(do_input):

            if str_input == "Y":
                config = update_config()
                do_input = False

            elif str_input == "N":
                do_config = False
                do_input = False

            else:
                print("Valor no reconocido")
                print("¿Quiere configurar la simulacion (Y/N)?")
                str_input = input().strip().upper()

    return config

def main():

    config = simulation_config() 
    environment = Environment(config["size"])
    simulation = Simulation(environment, config)

    if simulation.init():
        simulation.run()
    else:
        print("ERROR: Initial individual generation size is over max size")

if __name__ == "__main__":
    main()