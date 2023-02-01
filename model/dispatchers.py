import logging
from typing import List

from model.event import Event
from model.bid import Bid
from model.buffer import Buffer
from model.units import ProcessingUnit
from model.step_record import StepRecorder
from model.timer import Timer


class ProcessingDispatcher:

    def __init__(self, processing_units: List[ProcessingUnit], buffer: Buffer) -> None:

        self.timer = Timer()

        self.processing_units = processing_units
        self.buffer = buffer

    def _has_free_unit(self) -> bool:
        for unit in self.processing_units:
            if unit.is_free():
                return True

        return False

    def _buffer(self, bid: Bid) -> None:
        refused_bid = self.buffer.put(bid)

        if refused_bid:
            refused_bid.is_refused = True

        StepRecorder.pushed_bid = bid
        StepRecorder.refused_bid = refused_bid

        logging.debug(f"Buffering {bid}")
        logging.debug(f"Refused {refused_bid}")


    def _process(self, bid: Bid) -> Event:

        bid.selection_time = self.timer.get_current_time()

        for unit in self.processing_units:
            if unit.is_free():
                event = unit.process(bid)
                return event

    def process(self, bid: Bid) -> Event | None:

        if not self._has_free_unit():
            self._buffer(bid)
            return

        event = self._process(bid)
        return event


class SelectingDispatcher:

    def __init__(self, processing_units: List[ProcessingUnit], buffer: Buffer) -> None:

        self.timer: Timer = Timer()

        self.processing_units: List[ProcessingUnit] = processing_units
        self.buffer: Buffer = buffer

    def _get_new_bid(self) -> Bid:

        new_bid = self.buffer.get()

        return new_bid

    def _process(self, bid: Bid) -> Event:

        bid.selection_time = self.timer.get_current_time()

        for unit in self.processing_units:
            if unit.is_free():
                event = unit.process(bid)
                return event

    def select(self) -> Event:
        event = None

        bid = self._get_new_bid()
        if bid:
            event = self._process(bid)

        StepRecorder.poped_bid = bid

        logging.debug(f"select: {bid}")

        return event
