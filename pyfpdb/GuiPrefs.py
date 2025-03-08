#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Carl Gherardi
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

import os
import xml.dom.minidom
from xml.dom.minidom import Node, Element
from collections.abc import Iterable
from typing import Optional
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QVBoxLayout, QTreeWidget,
                             QTreeWidgetItem, QComboBox, QCheckBox, QWidget)
from PyQt6.QtCore import (Qt, pyqtSlot)

import Configuration

rewrite = {
    'general' : _('General'),
    'supported_databases' : _('Databases'),
    'import'  : _('Import'),
    'gui_qss_theme' : _('Theme'),
    'name' : _('Name'),
    'path' : _('Path'),
    'hud_ui' : _('HUD'),
    'supported_sites' : _('Sites'),
    'supported_games' : _('Games'),
    'popup_windows' : _('Popup Windows'),
    'pu' : _('Window'),
    'pu_name' : _('Popup Name'),
    'pu_stat' : _('Stat'),
    'pu_stat_name' : _('Stat Name'),
    'aux_windows' : _('Auxiliary Windows'),
    'aw stud_mucked' : _('Stud mucked'),
    'aw mucked' : _('Mucked'),
    'hhcs' : _('Hand History Converters'),
    'gui_cash_stats' : _('Ring Player Stats'),
    'field_type' : _('Field Type'),
    'col': _('Column'),
    'col_title' : _('Column Heading'),
    'xalignment' : _('Left/Right Align'),
    'disp_all' : _('Show in Summaries'),
    'disp_posn' : _('Show in Position Stats'),
    'col_name' : _('Stat Name'),
    'field_format' : _('Format'),
}

# For each attribute in this list, the value field will be a checkbox.
boolean_attributes = [
    'import.callFpdbHud',
    'import.fastStoreHudCache',
    'import.saveActions',
    'import.cacheSessions',
    'import.publicDB',
    'col.disp_all',
    'col.disp_posn',
    'site.enabled',
    'site.aux_enabled',
    'email.useSsl',
]

def get_theme_names(config: Configuration.Config, node: Element):
    themes = ['']
    path = node.getAttribute('path')
    if path is not None:
        full_path = os.path.join(config.fpdb_root_path, path)
        try:
            for d in os.listdir(full_path):
                if os.path.isdir(os.path.join(full_path, d)):
                    themes.append(d)
        except FileNotFoundError:
            #TODO: clean warning popup
            print("FileNotFoundError:", full_path)
        print("themes:", themes)
    return themes


# For each attribute in this map, the value field will be a combox.
# maps value is a callable that takes the attribute parent node, and returns
# a list of strings that will be used as choices in the combobox
choice_attributes = {
    'general.config_difficulty': lambda config, node: ['normal', 'expert'],
    'gui_qss_theme.name' : get_theme_names,
}

entitled_items = {
    'col': 'name',
    'site': 'name',
    'game': 'name',
    'aw': 'name',
    'ls': 'name',
    'ss': 'name',
    'stat': 'name',
    'pu': 'pu_name',
    'pu_stat': 'pu_stat_name',
    'hhc': 'site',
    'database': 'db_server',
}

class CheckBoxItem(QCheckBox):
    def __init__(self, item: QTreeWidgetItem, value: bool):
        super().__init__() # space label to mask DisplayRole
        self.item = item
        self.column = 1
        self.setCheckState(Qt.CheckState.Checked if value else Qt.CheckState.Unchecked)
        self.setLabel(value)
        self.stateChanged.connect(self.onValueChanged)  # Connect to custom handler

    def setLabel(self, value):
        self.setText("On"if value else "Off")

    def onValueChanged(self, value: int):
        str_value = "True" if value else "False"
        self.setLabel(value)
        self.item.setData(self.column, Qt.ItemDataRole.UserRole, str_value)
        tree_widget = self.item.treeWidget()
        if tree_widget:
            tree_widget.itemChanged.emit(self.item, self.column)

class ComboBoxItem(QComboBox):
    # # items = {
    # #     'theme_name': lambda self, parent:
    # #
    # # }
    def __init__(self, item: QTreeWidgetItem, choice_list: Iterable[Optional[str]]=[], initial_value : str=""):
        super().__init__()
        self.item = item
        self.column = 1
        self.addItems(choice_list)
        index = self.findText(initial_value)  # Find index of the item with matching text
        if index != -1:  # Ensure the item exists in the combo box
            self.setCurrentIndex(index)  # Select the item
        else:
            # log.warning(f"GuiPrefs Value '{initial_value}' not found in choice list {str(choice_list)}")
            print(f"GuiPrefs Value '{initial_value}' not found in choice list {str(choice_list)}")

        self.currentIndexChanged.connect(self.onSelectionChanged)  # Connect to custom handler

    def onSelectionChanged(self, index: int):
        """Update the QTreeWidgetItem's data when the ComboBoxItem selection changes."""
        # if self.item:
        selected_value = self.itemText(index)
        self.item.setData(self.column, Qt.ItemDataRole.UserRole, selected_value)
        print(f"combo: set value {selected_value}")
        # Emit itemChanged signal so that updateConf() gets called
        tree_widget = self.item.treeWidget()
        if tree_widget:
            tree_widget.itemChanged.emit(self.item, self.column)

