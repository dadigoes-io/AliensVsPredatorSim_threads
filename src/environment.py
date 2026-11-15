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
        for row_list in self.matrix:
            str_out = ""
            for box in row_list:
                if box is None:
                    str_out += "□ "
                else:
                    str_out += f"{box.get_id()[0]} "

            print(str_out)