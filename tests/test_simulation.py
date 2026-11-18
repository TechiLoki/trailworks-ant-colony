import unittest
from simulation import Colony


class SimulationTests(unittest.TestCase):
    def test_seed_reproduces_state(self):
        first, second = Colony(population=12), Colony(population=12)
        first.step(50)
        second.step(50)
        self.assertEqual(first.snapshot(), second.snapshot())

    def test_food_conservation_and_valid_positions(self):
        colony = Colony(population=40)
        colony.step(250)
        self.assertEqual(colony.initial_food, colony.delivered + sum(colony.food.values()) + sum(a.carrying for a in colony.ants))
        self.assertTrue(all(colony.valid(a.x, a.y) for a in colony.ants))

    def test_pickup_and_delivery(self):
        colony = Colony(population=1)
        ant = colony.ants[0]
        ant.x, ant.y = 78, 20
        colony.step()
        self.assertTrue(ant.carrying)
        self.assertEqual(colony.food[78, 20], 399)
        ant.x, ant.y = colony.nest
        colony.step()
        self.assertFalse(ant.carrying)
        self.assertEqual(colony.delivered, 1)

    def test_evaporation(self):
        colony = Colony(population=1, evaporation=.1)
        colony.trail[0] = 10
        colony.step()
        self.assertAlmostEqual(colony.trail[0], 9)

    def test_reject_bad_configuration_and_food(self):
        for kwargs in ({'population':0}, {'population':501}, {'evaporation':0}):
            with self.assertRaises(ValueError): Colony(**kwargs)
        colony = Colony()
        for x, y in [(-1,0),(48,10),colony.nest]:
            with self.assertRaises(ValueError): colony.add_food(x,y)

    def test_food_addition_updates_total(self):
        colony = Colony()
        colony.add_food(30,30,50)
        self.assertEqual(colony.initial_food,850)
        self.assertEqual(colony.food[30,30],50)


if __name__ == '__main__': unittest.main()
