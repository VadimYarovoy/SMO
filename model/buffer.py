import copy
from typing import List
from model.bid import Bid


class Buffer:

    def __init__(self, capacity: int) -> None:
        super().__init__()

        self.data: List[Bid] = [None] * capacity
        self.capacity = capacity
        self.pointer = 0

    def put(self, new_bid: Bid) -> Bid | None:
        refused_bid = None

        if self.is_full():
            list_id = None
            time = None

            for id, bid in enumerate(self.data):
                bid_time = bid.generation_time

                if time:
                    if bid_time > time:
                        time = bid_time
                        list_id = id
                else:
                    time = bid_time
                    list_id = id

            refused_bid = copy.deepcopy(self.data[list_id])
            self.data[list_id] = None

        i = self.pointer

        while True:
            bid = self.data[i]

            if bid == None:
                self.data[i] = new_bid
                self.pointer = (i + 1) % self.capacity
                break

            i += 1
            i %= self.capacity

        return refused_bid

    def get(self) -> Bid | None:

        bid = None

        list_id = None
        unit_id = None

        for id, bid in enumerate(self.data):
            if bid:
                bid_unit_id = bid.generating_unit_id

                if unit_id:
                    if bid_unit_id < unit_id:
                        unit_id = bid_unit_id
                        list_id = id
                else:
                    unit_id = bid_unit_id
                    list_id = id

        if list_id != None:
            bid = copy.deepcopy(self.data[list_id])
            self.data[list_id] = None

        return bid

    def is_full(self):
        for bid in self.data:
            if bid == None:
                return False

        return True

    def __iter__(self):
        return iter(self.data)

    def __next__(self):
        return next(self.data)

    def make_empty(self):
        self.data = [None] * self.capacity