class SyncingTreeWidgetItem(QTreeWidgetItem):
    """A QTreeWidgetItem that ensures UserRole is updated when DisplayRole changes."""
    def setData(self, column: int, role: Qt.ItemDataRole, value):
        print(f"SyncingTreeWidgetItem.setData({role}, {value}")
        # If DisplayRole is changed, update UserRole as well
        if role == Qt.ItemDataRole.EditRole:
            print(f"SyncingTreeWidgetItem.setData({value}")
            super().setData(column, Qt.ItemDataRole.UserRole, value)
        super().setData(column, role, value)

class GuiPrefs(QDialog):

    def __init__(self, config, parentwin):
        QDialog.__init__(self, parentwin)
        self.resize(600, 350)
        self.config = config
        self.setLayout(QVBoxLayout())


        self.doc = self.config.get_doc()

        self.configView = QTreeWidget()
        self.configView.setColumnCount(2)
        self.configView.setHeaderLabels([_("Setting"), _("Value (double-click to change)")])

        if self.doc.documentElement.tagName == 'FreePokerToolsConfig':
            self.root = QTreeWidgetItem(["fpdb", None])
            self.configView.addTopLevelItem(self.root)
            self.root.setExpanded(True)
            for elem in self.doc.documentElement.childNodes:
                self.addTreeRows(self.root, elem)
        self.layout().addWidget(self.configView)
        self.configView.resizeColumnToContents(0)

        self.configView.itemChanged.connect(self.updateConf)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, self)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        self.layout().addWidget(btns)

    def updateConf(self, item, column):
        if column != 1:
            return
        item.data(1, Qt.ItemDataRole.UserRole+1).value = item.data(1, Qt.ItemDataRole.UserRole)

    def rewriteText(self, s):
        if s in rewrite:
            s = rewrite[s]
        return s

    def addTreeRows(self, parent, node):
        if (node.nodeType == node.ELEMENT_NODE):
            node_name = node.nodeName
#         elif (node.nodeType == node.TEXT_NODE):
#             # text nodes hold the whitespace (or whatever) between the xml elements, not used here
#             (node.nodeName, value) = ("TEXT: ["+node.nodeValue+"|"+node.nodeValue+"]", node.data)
#         else:
#             (node.nodeName, value) = ("?? "+node.nodeValue, "type="+str(node.nodeType))
#
#         if node.nodeType != node.TEXT_NODE and node.nodeType != node.COMMENT_NODE:
            label = self.rewriteText(node.nodeName)
            node_title = None
            item = QTreeWidgetItem(parent, [label, None])
            selection_widget = None
            # if node.nodeName == 'gui_qss_theme': # manage the dropbox for QSS Theme Name
            #     cmb = ComboBoxItem(None, ) # Used for QSS Themes
            #     cmb.addItems([""])
            if node.hasAttributes():
                for i in range(node.attributes.length):
                    attr_name = node.attributes.item(i).localName
                    attr_value = node.attributes.item(i).value
                    attritem = SyncingTreeWidgetItem(item, [self.rewriteText(attr_name), None])
                    attritem.setData(1, Qt.ItemDataRole.UserRole+1, node.attributes.item(i))
                    attritem.setFlags(attritem.flags() | Qt.ItemFlag.ItemIsEditable)
                    full_node_attr = '.'.join([node.nodeName, attr_name])

                    if node.nodeName in entitled_items and attr_name == entitled_items[node.nodeName]:
                        print("title for", label, "is", attr_value)
                        node_title = attr_value

                    if full_node_attr in boolean_attributes:
                        checkbox = CheckBoxItem(attritem, attr_value.lower()=="true")
                        self.configView.setItemWidget(attritem, 1, checkbox)

                    elif full_node_attr in choice_attributes:
                        choices = choice_attributes[full_node_attr](self.config, node)
                        combobox = ComboBoxItem(attritem, choices, attr_value)
                        print('choice_attributes:', full_node_attr, choices, attr_value)
                        self.configView.setItemWidget(attritem, 1, combobox)

                    else:
                        attritem.setData(1, Qt.ItemDataRole.DisplayRole, attr_value)

            if node_title:
                item.setData(0, Qt.ItemDataRole.DisplayRole, label + " " + node_title)

            if node.hasChildNodes():
                for elem in node.childNodes:
                    self.addTreeRows(item, elem)

if __name__=="__main__":
    Configuration.set_logfile("fpdb-log.txt")

    config = Configuration.Config()

    from PyQt6.QtWidgets import QApplication, QMainWindow
    app = QApplication([])
    main_window = QMainWindow()
    main_window.show()
    prefs = GuiPrefs(config, main_window)
    prefs.exec()
    app.exec()
