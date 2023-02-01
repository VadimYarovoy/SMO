from model.bid import Bid


class StepRecorder:
    current_time: float
    event_type: str
    current_bid: Bid
    pushed_bid: Bid
    poped_bid: Bid
    refused_bid: Bid
