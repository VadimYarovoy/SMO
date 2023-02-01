from dataclasses import dataclass

@dataclass
class StatsRecord:
    num_total_bids: int = 0
    num_processed_bids: int = 0
    num_refused_bids: int = 0
    probability: float = 0
    sum_waiting_time: float = 0
    sum_sqr_waiting_time: float = 0
    sum_processing_time: float = 0
    sum_sqr_processing_time: float = 0