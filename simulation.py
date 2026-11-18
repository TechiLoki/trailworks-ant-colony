"""Seeded, grid-based foraging simulation with separate outbound/home trails."""
from dataclasses import dataclass
import math
import random


@dataclass
class Ant:
    x: int
    y: int
    heading: int
    carrying: bool = False
    age: int = 0


class Colony:
    DIRECTIONS = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))

    def __init__(self, seed=7, population=150, evaporation=0.025):
        if not 1 <= population <= 500:
            raise ValueError('population must be between 1 and 500')
        if not 0.001 <= evaporation <= 0.2:
            raise ValueError('evaporation must be between 0.001 and 0.2')
        self.width, self.height = 96, 64
        self.seed, self.evaporation = seed, evaporation
        self.random = random.Random(seed)
        self.nest = (14, 32)
        self.tick = self.delivered = self.initial_food = 0
        self.food = {}
        self.walls = set()
        self.home = [0.0] * (self.width * self.height)
        self.trail = [0.0] * (self.width * self.height)
        # A barrier with two passages makes route selection visible.
        for y in range(8, 57):
            if not 25 <= y <= 36:
                self.walls.add((48, y))
        self.add_food(78, 20, 400)
        self.add_food(75, 47, 400)
        self.ants = [Ant(*self.nest, self.random.randrange(8)) for _ in range(population)]

    def index(self, x, y):
        return y * self.width + x

    def valid(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height and (x, y) not in self.walls

    def add_food(self, x, y, amount=200):
        if not self.valid(x, y) or math.dist((x, y), self.nest) <= 3:
            raise ValueError('food must be on an open cell away from the nest')
        if not 1 <= amount <= 10000:
            raise ValueError('food amount must be between 1 and 10000')
        self.food[x, y] = self.food.get((x, y), 0) + amount
        self.initial_food += amount

    def step(self, steps=1):
        for _ in range(steps):
            self.tick += 1
            decay = 1 - self.evaporation
            for field in (self.home, self.trail):
                for i, value in enumerate(field):
                    field[i] = value * decay if value > 0.01 else 0.0
            for ant in self.ants:
                self._move(ant)

    def _move(self, ant):
        ant.age += 1
        position = ant.x, ant.y
        if not ant.carrying and self.food.get(position, 0):
            self.food[position] -= 1
            ant.carrying = True
            ant.age = 0
            ant.heading = (ant.heading + 4) % 8
        elif ant.carrying and math.dist(position, self.nest) <= 2:
            ant.carrying = False
            self.delivered += 1
            ant.age = 0
            ant.heading = (ant.heading + 4) % 8
        # Trail strength fades with distance/time since visiting its source.
        deposited = self.trail if ant.carrying else self.home
        i = self.index(*position)
        deposited[i] = min(100.0, deposited[i] + 12.0 / (1 + ant.age * 0.03))
        followed = self.home if ant.carrying else self.trail
        candidates, weights = [], []
        for direction, (dx, dy) in enumerate(self.DIRECTIONS):
            x, y = ant.x + dx, ant.y + dy
            if not self.valid(x, y):
                continue
            # Do not cut diagonally through obstacle corners.
            if dx and dy and (not self.valid(ant.x + dx, ant.y) or not self.valid(ant.x, ant.y + dy)):
                continue
            turn = min((direction-ant.heading) % 8, (ant.heading-direction) % 8)
            persistence = (3.0, 1.7, 0.8, 0.35, 0.2)[turn]
            attraction = 1.0 + followed[self.index(x, y)] * 2
            if ant.carrying:
                # Local nest sensing only; distant navigation uses home trails.
                if math.dist((x, y), self.nest) < 10:
                    attraction += 40 / (1 + math.dist((x, y), self.nest))
            else:
                for (fx, fy), amount in self.food.items():
                    distance = math.dist((x, y), (fx, fy))
                    if amount and distance < 9:
                        attraction += 90 / (1 + distance) ** 2
            candidates.append((x, y, direction))
            weights.append(persistence * attraction)
        if candidates:
            # Exploration prevents complete lock-in to an early route.
            if self.random.random() < 0.08:
                ant.x, ant.y, ant.heading = self.random.choice(candidates)
            else:
                ant.x, ant.y, ant.heading = self.random.choices(candidates, weights)[0]

    def snapshot(self):
        return dict(width=self.width, height=self.height, tick=self.tick,
                    delivered=self.delivered, remaining=sum(self.food.values()),
                    carrying=sum(a.carrying for a in self.ants), initial_food=self.initial_food,
                    nest=self.nest, walls=sorted(self.walls),
                    food=[[x, y, n] for (x, y), n in self.food.items() if n],
                    ants=[[a.x, a.y, a.carrying] for a in self.ants],
                    home=[round(v, 2) for v in self.home],
                    trail=[round(v, 2) for v in self.trail])
