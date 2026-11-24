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
    def add_individual(self, ind, locked):
        # If pos is prev locked (from hatching egg)
        if locked:
            return self._add_individual_locked(ind)
        
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

    def _add_individual_locked(self, ind):
            pos = ind.get_pos()
 
            if self.is_taken(pos):
                return False

            if not self.get_mutex_matrix[pos[0]][pos[1]].locked():
                return False
                
            self.matrix[pos[0]][pos[1]] = ind
            return True 

    def get_individual_target(self, indiv : Individual):
        indiv_pos = indiv.get_pos()
        targets_pos = self._get_adyacents_positions(indiv_pos)
        adquired_pos = []
        acquired_locks = []
        ady_indivs = []
        indiv_locked = False
        target_found = False

        try:
            # Acquire attacker lock
            indiv_lock = self.mutex_matrix[indiv_pos[0]][indiv_pos[1]]
            if not indiv_lock.acquire(blocking = False):
                return False
            indiv_locked = True

            # Checking if same individual in matrix
            if not self.matrix[indiv_pos[0]][indiv_pos[1]] is indiv:
                raise ValueError(f"Updated checking individual {indiv.get_id()} error")

            # Acquire adyacents locks
            for pos in targets_pos:
                lock = self.mutex_matrix[pos[0]][pos[1]]
                if lock.acquire(blocking = False):
                    acquired_locks.append(lock)
                    adquired_pos.append(pos)

            # Get adyacent targets
            for pos in adquired_pos:
                aux_target = self.matrix[pos[0]][pos[1]]
                if aux_target:
                    ady_indivs.append(aux_target)

            # Select target
            target = indiv._select_target(ady_indivs)

            if not target or not target.is_individual_alive():
                return False
            
            target_pos = target.get_pos()
            acquired_locks.remove(self.mutex_matrix[target_pos[0]][target_pos[1]])
            target_found = True

            return target

        finally:
            # Release locks except indiv and target
            for lock in acquired_locks:
                lock.release()

            if not target_found and indiv_locked:
                indiv_lock.release()

    def move_individual_random(self, indiv: Individual):

        next_pos_list = []
        acquired_pos = []
        acquired_locks = []    

        old_pos = indiv.get_pos()
        
        try:
            # Get adyacents pos
            next_pos_list = self._get_adyacents_positions(old_pos)

            lock = self.mutex_matrix[old_pos[0]][old_pos[1]]

            # Cheking if indiv is being a target
            if not lock.acquire(blocking = False):
                return False

            acquired_locks.append(lock)
            
            # Acquire all adyacents locks
            for pos in next_pos_list:
                lock = self.mutex_matrix[pos[0]][pos[1]]
                if lock.acquire(blocking = False):
                    acquired_locks.append(lock)
                    acquired_pos.append(pos)

            if not acquired_pos:
                return False

            if not indiv.is_individual_alive():
                return False

            # Check individual is same in matrix
            if self.matrix[old_pos[0]][old_pos[1]] is not indiv:
                raise ValueError(f"Updated checking individual {indiv.get_id()} error")

            new_pos = random.choice(acquired_pos)
            while(self.is_taken(new_pos)):
                acquired_pos.remove(new_pos)
                if len(acquired_pos) == 0:
                    return False
                new_pos = random.choice(acquired_pos)

            if not self._update_individual_pos_locked(indiv, new_pos):
                raise ValueError(f"Updated individual pos {indiv.get_id()} error")
                
            return True

        finally:
            # Release all adyacents blocks
            for lock in acquired_locks:
                lock.release()

    def move_individual_locked(self, indiv: Individual, new_pos):

        # Both positions are suposed to be locked previously
        old_pos = indiv.get_pos()

        if not self.mutex_matrix[old_pos[0]][old_pos[1]].locked():
            raise ValueError(f"Old individual {indiv.get_id()} not locked")
            
        if not self.mutex_matrix[new_pos[0]][new_pos[1]].locked():
            raise ValueError(f"New individual {indiv.get_id()} not locked")

        # Checking if same individual in matrix
        if not self.matrix[old_pos[0]][old_pos[1]] is indiv:
            raise ValueError(f"Updated checking individual {indiv.get_id()} error")
        
        return self._update_individual_pos_locked(indiv, new_pos)

    def remove_individual_locked(self, indiv):
        pos = indiv.get_pos()
        # Pos suposed to be previously locked

        if not self.mutex_matrix[pos[0]][pos[1]].locked():
            raise ValueError(f"Removed individual {indiv.get_id()} not locked")

        # Check individual to remove is same in matrix
        if self.matrix[pos[0]][pos[1]] is not indiv:
            raise ValueError(f"Updated individual {indiv.get_id()} error")

        self.matrix[pos[0]][pos[1]] = None

    def get_random_empty_pos(self):

        while True:
            row = random.randrange(self.size)
            col = random.randrange(self.size)

            if not self.is_taken((row, col)):
                return (row, col)

    def get_random_ady_pos(self, gen_pos):
        # For alien eggs

        new_pos_list = []
        acquired_pos = []
        acquired_locks = []    
        
        try:
            # Get adyacents pos
            new_pos_list = self._get_adyacents_positions(gen_pos)
            
            # Acquire all adyacents locks
            for pos in new_pos_list:
                lock = self.mutex_matrix[pos[0]][pos[1]]
                if lock.acquire(blocking = False):
                    acquired_locks.append(lock)
                    acquired_pos.append(pos)

            if not acquired_pos:
                return None

            new_pos = random.choice(acquired_pos)
            while(self.is_taken(new_pos)):
                acquired_pos.remove(new_pos)
                if len(acquired_pos) == 0:
                    return None
                new_pos = random.choice(acquired_pos)

            # Keep lock for generate new alien
            acquired_locks.remove(self.get_mutex_matrix[new_pos[0]][new_pos[1]])

            return new_pos

        finally:
            # Release all adyacents blocks
            for lock in acquired_locks:
                lock.release()


    def lock_positions(self, list_pos):
        for pos in list_pos:
            self.mutex_matrix[pos[0]][pos[1]].acquire()

    def unlock_positions(self, list_pos):
        for pos in list_pos:
            self.mutex_matrix[pos[0]][pos[1]].release()

    def is_locked(self, pos):
        return self.mutex_matrix[pos[0]][pos[1]].locked()

    def print_matrix(self):

        GREEN = "\033[92m"
        DARK_GREEN = "\033[38;5;22m"
        YELLOW = "\033[93m"
        BLUE = "\033[94m"
        RESET = "\033[0m"

        adquired_locks = []

        # Create a copy of matrix to minimize time of getting acquire all the matrix
        try:
            # Acquire matrix
            for lock_list in self.mutex_matrix:
                for lock in lock_list:
                    lock.acquire()
                    adquired_locks.append(lock)

            matrix_copy = [row.copy() for row in self.matrix]

        finally:
            # Release matrix
            for lock in adquired_locks:
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

    def _update_individual_pos_locked(self, indiv: Individual, new_pos):
        # Both positions are suposed to be locked previously
        old_pos = indiv.get_pos()

        if not self.mutex_matrix[old_pos[0]][old_pos[1]].locked():
            return False
        
        if not self.mutex_matrix[new_pos[0]][new_pos[1]].locked():
            return False

        # Check individual is same in matrix
        if self.matrix[old_pos[0]][old_pos[1]] is not indiv:
            raise ValueError(f"Updated checking individual {indiv.get_id()} error")

        # Check new position is None
        if self.matrix[new_pos[0]][new_pos[1]] is not None:
            raise ValueError(f"Checking new pos for individual {indiv.get_id()} error")
        
        self.matrix[old_pos[0]][old_pos[1]] = None
        self.matrix[new_pos[0]][new_pos[1]] = indiv
        indiv.update_pos(new_pos)
        return True
                
    def _get_adyacents_positions(self, pos):
        ady_pos = []
        for aux_row in range(-1,2):
                        for aux_col in range(-1,2):
                            if not (aux_row == 0 and aux_col == 0):
                                aux_pos = (pos[0] + aux_row, pos[1] + aux_col)
                                if (aux_pos[0] in range(0, self.get_size())) and (aux_pos[1] in range(0, self.get_size())):
                                    ady_pos.append(aux_pos)
        return ady_pos