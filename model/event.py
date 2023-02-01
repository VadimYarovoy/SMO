from dataclasses import dataclass
from enum import Enum, auto

from model.bid import Bid

class EventTag(Enum):
  """TODO"""

  START = auto()
  GENERATE = auto()
  PROCESS = auto()
  END = auto()

@dataclass
class Event:
  """TODO"""

  time: float
  tag: EventTag
  data: Bid | None = None

  def __str__(self) -> str:
    return "Event[{:.2f}, {:s}, {}]".format(self.time, str(self.tag.name), self.data)
