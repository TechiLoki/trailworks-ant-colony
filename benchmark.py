"""Reproducible model benchmark; outputs measured results as JSON."""
import argparse
import json
import time
from simulation import Colony

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps', type=int, default=3000)
    parser.add_argument('--population', type=int, default=150)
    parser.add_argument('--seed', type=int, default=7)
    args = parser.parse_args()
    if args.steps < 1: parser.error('steps must be positive')
    colony = Colony(seed=args.seed, population=args.population)
    start = time.perf_counter()
    colony.step(args.steps)
    seconds = time.perf_counter() - start
    remaining = sum(colony.food.values())
    carrying = sum(a.carrying for a in colony.ants)
    print(json.dumps(dict(seed=args.seed, population=args.population, steps=args.steps,
                         seconds=round(seconds,3), steps_per_second=round(args.steps/seconds,2),
                         delivered=colony.delivered, remaining=remaining, carrying=carrying,
                         food_conserved=colony.initial_food == remaining+carrying+colony.delivered), indent=2))
