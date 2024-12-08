import time
import RNS

from typing import Union
from kivy.metrics import dp,sp
from kivy.lang.builder import Builder
from kivy.core.clipboard import Clipboard
from kivy.utils import escape_markup
from kivymd.uix.recycleview import MDRecycleView
from kivymd.uix.list import OneLineIconListItem
from kivymd.uix.pickers import MDColorPicker
from kivymd.icon_definitions import md_icons
from kivymd.toast import toast
from kivy.properties import StringProperty, BooleanProperty
from kivy.effects.scroll import ScrollEffect
from kivy.clock import Clock
from sideband.sense import Telemeter
import threading
from datetime import datetime

if RNS.vendor.platformutils.get_platform() == "android":
    from ui.helpers import ts_format
    from android.permissions import request_permissions, check_permission
else:
    from .helpers import ts_format

class Utilities():
    def __init__(self, app):
        self.app = app
        self.screen = None
        self.rnstatus_screen = None
        self.rnstatus_instance = None
        self.logviewer_screen = None
    
        if not self.app.root.ids.screen_manager.has_screen("utilities_screen"):
            self.screen = Builder.load_string(layout_utilities_screen)
            self.screen.app = self.app
            self.screen.delegate = self
            self.app.root.ids.screen_manager.add_widget(self.screen)
        
        self.screen.ids.telemetry_scrollview.effect_cls = ScrollEffect
        info  = "This section contains various utilities and diagnostics tools, "
        info += "that can be helpful while using Sideband and Reticulum."
        
        if self.app.theme_cls.theme_style == "Dark":
            info = "[color=#"+self.app.dark_theme_text_color+"]"+info+"[/color]"
        
        self.screen.ids.utilities_info.text = info


    ### rnstatus screen
    ######################################

    def rnstatus_action(self, sender=None):
        if not self.app.root.ids.screen_manager.has_screen("rnstatus_screen"):
            self.rnstatus_screen = Builder.load_string(layout_rnstatus_screen)
            self.rnstatus_screen.app = self.app
            self.rnstatus_screen.delegate = self
            self.app.root.ids.screen_manager.add_widget(self.rnstatus_screen)

        self.app.root.ids.screen_manager.transition.direction = "left"
        self.app.root.ids.screen_manager.current = "rnstatus_screen"
        self.app.sideband.setstate("app.displaying", self.app.root.ids.screen_manager.current)
        
        self.update_rnstatus()

    def update_rnstatus(self, sender=None):
        threading.Thread(target=self.update_rnstatus_job, daemon=True).start()

    def update_rnstatus_job(self, sender=None):
        if self.rnstatus_instance == None:
            import RNS.Utilities.rnstatus as rnstatus
            self.rnstatus_instance = rnstatus

        import io
        from contextlib import redirect_stdout
        output = "None"
        with io.StringIO() as buffer, redirect_stdout(buffer):
            with RNS.logging_lock:
                self.rnstatus_instance.main(rns_instance=RNS.Reticulum.get_instance())
                output = buffer.getvalue()

        def cb(dt):
            self.rnstatus_screen.ids.rnstatus_output.text = f"[font=RobotoMono-Regular][size={int(dp(12))}]{output}[/size][/font]"
        Clock.schedule_once(cb, 0.2)

        if self.app.root.ids.screen_manager.current == "rnstatus_screen":
            Clock.schedule_once(self.update_rnstatus, 1)

    ### Log viewer screen
    ######################################

    def logviewer_action(self, sender=None):
        if not self.app.root.ids.screen_manager.has_screen("logviewer_screen"):
            self.logviewer_screen = Builder.load_string(layout_logviewer_screen)
            self.logviewer_screen.app = self.app
            self.logviewer_screen.delegate = self
            self.app.root.ids.screen_manager.add_widget(self.logviewer_screen)

        self.app.root.ids.screen_manager.transition.direction = "left"
        self.app.root.ids.screen_manager.current = "logviewer_screen"
        self.app.sideband.setstate("app.displaying", self.app.root.ids.screen_manager.current)
        
        self.update_logviewer()

    def update_logviewer(self, sender=None):
        threading.Thread(target=self.update_logviewer_job, daemon=True).start()

    def update_logviewer_job(self, sender=None):
        try:
            output = self.app.sideband.get_log()
        except Exception as e:
            output = f"An error occurred while retrieving log entries:\n{e}"

        self.logviewer_screen.log_contents = output
        def cb(dt):
            self.logviewer_screen.ids.logviewer_output.text = f"[font=RobotoMono-Regular][size={int(dp(12))}]{output}[/size][/font]"
        Clock.schedule_once(cb, 0.2)

        if self.app.root.ids.screen_manager.current == "logviewer_screen":
            Clock.schedule_once(self.update_logviewer, 1)

    def logviewer_copy(self, sender=None):
        Clipboard.copy(self.logviewer_screen.log_contents)
        if True or RNS.vendor.platformutils.is_android():
            toast("Log copied to clipboard")


