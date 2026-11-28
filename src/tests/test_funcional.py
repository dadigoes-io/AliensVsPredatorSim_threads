import unittest
from unittest.mock import patch

from simulation import Simulation
from environment import Environment
from individuals import AlienQueen, AlienSoldier, Predator, Human
from individuals.individual_type import IndividualType
from query_type import QueryType

class TestSimulation(unittest.TestCase):

    def setUp(self):
    
        self.enviroment = Environment(5)

        config = {
            "init_num_predators": 1,
            "alien_predator_ratio": 2,
            "hatching_egg_time": 30,
            "alien_sleep_time": 1,
            "predator_sleep_time": 2,
            "human_sleep_time": 3
        }

        self.simulation = Simulation(self.enviroment, config)

    def test_predator_attacks_alien_queen_over_alien_soldier(self):

        # Individuals
        alien_soldier = AlienSoldier("A01", (1,0), self.simulation)
        predator = Predator("P00", (1,1), self.simulation)
        alien_queen = AlienQueen("AQ00", (1,2), self.simulation)


        # Add individuals to simulation
        self.simulation.aliens["A01"] = alien_soldier
        self.simulation.predators["P00"] = predator
        self.simulation.aliens["AQ00"] = alien_queen

        # Check add individuals to enviroment
        self.assertTrue(self.enviroment.add_individual(alien_soldier, locked=False))
        self.assertTrue(self.enviroment.add_individual(predator, locked=False))
        self.assertTrue(self.enviroment.add_individual(alien_queen, locked=False))

        # Attack
        result = predator._attack()

        # Check results
        self.assertTrue(result)

        self.assertEqual(alien_soldier.get_resistance(), 5)
        self.assertEqual(predator.get_resistance(), 19)
        self.assertEqual(alien_queen.get_resistance(), 95)

        self.assertTrue(alien_soldier.is_individual_alive())
        self.assertTrue(predator.is_individual_alive())
        self.assertTrue(alien_queen.is_individual_alive())

        # Check query
        query_type, data = self.simulation.queue.get()

        self.assertEqual(query_type, QueryType.ATTACK)
        self.assertEqual(data, ("P00", "AQ00", (1,2)))

    def test_predator_moves(self):

        # Individuals
        predator = Predator("P00", (2,2), self.simulation)

        # Add individual to simulation
        self.simulation.predators["P00"] = predator

        # Check ad individual to enviroment
        self.assertTrue(self.enviroment.add_individual(predator, locked=False))
    
        # Move
        old_pos = predator.get_pos()
        predator._move()
        new_pos = predator.get_pos()

        # Check results
        self.assertNotEqual(new_pos, old_pos)

        self.assertLessEqual(abs(new_pos[0] - old_pos[0]), 1)
        self.assertLessEqual(abs(new_pos[1] - old_pos[1]), 1)

        self.assertIsNone(self.enviroment.get_matrix()[old_pos[0]][old_pos[1]])
        self.assertIs(self.enviroment.get_matrix()[new_pos[0]][new_pos[1]], predator)
       
    def test_predator_kills_alien_soldier(self):

        # Individuals
        predator = Predator("P00", (2, 2), self.simulation)
        alien_soldier = AlienSoldier("A00", (2, 3), self.simulation)

        # Add individuals to simulation
        self.simulation.predators["P00"] = predator
        self.simulation.aliens["A00"] = alien_soldier

        # Add individuals to environment
        self.assertTrue(self.enviroment.add_individual(predator, locked=False))
        self.assertTrue(self.enviroment.add_individual(alien_soldier, locked=False))

        # Attack
        result = predator._attack()

        # Check death
        self.assertTrue(result)
        self.assertFalse(alien_soldier.is_individual_alive())
        self.assertEqual(alien_soldier.get_resistance(), 0)

        # Check predator movement
        self.assertEqual(predator.get_pos(), (2, 3))
        self.assertIsNone(self.enviroment.get_matrix()[2][2])
        self.assertIs(self.enviroment.get_matrix()[2][3], predator)

        # Check death query
        query_type, data = self.simulation.queue.get()

        self.assertEqual(query_type, QueryType.DEATH)
        self.assertEqual(data, ("P00", "A00", (2, 3), IndividualType.ALIEN_SOLDIER, False))

        # Process death query
        self.simulation.add_query(query_type, data)
        self.simulation.queue_queries()

        self.assertNotIn("A00", self.simulation.aliens)

    def test_alien_queen_death_clears_pending_eggs(self):

        # Individual
        queen = AlienQueen("AQ00", (2, 2), self.simulation)

        # Add individual to simulation
        self.simulation.aliens["AQ00"] = queen
        self.simulation.queen_id = "AQ00"
        self.simulation.alien_eggs = 3

        # Add individual to environment
        self.assertTrue(self.enviroment.add_individual(queen, locked=False))

        # Kill queen
        queen._receive_damage(queen.get_resistance())

        queen_pos = queen.get_pos()
        lock = self.enviroment.get_mutex_matrix()[queen_pos[0]][queen_pos[1]]

        self.assertTrue(lock.acquire(blocking=False))

        try:
            self.enviroment.remove_individual_locked(queen)
        finally:
            lock.release()

        # Send death query
        self.simulation.add_query(
            QueryType.DEATH,
            ("P00", "AQ00", queen_pos, IndividualType.ALIEN_QUEEN, False)
        )

        # Process death query
        self.simulation.queue_queries()

        # Check results
        self.assertNotIn("AQ00", self.simulation.aliens)
        self.assertEqual(self.simulation.alien_eggs, 0)

    def test_human_respawns_immediately_after_death(self):

        # Individuals
        predator = Predator("P00", (2, 2), self.simulation)
        human = Human("H00", (2, 3), self.simulation)

        # Add individuals to simulation
        self.simulation.predators["P00"] = predator
        self.simulation.humans["H00"] = human

        # Update ID counter
        self.simulation.next_human = 1

        # Add individuals to environment
        self.assertTrue(self.enviroment.add_individual(predator, locked=False))
        self.assertTrue(self.enviroment.add_individual(human, locked=False))

        # Attack
        result = predator._attack()

        self.assertTrue(result)
        self.assertFalse(human.is_individual_alive())

        # Prevent new thread from executing
        self.simulation.game_over = True

        # Process death query
        self.simulation.queue_queries()

        # Check human regeneration
        self.assertNotIn("H00", self.simulation.humans)
        self.assertEqual(len(self.simulation.humans), 1)

        self.assertIn("H01", self.simulation.humans)
        new_human = self.simulation.humans["H01"]

        new_human.join()

        self.assertIsInstance(new_human, Human)
        self.assertFalse(new_human.is_alive())

        # Check environment
        new_pos = new_human.get_pos()

        self.assertIs(
            self.enviroment.get_matrix()[new_pos[0]][new_pos[1]],
            new_human
        )

    def test_predator_respawns_after_five_seconds(self):

        # Individuals
        queen = AlienQueen("AQ00", (2, 2), self.simulation)
        predator = Predator("P00", (2, 3), self.simulation)
        surviving_predator = Predator("P01", (0, 0), self.simulation)   # To avoid game over

        # Add individuals to simulation
        self.simulation.aliens["AQ00"] = queen
        self.simulation.predators["P00"] = predator
        self.simulation.predators["P01"] = surviving_predator

        self.simulation.queen_id = "AQ00"
        self.simulation.next_predator = 2

        # Add individuals to environment
        self.assertTrue(self.enviroment.add_individual(queen, locked=False))
        self.assertTrue(self.enviroment.add_individual(predator, locked=False))
        self.assertTrue(self.enviroment.add_individual(surviving_predator, locked=False))

        # Queen kills predator
        queen._attack()
        queen._attack()

        self.assertFalse(predator.is_individual_alive())

        # Process death query
        self.simulation.queue_queries()

        self.assertNotIn("P00", self.simulation.predators)
        self.assertIn("P01", self.simulation.predators)
        self.assertEqual(len(self.simulation.predator_gen_buffer), 1)

        # Get death predator timer
        death_predator_timer = self.simulation.predator_gen_buffer[0]

        # Prevent new thread from executing
        self.simulation.game_over = True

        # Mocking time.monotonic from simulation to be under five seconds
        with patch("simulation.time.monotonic", return_value=death_predator_timer):
            self.simulation._respawn_predators()

        # Check before five seconds
        self.assertEqual(len(self.simulation.predators), 1)
        self.assertEqual(len(self.simulation.predator_gen_buffer), 1)

        # Mocking time.monotonic from simulation to wait five seconds and respawn predator
        with patch("simulation.time.monotonic", return_value=death_predator_timer + 5.1):
            self.simulation._respawn_predators()

        # Check after five seconds
        self.assertEqual(len(self.simulation.predators), 2)
        self.assertEqual(len(self.simulation.predator_gen_buffer), 0)

        # Check new predator
        self.assertIn("P02", self.simulation.predators)
        new_predator = self.simulation.predators["P02"]

        new_predator.join()

        self.assertIsInstance(new_predator, Predator)
        self.assertFalse(new_predator.is_alive())

        new_pos = new_predator.get_pos()

        self.assertIs(self.enviroment.get_matrix()[new_pos[0]][new_pos[1]], new_predator)

    def test_alien_queen_hatches_egg(self):

        # Individual
        queen = AlienQueen("AQ00", (2, 2), self.simulation)

        # Add individual to simulation
        self.simulation.aliens["AQ00"] = queen
        self.simulation.queen_id = "AQ00"
        self.simulation.next_alien = 1

        # Add individual to environment
        self.assertTrue(self.enviroment.add_individual(queen, locked=False))

        # Prevent new thread from executing
        self.simulation.game_over = True

        # Mocking time.monotonic from simulation to wait thirty seconds and hatch and egg
        with patch("individuals.alien.time.monotonic", return_value=queen.egg_timer + 30.1):
            queen._incubate_eggs()

        # Check query
        query_type, data = self.simulation.queue.get()

        self.assertEqual(query_type, QueryType.HATCH_EGG)

        # Process query
        self.simulation.add_query(query_type, data)
        self.simulation.queue_queries()

        self.assertEqual(self.simulation.alien_eggs, 1)

        # Hatch egg
        self.simulation._hatch_alien_egg()

        self.assertEqual(self.simulation.alien_eggs, 0)

        # Check new alien
        self.assertIn("A01", self.simulation.aliens)
        new_alien = self.simulation.aliens["A01"]

        new_alien.join()

        self.assertIsInstance(new_alien, AlienSoldier)
        self.assertIsNotNone(new_alien.ident)
        self.assertFalse(new_alien.is_alive())

        # Check position
        new_pos = new_alien.get_pos()

        self.assertLessEqual(abs(new_pos[0] - 2), 1)
        self.assertLessEqual(abs(new_pos[1] - 2), 1)
        self.assertNotEqual(new_pos, (2, 2))

        self.assertIs(self.enviroment.get_matrix()[new_pos[0]][new_pos[1]], new_alien)

    def test_locks_are_released_after_attack_and_movement(self):                                                                                

        # Individuals
        predator = Predator("P00", (2, 2), self.simulation)
        queen = AlienQueen("AQ00", (2, 3), self.simulation)

        # Add individuals to simulation
        self.simulation.predators["P00"] = predator
        self.simulation.aliens["AQ00"] = queen

        # Add individuals to environment
        self.assertTrue(self.enviroment.add_individual(predator, locked=False))
        self.assertTrue(self.enviroment.add_individual(queen, locked=False))

        # Lock target (queen) position manually
        target_lock = self.enviroment.get_mutex_matrix()[2][3]

        self.assertTrue(target_lock.acquire(blocking=False))

        try:
            # Attack should fail because target position is locked
            self.assertFalse(predator._attack())

            self.assertFalse(self.enviroment.is_locked((2, 2)))
            self.assertTrue(self.enviroment.is_locked((2, 3)))

        finally:
            target_lock.release()

        # Attack after releasing target lock
        self.assertTrue(predator._attack())

        # Check all locks are released
        for row in self.enviroment.get_mutex_matrix():
            for lock in row:
                self.assertFalse(lock.locked())

        # Move
        predator._move()

        # Check all locks are released
        for row in self.enviroment.get_mutex_matrix():
            for lock in row:
                self.assertFalse(lock.locked())

    def test_simulation_ends_and_joins_threads(self):

        # Individuals
        predator1 = Predator("P00", (0, 0), self.simulation)
        predator2 = Predator("P01", (4, 4), self.simulation)
        human1 = Human("H00", (0, 4), self.simulation)
        human2 = Human("H01", (4, 0), self.simulation)

        predator1.sleep_time = 0.01
        predator2.sleep_time = 0.01
        human1.sleep_time = 0.01
        human2.sleep_time = 0.01

        # Add individuals to simulation
        self.simulation.predators["P00"] = predator1
        self.simulation.predators["P01"] = predator2
        self.simulation.humans["H00"] = human1
        self.simulation.humans["H01"] = human2

        # Add individuals to environment
        self.assertTrue(self.enviroment.add_individual(predator1, locked=False))
        self.assertTrue(self.enviroment.add_individual(predator2, locked=False))
        self.assertTrue(self.enviroment.add_individual(human1, locked=False))
        self.assertTrue(self.enviroment.add_individual(human2, locked=False))

        # Mock to avoid prints during test
        with patch("builtins.print"):
            with patch("simulation.os.system"):
                self.simulation.run()

        # Check simulation end (because no aliens alive)
        self.assertTrue(self.simulation.get_game_over())

        # Check threads termination (individual and in thread list in simulation)
        self.assertFalse(predator1.is_alive())
        self.assertFalse(predator2.is_alive())
        self.assertFalse(human1.is_alive())
        self.assertFalse(human2.is_alive())

        for thread in self.simulation.threads:
            self.assertFalse(thread.is_alive())

if __name__ == "__main__":
    unittest.main()