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

    def add_individual(self, ind):
        pos = ind.pos
        
        if self.is_taken(pos[0], pos[1]):
            return False

        self.matrix[pos[0], pos[1]] = ind
        return True

    def get_random_empty_pos(self):

        occupied = False

        while occupied:
            pos = (random.randint(0, self.size), random.randint(0, self.size))
            occupied =  (self.matrix[pos[0]][pos[1]] == None)

        return pos