layout_utilities_screen = """
MDScreen:
    name: "utilities_screen"
    
    BoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Utilities"
            anchor_title: "left"
            elevation: 0
            left_action_items:
                [['menu', lambda x: root.app.nav_drawer.set_state("open")]]
            right_action_items:
                [
                ['close', lambda x: root.app.close_any_action(self)],
                ]

        ScrollView:
            id: telemetry_scrollview

            MDBoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: [dp(28), dp(32), dp(28), dp(16)]

                # MDLabel:
                #     text: "Utilities & Tools"
                #     font_style: "H6"

                MDLabel:
                    id: utilities_info
                    markup: True
                    text: ""
                    size_hint_y: None
                    text_size: self.width, None
                    height: self.texture_size[1]

                MDBoxLayout:
                    orientation: "vertical"
                    spacing: "24dp"
                    size_hint_y: None
                    height: self.minimum_height
                    padding: [dp(0), dp(35), dp(0), dp(35)]

                    MDRectangleFlatIconButton:
                        id: rnstatus_button
                        icon: "wifi-check"
                        text: "Reticulum Status"
                        padding: [dp(0), dp(14), dp(0), dp(14)]
                        icon_size: dp(24)
                        font_size: dp(16)
                        size_hint: [1.0, None]
                        on_release: root.delegate.rnstatus_action(self)
                        disabled: False

                    MDRectangleFlatIconButton:
                        id: logview_button
                        icon: "list-box-outline"
                        text: "Log Viewer"
                        padding: [dp(0), dp(14), dp(0), dp(14)]
                        icon_size: dp(24)
                        font_size: dp(16)
                        size_hint: [1.0, None]
                        on_release: root.delegate.logviewer_action(self)
                        disabled: False

                    MDRectangleFlatIconButton:
                        id: advanced_button
                        icon: "network-pos"
                        text: "Advanced RNS Configuration"
                        padding: [dp(0), dp(14), dp(0), dp(14)]
                        icon_size: dp(24)
                        font_size: dp(16)
                        size_hint: [1.0, None]
                        on_release: root.delegate.advanced_action(self)
                        disabled: False
                
"""

layout_rnstatus_screen = """
MDScreen:
    name: "rnstatus_screen"
    
    BoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            id: top_bar
            title: "Reticulum Status"
            anchor_title: "left"
            elevation: 0
            left_action_items:
                [['menu', lambda x: root.app.nav_drawer.set_state("open")]]
            right_action_items:
                [
                # ['refresh', lambda x: root.delegate.update_rnstatus()],
                ['close', lambda x: root.app.close_sub_utilities_action(self)],
                ]

        MDScrollView:
            id: rnstatus_scrollview
            size_hint_x: 1
            size_hint_y: None
            size: [root.width, root.height-root.ids.top_bar.height]
            do_scroll_x: False
            do_scroll_y: True

            MDGridLayout:
                cols: 1
                padding: [dp(28), dp(14), dp(28), dp(28)]
                size_hint_y: None
                height: self.minimum_height

                MDLabel:
                    id: rnstatus_output
                    markup: True
                    text: ""
                    size_hint_y: None
                    text_size: self.width, None
                    height: self.texture_size[1]
"""

layout_logviewer_screen = """
MDScreen:
    name: "logviewer_screen"
    
    BoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            id: top_bar
            title: "Log Viewer"
            anchor_title: "left"
            elevation: 0
            left_action_items:
                [['menu', lambda x: root.app.nav_drawer.set_state("open")]]
            right_action_items:
                [
                ['content-copy', lambda x: root.delegate.logviewer_copy()],
                ['close', lambda x: root.app.close_sub_utilities_action(self)],
                ]

        MDScrollView:
            id: logviewer_scrollview
            size_hint_x: 1
            size_hint_y: None
            size: [root.width, root.height-root.ids.top_bar.height]
            do_scroll_x: False
            do_scroll_y: True

            MDGridLayout:
                cols: 1
                padding: [dp(28), dp(14), dp(28), dp(28)]
                size_hint_y: None
                height: self.minimum_height

                MDLabel:
                    id: logviewer_output
                    markup: True
                    text: ""
                    size_hint_y: None
                    text_size: self.width, None
                    height: self.texture_size[1]
"""