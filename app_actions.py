import math
from typing import Dict, Iterable

import concurrent.futures

import multiprocessing
from multiprocessing import Process
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
import os

import dearpygui.dearpygui as dpg
from numpy import int16

import app_tags
from app_tags import *
from app_settings import *
from model.auto_mode import StatsRecord

from model.bid import Bid
from model.supervisor import Supervisor

def _save_settings():

    Settings.num_sources = dpg.get_value(item=SETTINGS_NUM_SOURCES)
    Settings.num_devices = dpg.get_value(item=SETTINGS_NUM_DEVICES)
    Settings.buffer_capacity = dpg.get_value(item=SETTINGS_BUFFER_CAPACITY)
    Settings.generation_freq = dpg.get_value(item=SETTINGS_GENERATION_FREQ)
    Settings.min_processing_time = dpg.get_value(item=SETTINGS_MIN_PROCESSING_TIME)
    Settings.max_processing_time = dpg.get_value(item=SETTINGS_MAX_PROCESSING_TIME)
    Settings.max_bids = dpg.get_value(item=SETTINGS_MAX_BIDS)

    if Settings.min_processing_time > Settings.max_processing_time:
        raise ValueError("Invalid input: min. proc. time > max. proc. time")

def _get_supervisor() -> Supervisor:

    supervisor = Supervisor(num_sources=Settings.num_sources,
                            num_devices=Settings.num_devices,
                            buffer_capacity=Settings.buffer_capacity,
                            generation_freq=Settings.generation_freq,
                            min_proc_time=Settings.min_processing_time,
                            max_proc_time=Settings.max_processing_time,
                            num_total_bids=Settings.max_bids)

    return supervisor


num_events = 0
supervisor = None


def _draw_event_calendar_content_block() -> None:

    global num_events
    num_events = 0

    dpg.delete_item(item=EVENT_CALENDAR_CONTENT_BLOCK, children_only=True)

    with dpg.table(tag=EVENT_CALENDAR, parent=EVENT_CALENDAR_CONTENT_BLOCK,
                   header_row=True, policy=dpg.mvTable_SizingStretchProp,
                   borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True,
                   row_background=True, scrollY=True, no_host_extendX=True):

        dpg.add_table_column(label="time")
        dpg.add_table_column(label="event type")
        dpg.add_table_column(label="src. id")
        dpg.add_table_column(label="gen. time")
        dpg.add_table_column(label="dev. id")
        dpg.add_table_column(label="pr. time")

def _draw_memory_buffer(bids: Iterable[Bid], pushed: Bid, poped: Bid, refused: Bid, pointer: int) -> None:

    dpg.delete_item(item=MEMORY_BUFFER, children_only=True)

    if refused:
        dpg.set_value(item="refused_bid", value="True")
    else:
        dpg.set_value(item="refused_bid", value="False")

    dpg.add_table_column(label="position", parent=MEMORY_BUFFER)
    dpg.add_table_column(label="src. id", parent=MEMORY_BUFFER)
    dpg.add_table_column(label="gen. time", parent=MEMORY_BUFFER)
    dpg.add_table_column(label="p", parent=MEMORY_BUFFER)

    i = 0
    for bid in bids:
        with dpg.table_row(parent=MEMORY_BUFFER):
            dpg.add_text(i + 1)
            if bid:
                dpg.add_text(bid.generating_unit_id)
                dpg.add_text(f"{bid.generation_time:.2f}")
            else:
                dpg.add_text("None")
                dpg.add_text("None")

            if pointer == i:
                dpg.add_text("1")
            else:
                dpg.add_text("0")

        i += 1


def _draw_memory_buffer_content_block() -> None:

    dpg.delete_item(item=MEMORY_BUFFER_CONTENT_BLOCK, children_only=True)

    with dpg.group(parent=MEMORY_BUFFER_CONTENT_BLOCK, horizontal=True):
        dpg.add_text("refused:")
        dpg.add_text(None, tag="refused_bid")

    with dpg.table(tag=MEMORY_BUFFER, parent=MEMORY_BUFFER_CONTENT_BLOCK,
                   header_row=True, policy=dpg.mvTable_SizingStretchProp,
                   borders_outerH=True, borders_innerV=True, borders_innerH=True, borders_outerV=True,
                   row_background=True, scrollY=True, no_host_extendX=True):
        dpg.add_table_column(label="position", parent=MEMORY_BUFFER)
        dpg.add_table_column(label="bid", parent=MEMORY_BUFFER)

