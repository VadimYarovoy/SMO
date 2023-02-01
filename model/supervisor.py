from dataclasses import dataclass
import logging
import math
from typing import Iterable, List, Tuple
from model.auto_mode import StatsRecord


from model.event import Event, EventTag
from model.bid import Bid
from model.buffer import Buffer
from model.dispatchers import ProcessingDispatcher, SelectingDispatcher
from model.units import GeneratingUnit, ProcessingUnit
from model.step_record import StepRecorder
from model.timer import Timer


class Supervisor:

    def __init__(self,
                 num_sources: int,
                 num_devices: int,
                 buffer_capacity: int,
                 generation_freq: float,
                 min_proc_time: float,
                 max_proc_time: float,
                 num_total_bids: int) -> None:

        self.events: List[Event] = []
        self.timer: Timer = Timer()

        self.num_generating_units = num_sources
        self.num_processing_units = num_devices

        self.num_total_bids = num_total_bids
        self.current_num_bids = 0

        self.generating_units = [GeneratingUnit(i + 1, generation_freq) for i in range(num_sources)]
        self.processing_units = [ProcessingUnit(i + 1, min_proc_time, max_proc_time) for i in range(num_devices)]

        self.memory_buffer = Buffer(buffer_capacity)

        self.processing_dispatcher = ProcessingDispatcher(self.processing_units, self.memory_buffer)
        self.selecting_dispatcher = SelectingDispatcher(self.processing_units, self.memory_buffer)

    # Steo mode utils
    def _add_new_event(self, event: Event) -> None:
        self.events.append(event)
        self._preserve_order()

    def _add_new_events(self, events: Iterable[Event]) -> None:
        self.events.extend(events)
        self._preserve_order()

    def _get_next_event(self) -> Event:
        return self.events.pop(0)

    def _preserve_order(self) -> None:
        self.events.sort(key=lambda event: event.time)

    # Step mode actions
    def _start_modeling(self) -> None:
        self.timer.current_time = 0
        self.current_num_bids = 0
        self.memory_buffer.make_empty()
        self.events = []
        time = self.timer.get_current_time()
        tag = EventTag.START
        new_event = Event(time, tag)
        self._add_new_event(new_event)

    def _trigger_all_generating_units(self) -> None:
        new_events = []

        for unit in self.generating_units:
            if self.current_num_bids > self.num_total_bids:
                break

            event = unit.generate()
            new_events.append(event)

            self.current_num_bids += 1

        self._add_new_events(new_events)

    def _trigger_generating_unit(self, unit_id: int) -> None:

        for unit in self.generating_units:
            if self.current_num_bids > self.num_total_bids:
                break

            if unit.unit_id == unit_id:
                new_event = unit.generate()

                self.current_num_bids += 1

                self._add_new_event(new_event)
                break

    def _trigger_processing_unit(self, unit_id: int) -> None:
        for unit in self.processing_units:
            if unit.unit_id == unit_id:
                unit.make_free()

    def _trigger_processing_dispatcher(self, bid: Bid) -> None:
        new_event = self.processing_dispatcher.process(bid)

        if new_event:
            self._add_new_event(new_event)

    def _trigger_selecting_dispatcher(self) -> None:
        new_event = self.selecting_dispatcher.select()
        if new_event:
            self._add_new_event(new_event)

    def _update_statistics(self, bid: Bid) -> None:
        current_time = self.timer.get_current_time()
        logging.info(f"{current_time:.2f}: update statistics - {bid}")

    def _end_modeling(self) -> None:
        print("THE END")

    # Step mode
    def start_step_mode(self):
        self._start_modeling()

    def end_step_mode(self):
        time = self.timer.get_current_time()
        tag = EventTag.END
        new_event = Event(time, tag)
        self._add_new_event(new_event)

    def step(self) -> Tuple:
        if not self.events:
            self.end_step_mode()

        current_event = self._get_next_event()

        current_time = current_event.time
        self.timer.set_current_time(current_time)

        current_bid = current_event.data

        StepRecorder.current_time = current_time
        StepRecorder.event_type = current_event.tag.name
        StepRecorder.current_bid = current_bid
        StepRecorder.pushed_bid = None
        StepRecorder.poped_bid = None
        StepRecorder.refused_bid = None

        logging.info(f"{current_time:.2f}: processing {current_event}")
        logging.info(f"{current_time:.2f}: current buffer {[str(bid) for bid in self.memory_buffer]}")

        match current_event.tag:
            case EventTag.START:
                self._trigger_all_generating_units()

            case EventTag.GENERATE:
                self._trigger_generating_unit(current_bid.generating_unit_id)
                self._trigger_processing_dispatcher(current_bid)

            case EventTag.PROCESS:
                self._trigger_processing_unit(current_bid.processing_unit_id)
                self._update_statistics(current_bid)
                self._trigger_selecting_dispatcher()

            case EventTag.END:
                self._end_modeling()

            case _:
                raise ValueError("Supervisor met unknown event tag")

        logging.info(f"END: current = {self.current_num_bids}, total = {self.num_total_bids}")

    def get_event_info(self) -> Tuple:
        return (StepRecorder.current_time,
                StepRecorder.event_type,
                StepRecorder.current_bid)

    def get_buffer_info(self) -> Tuple:
        return (self.memory_buffer,
                StepRecorder.pushed_bid,
                StepRecorder.poped_bid,
                StepRecorder.refused_bid,
                self.memory_buffer.pointer)

    def start_auto_mode(self):

        @dataclass
        class SpecialStatsRecord:
            num_total_bids: int = 0
            num_refused_bids: int = 0

        simulation_total_time = 0

        shared_stats = {i + 1: StatsRecord() for i in range(self.num_generating_units)}
        devices_stats = {i + 1: 0 for i in range(self.num_processing_units)}

        p_prev = 1
        p_next = 1

        N = 100
        # N = 500

        ill_state = False

        cond = 1
        #max_iteration = 200
        max_iteration = 50
        num_iteration = 0
        while cond > 0.1:
            print(f"cond = {cond} n = {N}")
            num_iteration += 1
            special_stats = SpecialStatsRecord()

            if num_iteration > max_iteration:
                ill_state = True
                break

            self.num_total_bids = N
            self.start_step_mode()

            self.step()
            time, event_type, bid = self.get_event_info()
            _, _, _, refused_bid, _ = self.get_buffer_info()

            while event_type != EventTag.END.name:

                if event_type == EventTag.GENERATE.name:
                    unit_id = bid.generating_unit_id
                    special_stats.num_total_bids += 1

                    shared_stats[unit_id].num_total_bids += 1

                if event_type == EventTag.PROCESS.name:
                    unit_id = bid.generating_unit_id

                    shared_stats[unit_id].num_processed_bids += 1

                    waiting_time = bid.selection_time - bid.generation_time
                    shared_stats[unit_id].sum_waiting_time += waiting_time
                    shared_stats[unit_id].sum_sqr_waiting_time += math.pow(waiting_time, 2)

                    processing_time = bid.processing_time - bid.selection_time
                    shared_stats[unit_id].sum_processing_time += processing_time
                    shared_stats[unit_id].sum_sqr_processing_time += math.pow(processing_time, 2)

                    devices_stats[bid.processing_unit_id] += processing_time

                if refused_bid:
                    unit_id = refused_bid.generating_unit_id

                    special_stats.num_refused_bids += 1
                    shared_stats[unit_id].num_refused_bids += 1

                self.step()
                time, event_type, bid = self.get_event_info()
                _, _, _, refused_bid, _ = self.get_buffer_info()

            simulation_total_time += time


            p_next = special_stats.num_refused_bids / special_stats.num_total_bids

            if p_next != 0:
                t_a = 1.643
                d = 0.1
                N = (math.pow(t_a, 2) * (1 - p_next)) / (p_next * math.pow(d, 2))


            cond = math.fabs(p_next - p_prev)

            p_prev = p_next


        if ill_state:
            for record in shared_stats.values():
                record.probability = None

        for unit_id, record in shared_stats.items():

            waiting_mean = None
            waiting_variance = None
            processing_mean = None
            processing_variance = None

            if record.num_processed_bids:
                waiting_mean = record.sum_waiting_time / record.num_processed_bids
                waiting_mean_sqr = record.sum_sqr_waiting_time / record.num_processed_bids
                waiting_variance = waiting_mean_sqr - math.pow(waiting_mean, 2)

                processing_mean = record.sum_processing_time / record.num_processed_bids
                processing_mean_sqr = record.sum_sqr_processing_time / record.num_processed_bids
                processing_variance = processing_mean_sqr - math.pow(processing_mean, 2)

        for unit_id in devices_stats.keys():
            devices_stats[unit_id] /= simulation_total_time

        return (shared_stats, devices_stats)
