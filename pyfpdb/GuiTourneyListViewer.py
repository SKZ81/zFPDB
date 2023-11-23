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

from PyQt5.QtCore import QCoreApplication, QSortFilterProxyModel, Qt
from PyQt5.QtGui import QPainter, QPixmap, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (QApplication, QFrame, QMenu,
                            QComboBox, QLabel, QLineEdit, QPushButton,
                            QProgressDialog, QScrollArea, QSplitter,
                            QTableView, QHBoxLayout, QVBoxLayout)

from GuiTourneyViewer import GuiTourneyViewer
import GuiReplayer

class GuiTourneyListViewer(GuiTourneyViewer):
    def __init__(self, config, db, sql, parent, debug=True):
        GuiTourneyViewer.__init__(self, config, db, sql, parent, debug)
        self.filters.registerButton1Name(_("Refresh List"))
        self.filters.registerButton1Callback(self.refreshTourneyList)

        self.colnum = {
                  'Id'        : 0,
                  'Tour #'          : 1,
                  'Entries'       : 2,
                  'Prize'      : 3,
                  'StartTime'      : 4,
                  'EndTime'    : 5,
                  'Name'    : 8,
                  'SiteId'          : 7,
                  'Currency'          : 8,
                  'Buyin'          : 9,
                  'Fee'         : 10,
                  'Speed'       : 11,
                 }

        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.model = QStandardItemModel(0, len(self.colnum), self.table)
        self.model.setHorizontalHeaderLabels(self.colnum.keys())

        self.filterModel = QSortFilterProxyModel()
        self.filterModel.setSourceModel(self.model)
        self.filterModel.setSortRole(Qt.UserRole)
        self.table.setModel(self.filterModel)
        self.table.verticalHeader().hide()
        # self.table.doubleClicked.connect(self.row_activated)
        # self.table.contextMenuEvent = self.contextMenu
        self.filterModel.rowsInserted.connect(self.table.resizeRowsToContents)
        # self.filterModel.filterAcceptsRow = lambda row, sourceParent: self.is_row_in_card_filter(row)
        #
        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)

        self.frame.layout().addWidget(self.table)
        self.table.doubleClicked.connect(self.row_activated)
        # self.table.contextMenuEvent = self.contextMenu

        # self.mainVBox.show()
    #end def __init__

    def get_filters_display(self):
        return {
                "Heroes"    : True,
                "Sites"     : True,
                "Games"     : True,
                "Currencies": True,
                "Limits"    : False,
                "LimitSep"  : False,
                "LimitType" : False,
                "Type"      : False,
                "UseType"   : 'tour',
                "Seats"     : False,
                "SeatSep"   : False,
                "Dates"     : True,
                "Groups"    : False,
                "Button1"   : True,
                "Button2"   : False
                }

    def refreshTourneyList(self):
        site_ids = [self.conf.get_site_id(site_name) for site_name, cbSite in self.filters.cbSites.items() if cbSite.isChecked()]
        column_names, tourneys = self.db.getTourneysFromSites(site_ids)
        for tourney in tourneys:
            modelrow = [QStandardItem(str(r)) for r in tourney]
            for index, item in enumerate(modelrow):
                item.setEditable(False)
                if index in (self.colnum['Buyin'], self.colnum['Fee'], self.colnum['Prize']) and item.data() != None:
                    item.setData(float(item.data(Qt.DisplayRole)), Qt.UserRole)
            self.model.appendRow(modelrow)
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()

    def displayClicked(self, widget, data=None):
        if self.prepare(10, 9):
            # result=self.db.getTourneyInfo(self.siteName, self.tourneyNo)
            print(result)
            if result[1] == None:
                self.table.reset()
                self.errorLabel = QLabel(_("Tournament not found.") + " " + _("Please ensure you imported it and selected the correct site."))
                self.mainVBox.layout().addWidget(self.errorLabel)
            else:
                x=0
                y=0
                for i in range(1,len(result[0])):
                    if y==9:
                        x+=2
                        y=0

                    label = QLabel(result[0][i])
                    self.table.attach(label,x,x+1,y,y+1)

                    if result[1][i]==None:
                        label = QLabel("N/A")
                    else:
                        label = QLabel(result[1][i])
                    self.table.attach(label,x+1,x+2,y,y+1)

                    y+=1
        # self.mainVBox.show_all()
    #def displayClicked

    def displayPlayerClicked(self, widget, data=None):
        if self.prepare(4, 5):
            result=self.db.getTourneyPlayerInfo(self.siteName, self.tourneyNo, self.playerName)
            if result[1] == None:
                self.table.reset()
                self.errorLabel = QLabel(_("Player or tournament not found.") + " " + _("Please ensure you imported it and selected the correct site."))
                self.mainVBox.layout().addWidget(self.errorLabel)
            else:
                x=0
                y=0
                for i in range(1,len(result[0])):
                    if y==5:
                        x+=2
                        y=0

                    label = QLabel(result[0][i])
                    self.table.attach(label,x,x+1,y,y+1)

                    if result[1][i]==None:
                        label = QLabel(_("N/A"))
                    else:
                        label = QLabel(result[1][i])
                    self.table.attach(label,x+1,x+2,y,y+1)

                    y+=1
        # self.mainVBox.show()
    #def displayPlayerClicked*

    def contextMenu(self, event):
        index = self.view.currentIndex()
        if index.row() < 0:
            return
        hand = self.hands[int(index.sibling(index.row(), self.colnum['HandId']).data())]
        m = QMenu()
        copyAction = m.addAction('Copy to clipboard')
        copyAction.triggered.connect(partial(self.copyHandToClipboard, hand=hand))
        m.move(event.globalPos())
        m.exec_()

    def row_activated(self, index):
        tourney_id = int(index.sibling(index.row(), self.colnum['Id']).data())
        handlist = [x[0] for x in self.db.get_hands_for_tourney(tourney_id)[1]]

        self.replayer = GuiReplayer.GuiReplayer(self.conf,  self.sql, self, handlist)
        self.replayer.play_hand(0)

    def get_vbox(self):
        """returns the vbox of this thread"""
        return self.mainVBox
    #end def get_vbox

    def prepare(self, columns, rows):
        try: self.errorLabel.destroy()
        except: pass

        try:
            self.tourneyNo = int(self.entryTourney.text())
        except ValueError:
            self.errorLabel = QLabel(_("invalid entry in tourney number - must enter numbers only"))
            self.mainVBox.layout().addWidget(self.errorLabel)
            return False
        self.siteName=self.siteBox.currentText()
        self.playerName=self.entryPlayer.text()

        self.table.reset()

        return True
    #end def readInfo
#end class GuiTourneyViewer
