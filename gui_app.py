#!/bin/python3

import logging
import dearpygui.dearpygui as dpg
from dearpygui.demo import _hsv_to_rgb

import app_tags
from app_actions import step_action, stop_action, set_way_callback, start_button

from app_tags import *


logging.basicConfig(filename='app.log', filemode='w', level=logging.DEBUG)


dpg.create_context()
dpg.set_global_font_scale(1.2)


with dpg.window(tag="primary-window"):

    dpg.add_text("GENERAL SETTINGS")

    dpg.add_separator()
    with dpg.group(horizontal=True):
        dpg.add_slider_int(tag=SETTINGS_NUM_SOURCES,
                          default_value=10,
                          min_value=1,
                          max_value=20,
                          format="sources = %d",
                          width=400, height=10)

        dpg.add_slider_int(tag=SETTINGS_NUM_DEVICES,
                          default_value=10,
                          min_value=1,
                          max_value=20,
                          format="devices = %d",
                          width=400, height=10)

        dpg.add_slider_int(tag=SETTINGS_BUFFER_CAPACITY,
                          default_value=10,
                          min_value=1,
                          max_value=20,
                          format="buffer size = %d",
                          width=400, height=10)


    dpg.add_separator()
    dpg.add_text("ADVANCED SETTINGS")
    dpg.add_spacer()
    dpg.add_separator()
    dpg.add_text("REQUEST GENERATION")
    dpg.add_slider_float(tag=SETTINGS_GENERATION_FREQ,
                        default_value=0.1,
                        min_value=0.1,
                        max_value=10,
                        format="frequency = %.1f",
                        width=1215, height=10)
    dpg.add_separator()
    dpg.add_spacer()
    dpg.add_text("PROCESSING TIME PER REQUEST")
    dpg.add_slider_float(tag=SETTINGS_MIN_PROCESSING_TIME,
                        default_value=20.0,
                        min_value=1.0,
                        max_value=100.0,
                        format="min = %.1f",
                        width=1215, height=10)
    dpg.add_slider_float(tag=SETTINGS_MAX_PROCESSING_TIME,
                        default_value=80.0,
                        min_value=1.0,
                        max_value=100.0,
                        format="max = %.1f",
                        width=1215, height=10)
    dpg.add_separator()
    dpg.add_spacer()
    dpg.add_text("REQUESTS !!!ONLY FOR STEP MODE!!!")
    dpg.add_slider_int(
                      tag=SETTINGS_MAX_BIDS,
                      default_value=100,
                      min_value=10,
                      max_value=1000,
                      format="max number = %d",
                        width=1215, height=10)
    dpg.add_separator()
    dpg.add_text("WAYS")
    with dpg.group(horizontal=True):

        dpg.add_radio_button(items=["step", "auto"],
                             horizontal=True,
                                callback=set_way_callback)
        i=4
        with dpg.theme(tag="__demo_theme"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, _hsv_to_rgb(i / 7.0, 0.6, 0.6))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _hsv_to_rgb(i / 7.0, 0.8, 0.8))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _hsv_to_rgb(i / 7.0, 0.7, 0.7))
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, i * 5)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, i * 3, i * 3)

        dpg.add_button(label="START / RESTART", callback=start_button)
        dpg.bind_item_theme(dpg.last_item(), "__demo_theme")

    with dpg.window(label="Error", tag=ERROR_WINDOW, modal=True, show=False):
        dpg.add_text(ERROR_DEFAULT_MESSAGE, tag=ERROR_MESSAGE)

    with dpg.child_window(label="Event Calendar",
                    tag=EVENT_CALENDAR_WINDOW,
                    show=False,
                    width=1000, height=410,
                    pos=(0, 380)):

        with dpg.group(horizontal=True):
            dpg.add_button(label="step", tag=STEP_BUTTON, callback=step_action)
            dpg.add_button(label="stop", tag=STOP_BUTTON, callback=stop_action, show=False)

        dpg.add_spacer()
        dpg.add_group(tag=EVENT_CALENDAR_CONTENT_BLOCK)

    with dpg.child_window(label="Memory Buffer",
                    tag=MEMORY_BUFFER_WINDOW,
                    show=False,
                    width=1460 - 1000, height=410,
                    pos=(1000, 380)):

        dpg.add_group(tag=MEMORY_BUFFER_CONTENT_BLOCK)

    with dpg.child_window(label="GRAF_WINDOW",
                    tag=GRAF_WINDOW,
                    show=False,                    
                    width=720 * 2, height=410 * 2,
                    pos=(0, 380)):
        with dpg.group(horizontal=True):
            dpg.add_group(tag=GRAF_CONTENT_BLOCK)


with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (145, 93, 93), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, (145, 93, 93), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (46, 8, 42), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (46, 8, 42), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (0, 8, 42), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Button, (1, 255, 255), category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)

    with dpg.theme_component(dpg.mvInputInt):
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (145, 93, 93), category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)

dpg.bind_theme(global_theme)

dpg.set_primary_window(window="primary-window", value=True)

dpg.create_viewport(title='Application', width=1480, height=800)
dpg.setup_dearpygui()
dpg.show_viewport()

dpg.start_dearpygui()
dpg.destroy_context()