def step_action(sender, app_data) -> None:

    global num_events
    global supervisor

    supervisor.step()
    time, event, bid = supervisor.get_event_info()

    if num_events == 0:
        with dpg.table_row(tag="row_1", parent=EVENT_CALENDAR):
            dpg.add_text(f"{time:.2f}")
            dpg.add_text(event)
            dpg.add_text(bid)
    else:
        with dpg.table_row(tag=f"row_{num_events + 1}", before=f"row_{num_events}"):
            if bid:
                dpg.add_text(f"{time:.2f}")
                dpg.add_text(event)
                dpg.add_text(bid.generating_unit_id)
                dpg.add_text(f"{bid.generation_time:.2f}")
                dpg.add_text(bid.processing_unit_id)
                dpg.add_text(f"{bid.processing_time:.2f}")


    buffer, pushed, poped, refused, pointer = supervisor.get_buffer_info()
    _draw_memory_buffer(buffer, pushed, poped, refused, pointer)

    num_events += 1

def stop_action(sender, app_data) -> None:

    global num_events
    global supervisor

    supervisor.end_step_mode()
    supervisor.step()
    time, event, bid = supervisor.get_event_info()

    with dpg.table_row(tag=f"row_{num_events + 1}", before=f"row_{num_events}"):
        dpg.add_text(f"{time:.2f}")
        dpg.add_text(event)
        dpg.add_text(bid)

    dpg.configure_item(item=STEP_BUTTON, enabled=False)
    dpg.configure_item(item=STOP_BUTTON, enabled=False)

def set_way_callback(sender, app_data):
    if app_data == "step":
        app_tags.WAY = "step"
    elif app_data == "auto":
        app_tags.WAY = "auto"

    print(app_tags.WAY)

