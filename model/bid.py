from dataclasses import dataclass

@dataclass
class Bid:

    id: int
    generating_unit_id: int = 0
    generation_time: float = 0

    processing_unit_id: int = 0
    processing_time: float = 0

    selection_time: float = 0
    is_refused: bool = False

    def __str__(self) -> str:

        format_string = "[id: {}, source: {}, gen. time: {:.2f}, device: {}, proc. time: {:.2f}, refused: {}]"

        return format_string.format(self.id, self.generating_unit_id, self.generation_time,
                                    self.processing_unit_id, self.processing_time,
                                    self.is_refused
)
