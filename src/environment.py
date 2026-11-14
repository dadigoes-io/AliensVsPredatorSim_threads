from individuals import *

class Environment():

    def __init__(self, size):
        self.size = size
        self.matrix = [[] for _ in range(size)]

