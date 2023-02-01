import logging

from model.event import Event, EventTag
from model.bid import Bid
from model.marker import Marker
from model.timer import Timer
from utils.random import ExponentialGenerator, UniformGenerator


class GeneratingUnit:
    """TODO"""

    def __init__(self, unit_id: int, generation_freq: float) -> None:

        if generation_freq <= 0:
            raise ValueError("generation frequency must be positive")

        self.timer = Timer()
        self.generator = ExponentialGenerator(generation_freq)

        self.unit_id = unit_id

    def generate(self) -> Event:

        current_time = self.timer.get_current_time()
        time = current_time + self.generator()

        bid = Bid(id=Marker().get_id(), generating_unit_id=self.unit_id, generation_time=time)

        event = Event(time, tag=EventTag.GENERATE, data=bid)

        logging.debug(f"{current_time:.2f}: unit {self.unit_id} generating {event}")

        return event


class ProcessingUnit:
    """TODO"""

    def __init__(self, unit_id: int, min_proc_time: float, max_proc_time: float) -> None:

        if min_proc_time > max_proc_time:
            raise ValueError("min. processing time must be less than max. processing time")


        self.timer = Timer()
        self.generator = UniformGenerator(min_proc_time, max_proc_time)

        self.unit_id = unit_id
        self.free = True

    def is_free(self) -> bool:
        return self.free

    def make_free(self) -> None:
        self.free = True

    def process(self, bid: Bid) -> Event:

        current_time = self.timer.get_current_time()
        time = current_time + self.generator()

        bid.processing_unit_id = self.unit_id
        bid.processing_time = time

        event = Event(time=time, tag=EventTag.PROCESS, data=bid)

        self.free = False

        logging.debug(f"{current_time:.2f}: unit {self.unit_id} generating {event}")

        return event
