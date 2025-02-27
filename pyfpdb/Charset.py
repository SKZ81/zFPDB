#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2010-2011 Mika Bostrom
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

# import L10n
# _ = L10n.get_translation()
# Settings
import Configuration

def to_utf8(s):
    return s.encode('utf-8')

def to_gui(s):
    return s.encode(Configuration.LOCALE_ENCODING, errors='replace').decode(Configuration.LOCALE_ENCODING)
