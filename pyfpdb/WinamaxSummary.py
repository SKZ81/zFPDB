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

from decimal_wrapper import Decimal
import datetime
# from bs4 import BeautifulSoup

from Exceptions import FpdbParseError
from HandHistoryConverter import *
import PokerStarsToFpdb
from TourneySummary import *


class WinamaxSummary(TourneySummary):
    
    # limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl' }
    # games = {                          # base, category
    #                            "Hold'em" : ('hold','holdem'),
    #                              'Omaha' : ('hold','omaha'),
    #                        "5 Card Omaha": ('hold','omaha5'), # TODO: check value
    #                  "5 Card Omaha Hi/Lo": ('hold','5omaha8'), # TODO: check value
    #                         "Omaha Hi/Lo": ('hold','omaha8'),
    #                         "7-Card Stud": ('stud','studhi'), # TODO: check value
    #                   "7-Card Stud Hi/Lo": ('stud','studhilo'), # TODO: check value
    #                                "Razz": ('stud','razz'), # TODO: check value
    #                     "2-7 Triple Draw": ('draw','27_3draw') # TODO: check value
    #           }

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP",     # legal ISO currency codes
                            'LS' : r"\$|\xe2\x82\xac|\u20ac" # legal currency symbols
                    }
    codepage = ("utf8", "cp1252")

    re_Identify = re.compile(r"Winamax\sPoker\s\-\sTournament\ssummary")
    
    re_SummaryTourneyInfo = re.compile(r"""
        \s:\s
        (?P<TOURNAME>.+)\((?P<TOURNO>[0-9]+)\)(\s-\sLate\sRegistration)?\s+
        (Player\s:\s(?P<PNAME>.*)\s+)?
        Buy-In\s:\s(?P<BUYIN>((?P<BIAMT>[\d\,.]+)(?P<BICURR>[%(LS)s])?[\s+]+)((?P<BIBOUNTY>[\d\,.]+)[%(LS)s\s+]+)?(?P<BIRAKE>[\d\,.]+)[%(LS)s\s+]+)\s+
        (Rebuy\scost\s:\s(?P<REBUY>(?P<REBUYAMT>.+)\s\+\s(?P<REBUYRAKE>.+))\s+)?
        (Addon\scost\s:\s(?P<ADDON>(?P<ADDONAMT>.+)\s\+\s(?P<ADDONRAKE>.+))\s+)?
        (Your\srebuys\s:\s(?P<PREBUYS>\d+)\s+)?
        (Your\saddons\s:\s(?P<PADDONS>\d+)\s+)?
        Registered\splayers\s:\s(?P<ENTRIES>[0-9]+)\s+
        (Total\srebuys\s:\s\d+\s+)?
        (Total\saddons\s:\s\d+\s+)?
        (Mode\s:\s(?P<TMODE>[^\s]+)\s+)?
        (Type\s:\s(?P<TTYPE>[^\s]+)\s+)?
        (Speed\s:\s(?P<SPEED>.+)?\s+)?
        (Flight\sID\s:\s.+\s+)?
        (Levels\s:\s.+\s+)?
        Prizepool\s:\s(?P<PRIZEPOOL>[.0-9%(LS)s]+)\s+
        Tournament\sstarted\s(?P<DATETIME>[0-9]{4}\/[0-9]{2}\/[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}\sUTC)\s+
        You\splayed\s(?P<PLAYTIME>(((?P<PLAYTIME_H>\d+)h\s)?((?P<PLAYTIME_M>\d+)min\s)?(?P<PLAYTIME_S>\d+)s))\s+
        You\sfinished\sin\s(?P<RANK>[0-9]+)(st|nd|rd|th)\splace\s+
        (You\swon\s(?P<WINNINGS>[.0-9%(LS)s]+)?(\s\+\s)?(Bounty\s(?P<WINNINGS_BOUNTY>[.0-9%(LS)s]+))?)?
        """ % substitutions ,re.VERBOSE|re.MULTILINE)

    # re_DateTime = re.compile(r"\[(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")

    @staticmethod
    def getSplitRe(self, head):
        return self.re_Identify

    def parseSummary(self):
        m = self.re_SummaryTourneyInfo.search(self.summaryText)
        if m == None:
            tmp = self.summaryText[0:200]
            log.error(_("WinamaxSummary.parseSummaryFromFile: '%s'") % tmp)
            raise FpdbParseError

        mg = m.groupdict()

        if 'ENTRIES' in mg:
            self.entries   = mg['ENTRIES']
        if 'PRIZEPOOL' in mg:
            self.prizepool = int(100*self.convert_to_decimal(mg['PRIZEPOOL']))
        if 'DATETIME' in mg:
            self.startTime = datetime.datetime.strptime(mg['DATETIME'], "%Y/%m/%d %H:%M:%S UTC")
            if 'PLAYTIME' in mg:
                self.endTime = self.startTime + datetime.timedelta(
                    hours=int(mg['PLAYTIME_H']) if 'PLAYTIME_H' in mg and mg['PLAYTIME_H'] is not None else 0,
                    minutes=int(mg['PLAYTIME_M']) if 'PLAYTIME_M' in mg and mg['PLAYTIME_M'] is not None else 0,
                    seconds=int(mg['PLAYTIME_S']))

        #FIXME: buyinCurrency and currency not detected
        if 'BICURR' in mg:

            self.buyinCurrency = mg['BICURR']
            self.currency  = mg['BICURR']

        if 'BUYIN' in mg:
            if mg['BUYIN'].find(u"€")!=-1:
                self.buyinCurrency="EUR"
            # elif mg['BUYIN'].find("FPP")!=-1:
            #     self.buyinCurrency="WIFP"
            # elif mg['BUYIN'].find("Free")!=-1:
            #     self.buyinCurrency="WIFP"
            else:
                self.buyinCurrency="play"
            rake = mg['BIRAKE'].strip('\r')
            self.buyin = int(100*self.convert_to_decimal(mg['BIAMT']))
            self.fee   = int(100*self.convert_to_decimal(rake))

            if self.buyin == 0 and self.fee == 0:
                self.buyinCurrency = "FREE"
                
        if 'REBUY' in mg and mg['REBUY'] != None:
            self.isRebuy   = True
            rebuyrake = mg['REBUYRAKE'].strip('\r')
            rebuyamt = int(100*self.convert_to_decimal(mg['REBUYAMT']))
            rebuyfee   = int(100*self.convert_to_decimal(rebuyrake))
            self.rebuyCost = rebuyamt + rebuyfee
        if 'ADDON' in mg and mg['ADDON'] != None:
            self.isAddOn = True
            addonrake = mg['ADDONRAKE'].strip('\r')
            addonamt = int(100*self.convert_to_decimal(mg['ADDONAMT']))
            addonfee   = int(100*self.convert_to_decimal(addonrake))
            self.addOnCost = addonamt + addonfee

        if 'TOURNO' in mg:
            self.tourNo = mg['TOURNO']
        if 'TOURNAME' in mg:
            self.tourneyName = mg['TOURNAME']
        #self.maxseats  =
        if int(self.entries) <= 10: #FIXME: obv not a great metric
            self.isSng     = True
        if 'TTYPE' in mg and mg['TTYPE'] != None:
            if mg['TTYPE']=='sngType':
                self.isSng = True
        if 'SPEED' in mg and mg['SPEED'] != None:
            if mg['SPEED']=='turbo':
                self.speed = 'Hyper'
            elif mg['SPEED']=='semiturbo':
                self.speed = 'Turbo'
            
        if 'PNAME' in mg and mg['PNAME'] is not None:
            name = mg['PNAME'].strip('\r')
            rank = mg['RANK']
            if rank!='...':
                rank = int(mg['RANK'])
                winnings = 0
                rebuyCount = None
                addOnCount = None
                koCount = None
    
                if 'WINNINGS' in mg and mg['WINNINGS'] != None:
                    if mg['WINNINGS'].find(u"€")!=-1:
                        self.currency="EUR"
                    elif mg['WINNINGS'].find("FPP")!=-1:
                        self.currency="WIFP"
                    elif mg['WINNINGS'].find("Free")!=-1:
                        self.currency="WIFP"
                    else:
                        self.currency="play"
                    winnings = int(100*self.convert_to_decimal(mg['WINNINGS']))
                if 'PREBUYS' in mg and mg['PREBUYS'] != None:
                    rebuyCount = int(mg['PREBUYS'])
                if 'PADDONS' in mg and mg['PADDONS'] != None:
                    addOnCount = int(mg['PADDONS'])
    
                #print "DEBUG: addPlayer(%s, %s, %s, %s, %s, %s, %s)" %(rank, name, winnings, self.currency, rebuyCount, addOnCount, koCount)
                self.addPlayer(rank, name, winnings, self.currency, rebuyCount, addOnCount, koCount)

    def convert_to_decimal(self, string):
        print("convert_to_decimal:", string)
        dec = self.clearMoneyString(string)
        dec = Decimal(dec)
        return dec

