import unittest

from environment import Environment
from simulation import Simulation
from individuals import AlienQueen, Predator
from query_type import QueryType

class TestAttack(unittest.TestCase):

    def setUp(self):

        self.enviroment = Environment(3)
        self.simulation = Simulation(self.enviroment)

        # Individuals
        self.alien_queen = AlienQueen("AQ00", (1,2), self.simulation)
        self.predator = Predator("P00", (1,1), self.simulation)


        # Add individuals to simulation
        self.simulation.aliens["AQ00"] = self.alien_queen
        self.simulation.predators["P00"] = self.predator

        # Check add individuals to enviroment
        self.assertTrue(self.enviroment.add_individual(self.alien_queen, locked=False))
        self.assertTrue(self.enviroment.add_individual(self.predator, locked=False))

    def test_predator_attacks_alien_queen(self):

        # Attack
        result = self.predator._attack()

        # Check results
        self.assertTrue(result)
        self.assertEqual(self.alien_queen.get_resistance(), 95)
        self.assertEqual(self.predator.get_resistance(), 19)

        self.assertTrue(self.alien_queen.is_individual_alive())
        self.assertTrue(self.predator.is_individual_alive())

        # Check query
        query_type, data = self.simulation.queue.get()

        self.assertEqual(query_type, QueryType.ATTACK)
        self.assertEqual(data, ("P00", "AQ00", (1,2)))

    if __name__ == "__main__":
        unittest.main()