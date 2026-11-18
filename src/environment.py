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

    def get_individual_target(self, indiv : Individual):
        indiv_pos = indiv.get_pos()
        ady_pos_list = self._get_adyacents_positions(indiv_pos)
        ady_indivs = []

        positions_to_lock = ady_pos_list
        positions_to_lock.sort()

        acquired_locks = []

        try:
            # Acquire locks
            lock = self.mutex_matrix[indiv_pos[0]][indiv_pos[1]]
            if not lock.acquire(blocking = False):
                return False

            for pos in positions_to_lock:
                lock = self.mutex_matrix[pos[0]][pos[1]]
                lock.acquire()
                acquired_locks.append(lock)

            # Get adyacent targets
            for pos in ady_pos_list:
                indiv = self.matrix[pos[0]][pos[1]]
                if indiv:
                    ady_indivs.append(indiv)

            target = indiv._select_target(ady_indivs)

            if not target.is_individual_alive():
                return None

            acquired_locks.remove(target.get_pos())

            return target

        finally:
            # Release locks except indiv and target
            for lock in acquired_locks:
                lock.release()

    def move_individual_random(self, indiv: Individual, game_over):
        if game_over:
            return False
        
        next_pos_list = []
        adquired_locks = []    

        old_pos = indiv.get_pos()
        
        try:
            # Get adyacents pos
            next_pos_list = self._get_adyacents_positions(old_pos)

            lock = self.mutex_matrix[old_pos[0]][old_pos[1]]
            
            if not lock.acquire(blocking = False):
                return False

            adquired_locks.append(lock)

            # Create sorted list of positions to lock to avoid deadlocks
            positions_to_lock = next_pos_list
            positions_to_lock.sort()
            
            # Acquire all adyacents block
            for pos in positions_to_lock:
                lock = self.mutex_matrix[pos[0]][pos[1]]
                if lock.acquire(blocking = False):
                    adquired_locks.append(lock)
                else:
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

    def move_individual(self, indiv: Individual, new_pos, game_over):
        if game_over:
            return False

        old_pos = indiv.get_pos()

        if not self.mutex_matrix[old_pos[0]][old_pos[1]].locked():
            raise ValueError(f"Old individual {indiv.get_id()} not locked")
            
        if self.mutex_matrix[new_pos[0]][new_pos[1]].locked():
            raise ValueError(f"New individual {indiv.get_id()} not locked")

        self.matrix[old_pos[0]][old_pos[1]] = None
        self.matrix[new_pos[0]][new_pos[1]] = indiv
        
        self._update_individual_pos(indiv, new_pos)
        return True
    
    def remove_individual(self, indiv):
        pos = indiv.get_pos()
        try:
            self.mutex_matrix[pos[0]][pos[1]].acquire()

            # Check individual to remove is same in matrix
            if self.matrix[pos[0]][pos[1]] is not indiv:
                raise ValueError(f"Updated individual {indiv.get_id()} error")

            self.matrix[pos[0]][pos[1]] = None
        finally:
            self.mutex_matrix[pos[0]][pos[1]].release()

    def get_random_empty_pos(self):

        while True:
            row = random.randrange(self.size)
            col = random.randrange(self.size)

            if not self.is_taken((row, col)):
                return (row, col)

    def lock_positions(self, list_pos):
        for pos in list_pos:
            self.mutex_matrix[pos[0], pos[1]].acquire()

    def unlock_positions(self, list_pos):
        for pos in list_pos:
            self.mutex_matrix[pos[0], pos[1]].release()

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

    def _get_adyacents_positions(self, pos):
        ady_pos = []
        for aux_row in range(-1,2):
                        for aux_col in range(-1,2):
                            if not (aux_row == 0 and aux_col == 0):
                                aux_pos = (pos[0] + aux_row, pos[1] + aux_col)
                                if (aux_pos[0] in range(0, self.get_size())) and (aux_pos[1] in range(0, self.get_size())):
                                    ady_pos.append(aux_pos)
        return ady_pos