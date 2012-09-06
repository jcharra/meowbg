
import random

class Dice(object):
    def roll(self):
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        if d1 == d2:
            return [d1] * 4
        else:
            return [d1, d2]

    def rollout(self):
        while True:
            d1, d2 = random.randint(1, 6), random.randint(1, 6)
            if d1 != d2:
                return d1, d2