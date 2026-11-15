import threading
import random
from individuals import *

class Environment():

    def __init__(self, size):
        self.size = size
        self.matrix = [[None for _ in range(size)] for _ in range(size)]
        self.mutex_matrix = [[threading.Lock() for _ in range(size)] for _ in range(size)]

    def is_taken(self, row, column):
        return self.matrix[row][column] is not None


    # Hacer atomico get_random_empty_pos y add_individual
    def add_individual(self, ind):
        pos = ind.pos

        if self.is_taken(pos[0], pos[1]):
            return False

        self.matrix[pos[0]][pos[1]] = ind
        return True

    def get_random_empty_pos(self):

        while True:
            row = random.randrange(self.size)
            col = random.randrange(self.size)

            if not self.is_taken(row, col):
                return (row, col)

    def print_matrix(self):

        GREEN = "\033[92m"
        DARK_GREEN = "\033[38;5;22m"
        YELLOW = "\033[93m"
        BLUE = "\033[94m"
        RESET = "\033[0m"

        for row_list in self.matrix:
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