def start_button(sender, app_data) -> None:
    if app_tags.WAY == "step":
        try:
            _save_settings()
        except ValueError as err:
            dpg.set_value(item=ERROR_MESSAGE, value=err)
            dpg.configure_item(item=ERROR_WINDOW, show=True)
            return
        except Exception:
            dpg.set_value(item=ERROR_MESSAGE, value=ERROR_DEFAULT_MESSAGE)
            dpg.configure_item(item=ERROR_WINDOW, show=True)
            return

        _draw_event_calendar_content_block()
        _draw_memory_buffer_content_block()

        global supervisor
        supervisor = _get_supervisor()
        supervisor.start_step_mode()

        dpg.configure_item(item=STEP_BUTTON, enabled=True)
        dpg.configure_item(item=STOP_BUTTON, enabled=True)

        dpg.configure_item(item=GRAF_WINDOW, show=False)

        dpg.configure_item(item=EVENT_CALENDAR_WINDOW, show=True)
        dpg.configure_item(item=MEMORY_BUFFER_WINDOW, show=True)
    elif app_tags.WAY == "auto":
        try:
            _save_settings()
        except ValueError as err:
            dpg.set_value(item=ERROR_MESSAGE, value=err)
            dpg.configure_item(item=ERROR_WINDOW, show=True)
            return
        except Exception:
            dpg.set_value(item=ERROR_MESSAGE, value=ERROR_DEFAULT_MESSAGE)
            dpg.configure_item(item=ERROR_WINDOW, show=True)
            return

        dpg.configure_item(item=EVENT_CALENDAR_WINDOW, show=False)
        dpg.configure_item(item=MEMORY_BUFFER_WINDOW, show=False)

        dpg.configure_item(item=GRAF_WINDOW, show=True)

        def f_1():
            data_y = []
            data_x = []
            for i in range(0, 11):
                print(i)
                supervisor = Supervisor(num_sources= i * 10 + 1,
                                num_devices=10,
                                buffer_capacity=10,
                                generation_freq=Settings.generation_freq,
                                min_proc_time=Settings.min_processing_time,
                                max_proc_time=Settings.max_processing_time,
                                num_total_bids=1000)

                stats, device_stats = supervisor.start_auto_mode()

                tb = 0
                tr = 0
                for _, record in stats.items():
                    tb += record.num_total_bids
                    tr += record.num_refused_bids

                data_y.append(tr / tb)
                data_x.append(i * 10)

            _draw_grafic(data_x, data_y, "Ref Prob / sources", "Probability", "Sources")
            print("done")



        def f_2():
            data_y1 = []
            data_x1 = []
            for i in range(0, 11):
                print(i)
                supervisor1 = Supervisor(num_sources= 10,
                                num_devices=10,
                                buffer_capacity=i * 10 + 1,
                                generation_freq=Settings.generation_freq,
                                min_proc_time=Settings.min_processing_time,
                                max_proc_time=Settings.max_processing_time,
                                num_total_bids=1000)

                stats1, device_stats1 = supervisor1.start_auto_mode()

                tb = 0
                tr = 0
                for _, record in stats1.items():
                    tb += record.num_total_bids
                    tr += record.num_refused_bids

                data_y1.append(tr / tb)
                data_x1.append(i * 10)

            _draw_grafic(data_x1, data_y1, "Ref Prob / Buffer size", "Probability", "Buffer")
            print("done")

        def f_3():
            data_y2 = []
            data_x2 = []
            for i in range(0, 11):
                print(i)
                supervisor2 = Supervisor(num_sources= 10,
                                num_devices=i * 10 + 1,
                                buffer_capacity=10,
                                generation_freq=Settings.generation_freq,
                                min_proc_time=Settings.min_processing_time,
                                max_proc_time=Settings.max_processing_time,
                                num_total_bids=1000)

                stats2, device_stats1 = supervisor2.start_auto_mode()

                tb = 0
                tr = 0
                for _, record in stats2.items():
                    tb += record.num_total_bids
                    tr += record.num_refused_bids

                data_y2.append(tr / tb)
                data_x2.append(i * 10)

            _draw_grafic(data_x2, data_y2, "Ref Prob / devices", "Probability", "devices")
            print("done")

        def f_4():
            data_y4 = []
            data_x4 = []
            for i in range(0, 11):
                print(i)
                supervisor4 = Supervisor(num_sources= i * 10 + 1,
                                num_devices=10,
                                buffer_capacity=10,
                                generation_freq=Settings.generation_freq,
                                min_proc_time=Settings.min_processing_time,
                                max_proc_time=Settings.max_processing_time,
                                num_total_bids=1000)

                stats4, dev4 = supervisor4.start_auto_mode()

                tb = 0
                al = 0
                prof = 0
                for _, record in stats4.items():
                    tb += record.num_total_bids
                    al += record.sum_processing_time + record.sum_waiting_time
                    prof += record.sum_processing_time

                f = 0
                sk = 0
                for _, k in dev4.items():
                    sk += k
                    f += 1

                data_y4.append((k / f) * 10)
                data_x4.append(i * 10)

                print(k / f)

            _draw_grafic(data_x4, data_y4, "P / Sources", "P", "num sources")
            print("done")


        def f_5():
            data_y5 = []
            data_x5 = []
            for i in range(0, 11):
                print(i)
                supervisor5 = Supervisor(num_sources= 10,
                                num_devices=i * 10 + 1,
                                buffer_capacity=10,
                                generation_freq=Settings.generation_freq,
                                min_proc_time=Settings.min_processing_time,
                                max_proc_time=Settings.max_processing_time,
                                num_total_bids=1000)

                stats5, dev5 = supervisor5.start_auto_mode()

                tb = 0
                al = 0
                prof = 0
                for _, record in stats5.items():
                    tb += record.num_total_bids
                    al += record.sum_processing_time + record.sum_waiting_time
                    prof += record.sum_processing_time

                f = 0
                sk = 0
                for _, k in dev5.items():
                    sk += k
                    f += 1

                data_y5.append((k / f) * 10)
                data_x5.append(i * 10)

                #print(k / f)

            _draw_grafic(data_x5, data_y5, "P / devices", "P", "num devices")
            print("done")

        def f_6():
            data_y6 = []
            data_x6 = []
            for i in range(0, 11):
                print(i)
                supervisor6 = Supervisor(num_sources= 10,
                                num_devices=10,
                                buffer_capacity=i * 10 + 1,
                                generation_freq=Settings.generation_freq,
                                min_proc_time=Settings.min_processing_time,
                                max_proc_time=Settings.max_processing_time,
                                num_total_bids=1000)

                stats6, dev6 = supervisor6.start_auto_mode()

                tb = 0
                al = 0
                prof = 0
                for _, record in stats6.items():
                    tb += record.num_total_bids
                    al += record.sum_processing_time + record.sum_waiting_time
                    prof += record.sum_processing_time

                f = 0
                sk = 0
                for _, k in dev6.items():
                    sk += k
                    f += 1

                data_y6.append((k / f) * 10)
                data_x6.append(i * 10)

                #print(k / f)

            _draw_grafic(data_x6, data_y6, "P / Buffer", "P", "Buffer size")
            print("done")

        def f_7():
            data_y7 = []
            data_x7 = []
            for i in range(0, 11):
                print(i)
                supervisor7 = Supervisor(num_sources= i * 10 + 1,
                                num_devices=10,
                                buffer_capacity=10,
                                generation_freq=Settings.generation_freq,
                                min_proc_time=Settings.min_processing_time,
                                max_proc_time=Settings.max_processing_time,
                                num_total_bids=1000)

                stats7, dev7 = supervisor7.start_auto_mode()

                tb = 0
                al = 0
                prof = 0
                for _, record in stats7.items():
                    tb += record.num_total_bids
                    al += record.sum_processing_time + record.sum_waiting_time
                    #prof += record.sum_processing_time

                f = 0
                sk = 0
                for _, k in dev7.items():
                    sk += k
                    f += 1

                data_y7.append(al / tb)
                data_x7.append(i * 10)

                #print(k / f)

            _draw_grafic2(data_x7, data_y7, "Mid time / Sources", "mid time", "num sources")
            print("done")

        def f_8():
            data_y8 = []
            data_x8 = []
            for i in range(0, 11):
                print(i)
                supervisor8 = Supervisor(num_sources= 10,
                                num_devices=i * 10 + 1,
                                buffer_capacity=10,
                                generation_freq=Settings.generation_freq,
                                min_proc_time=Settings.min_processing_time,
                                max_proc_time=Settings.max_processing_time,
                                num_total_bids=1000)

                stats8, dev8 = supervisor8.start_auto_mode()

                tb = 0
                al = 0
                prof = 0
                for _, record in stats8.items():
                    tb += record.num_total_bids
                    al += record.sum_processing_time + record.sum_waiting_time
                    #prof += record.sum_processing_time

                f = 0
                sk = 0
                for _, k in dev8.items():
                    sk += k
                    f += 1

                data_y8.append(al / tb)
                data_x8.append(i * 10)

                #print(k / f)

            _draw_grafic2(data_x8, data_y8, "Mid time / Devices", "mid time", "num devices")
            print("done")

        def f_9():
            data_y9 = []
            data_x9 = []
            for i in range(0, 11):
                print(i)
                supervisor9 = Supervisor(num_sources= 10,
                                num_devices=10,
                                buffer_capacity=i * 10 + 1,
                                generation_freq=Settings.generation_freq,
                                min_proc_time=Settings.min_processing_time,
                                max_proc_time=Settings.max_processing_time,
                                num_total_bids=1000)

                stats9, dev9 = supervisor9.start_auto_mode()

                tb = 0
                al = 0
                prof = 0
                for _, record in stats9.items():
                    tb += record.num_total_bids
                    al += record.sum_processing_time + record.sum_waiting_time
                    #prof += record.sum_processing_time

                f = 0
                sk = 0
                for _, k in dev9.items():
                    sk += k
                    f += 1

                data_y9.append(al / tb)
                data_x9.append(i * 10)

                #print(k / f)

            _draw_grafic2(data_x9, data_y9, "Mid time / Buffer", "mid time", "buffer size")
            print("done")

        # # вероятность отказа / колво источников
        f_1()
        # # # вероятность отказа / размер буффера
        f_2()
        # # # вероятность отказа / размер приборов
        f_3()
        # # # загруженность приборов / кол-во источников
        f_4()
        # # # загруженность приборов / кол-во устройств
        f_5()
        # # # загруженность приборов / размер буффера
        f_6()
        # # среднее время в системе / кол-во источников
        f_7()
        # # среднее время в системе / кол-во устройств
        f_8()
        # среднее время в системе / размер буффера
        f_9()




