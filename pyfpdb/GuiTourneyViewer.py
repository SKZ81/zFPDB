#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2010-2011 Steffen Schaumburg
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in agpl-3.0.txt.

import L10n
_ = L10n.get_translation()
from PyQt6.QtWidgets import (QSplitter, QScrollArea, QFrame, QVBoxLayout)

import Filters

class GuiTourneyViewer(QSplitter):
    def __init__(self, config, db, querylist, parent, debug):
        """Constructor for GraphViewer"""
        QSplitter.__init__(self, parent)
        self.sql = querylist
        self.conf = config
        self.db = db
        self.debug = debug
        self.parent = parent

        self.filters_display = self.get_filters_display()

        self.filters = Filters.Filters(self.db, display = self.filters_display)

        scroll = QScrollArea()
        scroll.setWidget(self.filters)
        self.addWidget(scroll)

        self.frame = QFrame()
        self.graphBox = QVBoxLayout()
        self.frame.setLayout(self.graphBox)
        self.addWidget(self.frame)
        self.setStretchFactor(0, 0)
        self.setStretchFactor(1, 1)

    def get_filters_display(self): abstract

