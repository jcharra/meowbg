
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

class FakeDice(object):
    def set_next_dice(self, d1, d2):
        self.d1, self.d2 = d1, d2

    def roll(self):
        if self.d1 == self.d2:
            return [self.d1, self.d1, self.d1, self.d1]
        else:
            return [self.d1, self.d2]