def _draw_grafic(data_x: list, data_y: list, name: str, namey: str, namex: str) -> None:
    dpg.delete_item(item=GRAF, children_only=True)
    print("into")
    with dpg.plot(label=f'{name}', height=400, width=-1, parent=GRAF_CONTENT_BLOCK):

        xaxis = dpg.add_plot_axis(dpg.mvXAxis, label=f'{namex}')
        yaxis = dpg.add_plot_axis(dpg.mvYAxis, label=f'{namey}', lock_max=True)

        dpg.add_shade_series(data_x, data_y, label="Stock 3", parent=yaxis)
        dpg.bind_item_theme(dpg.last_item(), "stock_theme3")

def _draw_grafic2(data_x: list, data_y: list, name: str, namey: str, namex: str) -> None:
    dpg.delete_item(item=GRAF, children_only=True)
    print("into")
    with dpg.plot(label=f'{name}', height=400, width=-1, parent=GRAF_CONTENT_BLOCK):

        xaxis = dpg.add_plot_axis(dpg.mvXAxis, label=f'{namex}')
        yaxis = dpg.add_plot_axis(dpg.mvYAxis, label=f'{namey}')

        dpg.add_shade_series(data_x, data_y, label="Stock 3", parent=yaxis)
        dpg.bind_item_theme(dpg.last_item(), "stock_theme3")