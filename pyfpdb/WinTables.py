#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Routines for detecting and handling poker client windows for MS Windows.
"""
#    Copyright 2008 - 2010, Ray E. Barker

#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

########################################################################
# to do
# for win7 the fixed b_width and tb_height are not correct - need to discover these from os
import L10n
_ = L10n.get_translation()

#    Standard Library modules
import re

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("hud")

from PyQt6.QtGui import QWindow
import ctypes
EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
GetWindowRect = ctypes.windll.user32.GetWindowRect
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindow = ctypes.windll.user32.IsWindow

#    FreePokerTools modules
from TableWindow import Table_Window

#    We don't know the border width or title bar height
#    so we guess here. We can probably get these from a windows call.
b_width = 3
tb_height = 29

titles = {}

class Table(Table_Window):
    # specific win32 values
    GW_OWNER = 4
    GWL_EXSTYLE = -20
    WS_EX_TOOLWINDOW = 0x00000080
    SM_CXSIZEFRAME = 32
    SM_CYCAPTION = 4

    def find_table_parameters(self):
        """Finds poker client window with the given table name."""
        # titles = {}
        EnumWindows(EnumWindowsProc(win_enum_handler), 0)
        for hwnd in titles:
            if titles[hwnd] == "":
                continue
            # if window not visible, probably not a table
            if not IsWindowVisible(hwnd):
                continue
            # if window is a child of another window, probably not a table
            if GetParent(hwnd) != 0:
                continue
            HasNoOwner = GetWindow(hwnd, GW_OWNER) == 0
            WindowStyle = GetWindowLong(hwnd, GWL_EXSTYLE)
            if HasNoOwner and WindowStyle & WS_EX_TOOLWINDOW != 0:
                continue
            if not HasNoOwner and WindowStyle & WS_EX_APPWINDOW == 0:
                continue
            
            if re.search(self.search_string, titles[hwnd], re.I):
                if self.check_bad_words(titles[hwnd]):
                    continue

                self.number = hwnd
                break

        if self.number is None:
            log.error(_("Window %s not found. Skipping."), self.search_string)
            return

        self.title = titles[self.number]
        self.hud = None
        self.gdkhandle = QWindow.fromWinId(self.number)

    def get_geometry(self):
        try:
            if IsWindow(self.number):  # ✅ Checks if the window handle is valid
                rect = ctypes.wintypes.RECT()  # ✅ Create a RECT structure
                GetWindowRect(self.number, ctypes.byref(rect))  # ✅ Get window bounds
                x, y, width, height = rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
                                
#                 # this apparently returns x = far left side of window, width = far right side of window, y = top of window, height = bottom of window
#                 # so apparently we have to subtract x from "width" to get actual width, and y from "height" to get actual height ?
#                 # it definitely gives slightly different results than the GTK code that does the same thing.
#
#                 # minimised windows are given -32000 (x,y) value,
#                 #   so just zeroise to avoid downstream confusion
#                 if x < 0: x = 0
#                 if y < 0: y = 0
#
#                 width = width - x
#                 height = height - y
                
                # determine system titlebar and border setting constant values
                # see http://stackoverflow.com/questions/431470/window-border-width-and-height-in-win32-how-do-i-get-it
                try:
                    self.b_width; self.tb_height
                except:

                    self.b_width = GetSystemMetrics(SM_CXSIZEFRAME)
                    self.tb_height = GetSystemMetrics(SM_CYCAPTION)

                # fixme - x and y must _not_ be adjusted by the b_width if the window has been maximised
                return {
                    'x'      : int(x) + self.b_width,
                    'y'      : int(y) + self.tb_height + self.b_width,
                    'height' : int(height),
                    'width'  : int(width)
                }
            else:
                log.debug("newhud - WinTables window not found")
                return None
        except AttributeError:
            return None

    def get_window_title(self):
        length = GetWindowTextLength(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        GetWindowText(hwnd, buf, length + 1)
        return buf.value

    def topify(self, window):
        """Set the specified Qt window to stayontop in MS Windows."""

        # self.number is the windows handle
        # self.gdkhandle is a foreign QWindow associated with the poker client
        # window is a seat_window object from Mucked (a Qt QWidget)
        # window.windowHandle() is a QWindow object

        if self.gdkhandle is None:
            self.gdkhandle = QWindow.fromWinId(int(self.number))
        window.windowHandle().setTransientParent(self.gdkhandle)

def win_enum_handler(hwnd, lParams):
    length = GetWindowTextLength(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    GetWindowText(hwnd, buf, length + 1)
    titles[hwnd] = buf.value
    return True
