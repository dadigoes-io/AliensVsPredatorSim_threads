import threading
import random
from individuals import *

class Environment():

    def __init__(self, size):
        self.size = size
        self.matrix = [[None for _ in range(size)] for _ in range(size)]
        self.mutex_matrix = [[threading.Lock() for _ in range(size)] for _ in range(size)]

    def get_size(self):
        return self.size

    def get_matrix(self):
        return self.matrix

    def get_mutex_matrix(self):
        return self.mutex_matrix

    def is_taken(self, pos):
        return self.matrix[pos[0]][pos[1]] is not None

    # Hacer atomico get_random_empty_pos y add_individual
    def add_individual(self, ind):
        pos = ind.get_pos()
        lock = self.mutex_matrix[pos[0]][pos[1]]

        # Acquire block
        lock.acquire()
        try:    
            if self.is_taken(pos):
                return False
            
            self.matrix[pos[0]][pos[1]] = ind
            return True
        finally:
            # Release block
            lock.release()

    def get_adyacents_individuals(self, pos):
        ady_blocks = self._get_adyacents_blocks()
        ady_indivs = []

        positions_to_lock = ady_blocks
        positions_to_lock.sort()

        try:
            # Acquire locks
            for lock in positions_to_lock:
                lock.acquire()

            for indiv in ady_blocks:
                if indiv:
                    ady_indivs.append(indiv)

            return ady_indivs

        finally:
            # Release locks
            for lock in positions_to_lock:
                lock.release()


    def move_individual(self, indiv: Individual, game_over):
        if game_over:
            return False
        
        next_pos_list = []
        adquired_locks = []    

        old_pos = indiv.get_pos()
        
        try:

            # Get adyacents blocks
            next_pos_list = self._get_adyacents_blocks(old_pos)

            # Create sorted list of positions to lock to avoid deadlocks
            positions_to_lock = next_pos_list + [old_pos]
            positions_to_lock.sort()
            
            # Acquire all adyacents block
            for pos in positions_to_lock:
                lock = self.mutex_matrix[pos[0]][pos[1]]
              
                if lock.acquire(blocking = (pos == old_pos)):
                    adquired_locks.append(lock)

                elif pos != old_pos:
                    next_pos_list.remove(pos)

            if not next_pos_list:
                return False

            # Check individual to move is same in matrix
            if self.matrix[old_pos[0]][old_pos[1]] is not indiv:
                raise ValueError(f"Updated individual {indiv.get_id()} error")

            new_pos = random.choice(next_pos_list)
            while(self.is_taken(new_pos)):
                next_pos_list.remove(new_pos)
                if len(next_pos_list) == 0:
                    return False
                new_pos = random.choice(next_pos_list)

            self._update_individual_pos(indiv, new_pos)
            return True

        finally:
            # Release all adyacents blocks
            for lock in adquired_locks:
                lock.release()

    def remove_individual(self, ind):
        pos = ind.get_pos()
        try:
            self.mutex_matrix[pos[0]][pos[1]].acquire()
            self.matrix[pos[0]][pos[1]] = None
        finally:
            self.mutex_matrix[pos[0]][pos[1]].release()

    def get_random_empty_pos(self):

        while True:
            row = random.randrange(self.size)
            col = random.randrange(self.size)

            if not self.is_taken((row, col)):
                return (row, col)

    def print_matrix(self):

        GREEN = "\033[92m"
        DARK_GREEN = "\033[38;5;22m"
        YELLOW = "\033[93m"
        BLUE = "\033[94m"
        RESET = "\033[0m"

        # Create a copy of matrix to minimize time of getting acquire all the matrix
        try:
            # Acquire matrix
            for lock_list in self.mutex_matrix:
                for lock in lock_list:
                    lock.acquire()

            matrix_copy = [row.copy() for row in self.matrix]

        finally:
            # Release matrix
            for lock_list in self.mutex_matrix:
                for lock in lock_list:
                    lock.release()

        # Print matrix

        for row_list in matrix_copy:
            str_out = ""

            for box in row_list:

                if box is None:
                    str_out += "□ "

                else:
                    indiv = box.get_id()[0]

                    match indiv:
                        case "Q":
                            str_out += f"{DARK_GREEN}{indiv}{RESET} "
                        case "A":
                            str_out += f"{GREEN}{indiv}{RESET} "
                        case "P":
                            str_out += f"{YELLOW}{indiv}{RESET} "
                        case "H":
                            str_out += f"{BLUE}{indiv}{RESET} "

            print(str_out)

    def _update_individual_pos(self, indiv: Individual, new_pos):
            # Call always on lock
            old_pos = indiv.get_pos()
            self.matrix[old_pos[0]][old_pos[1]] = None
            self.matrix[new_pos[0]][new_pos[1]] = indiv
            indiv.update_pos(new_pos)

    def _get_adyacents_blocks(self, pos):
        ady_blocks = []
        for aux_row in range(-1,2):
                        for aux_col in range(-1,2):
                            if not (aux_row == 0 and aux_col == 0):
                                aux_pos = (pos[0] + aux_row, pos[1] + aux_col)
                                if (aux_pos[0] in range(0, self.get_size())) and (aux_pos[1] in range(0, self.get_size())):
                                    ady_blocks.append(aux_pos)
        return ady_blocks