import math
import random


class UniformGenerator:

  frequency: float

  def __init__(self, alpha: float, beta: float) -> None:
    """TODO"""

    if alpha > beta:
      raise ValueError

    self.alpha = alpha
    self.beta = beta

  def __call__(self) -> float:
    """TODO"""

    r = random.random()
    return r * (self.beta - self.alpha) + self.alpha


class ExponentialGenerator:

  frequency: float

  def __init__(self, frequency: float) -> None:
    """TODO"""

    if frequency <= 0:
      raise ValueError

    self.frequency = frequency

  def __call__(self) -> float:
    """TODO"""

    r = random.random()
    return (-1 / self.frequency) * math.log(1 - r)
     