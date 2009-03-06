#!/usr/bin/python

#Copyright 2008 Carl Gherardi
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
#In the "official" distribution you can find the license in
#agpl-3.0.txt in the docs folder of the package.

import Hand
import re
import sys
import threading
import traceback
import logging
from optparse import OptionParser
import os
import os.path
import xml.dom.minidom
import codecs
from decimal import Decimal
import operator
from xml.dom.minidom import Node
# from pokereval import PokerEval
import time
import datetime
import gettext

#from pokerengine.pokercards import *
# provides letter2name{}, letter2names{}, visible_card(), not_visible_card(), is_visible(), card_value(), class PokerCards
# but it's probably not installed so here are the ones we may want:
letter2name = {
    'A': 'Ace',
    'K': 'King',
    'Q': 'Queen',
    'J': 'Jack',
    'T': 'Ten',
    '9': 'Nine',
    '8': 'Eight',
    '7': 'Seven',
    '6': 'Six',
    '5': 'Five',
    '4': 'Four',
    '3': 'Trey',
    '2': 'Deuce'
    }

letter2names = {
    'A': 'Aces',
    'K': 'Kings',
    'Q': 'Queens',
    'J': 'Jacks',
    'T': 'Tens',
    '9': 'Nines',
    '8': 'Eights',
    '7': 'Sevens',
    '6': 'Sixes',
    '5': 'Fives',
    '4': 'Fours',
    '3': 'Treys',
    '2': 'Deuces'
    }

import gettext
gettext.install('myapplication')

class HandHistoryConverter(threading.Thread):

    def __init__(self, in_path = '-', out_path = '-', sitename = None, follow=False):
        threading.Thread.__init__(self)
        logging.info("HandHistory init called")
        
        # default filetype and codepage. Subclasses should set these properly.
        self.filetype  = "text"
        self.codepage  = "utf8"
        
        self.in_path = in_path
        self.out_path = out_path
        if self.out_path == '-':
            # write to stdout
            self.out_fh = sys.stdout
        else:
            self.out_fh = open(self.out_path, 'a') #TODO: append may be overly conservative.
        self.sitename  = sitename
        self.follow = follow
        self.compiledPlayers   = set()
        self.maxseats  = 10

    def __str__(self):
        #TODO : I got rid of most of the hhdir stuff.
        tmp = "HandHistoryConverter: '%s'\n" % (self.sitename)
        tmp = tmp + "\thhbase:     '%s'\n" % (self.hhbase)
        tmp = tmp + "\thhdir:      '%s'\n" % (self.hhdir)
        tmp = tmp + "\tfiletype:   '%s'\n" % (self.filetype)
        tmp = tmp + "\tinfile:     '%s'\n" % (self.file)
        tmp = tmp + "\toutfile:    '%s'\n" % (self.ofile)
        #tmp = tmp + "\tgametype:   '%s'\n" % (self.gametype[0])
        #tmp = tmp + "\tgamebase:   '%s'\n" % (self.gametype[1])
        #tmp = tmp + "\tlimit:      '%s'\n" % (self.gametype[2])
        #tmp = tmp + "\tsb/bb:      '%s/%s'\n" % (self.gametype[3], self.gametype[4])
        return tmp

    def run(self):
        if self.follow:
            for handtext in self.tailHands():
                self.processHand(handtext)
        else:
            handsList = self.allHands()
            logging.info("Parsing %d hands" % len(handsList))
            for handtext in handsList:
                self.processHand(handtext)
            if self.out_fh != sys.stdout:
                self.ouf_fh.close()

    def tailHands(self):
        """pseudo-code"""
        while True:
            ifile.tell()
            text = ifile.read()
            if nomoretext:
                wait or sleep
            else:
                ahand = thenexthandinthetext
                yield(ahand)

    def allHands(self):
        """Return a list of handtexts in the file at self.in_path"""
        self.readFile()
        self.obs = self.obs.strip()
        self.obs = self.obs.replace('\r\n', '\n')
        if self.obs == "" or self.obs == None:
            logging.info("Read no hands.")
            return
        return re.split(self.re_SplitHands,  self.obs)
        
    def processHand(self, handtext):
        gametype = self.determineGameType(handtext)
        logging.debug("gametype %s" % gametype)
        if gametype is None:
            return
        
        hand = None
        if gametype['game'] in ("hold", "omaha"):
            hand = Hand.HoldemOmahaHand(self, self.sitename, gametype, handtext)
        elif gametype['game'] in ("razz","stud","stud8"):
            hand = Hand.StudHand(self, self.sitename, gametype, handtext)
        
        if hand:
            hand.writeHand(self.out_fh)
        else:
            logging.info("Unsupported game type: %s" % gametype)
            # TODO: pity we don't know the HID at this stage. Log the entire hand?
            # From the log we can deduce that it is the hand after the one before :)
       
       
    def processFile(self):
        starttime = time.time()
        if not self.sanityCheck():
            print "Cowardly refusing to continue after failed sanity check"
            return
        self.readFile(self.file)
        if self.obs == "" or self.obs == None:
            print "Did not read anything from file."
            return

        self.obs = self.obs.replace('\r\n', '\n')
        self.gametype = self.determineGameType()
        if self.gametype == None:
            print "Unknown game type from file, aborting on this file."
            return
        self.hands = self.splitFileIntoHands()
        outfile = open(self.ofile, 'w')        
        for hand in self.hands:
            #print "\nDEBUG: Input:\n"+hand.handText
            self.readHandInfo(hand)
            
            self.readPlayerStacks(hand)
            #print "DEBUG stacks:", hand.stacks
            # at this point we know the player names, they are in hand.players
            playersThisHand = set([player[1] for player in hand.players])
            if playersThisHand <= self.players: # x <= y means 'x is subset of y'
                # we're ok; the regex should already cover them all.
                pass
            else:
                # we need to recompile the player regexs.
                self.players = playersThisHand
                self.compilePlayerRegexs()

            self.markStreets(hand)
            # Different calls if stud or holdem like
            if self.gametype[1] == "hold" or self.gametype[1] == "omahahi":
                self.readBlinds(hand)
                self.readButton(hand)
                self.readHeroCards(hand) # want to generalise to draw games
            elif self.gametype[1] == "razz" or self.gametype[1] == "stud" or self.gametype[1] == "stud8":
                self.readAntes(hand)
                self.readBringIn(hand)

            self.readShowdownActions(hand)
            
            # Read actions in street order
            for street in hand.streetList: # go through them in order
                print "DEBUG: ", street
                if hand.streets.group(street) is not None:
                    if self.gametype[1] == "hold" or self.gametype[1] == "omahahi":
                        self.readCommunityCards(hand, street) # read community cards
                    elif self.gametype[1] == "razz" or self.gametype[1] == "stud" or self.gametype[1] == "stud8":
                        self.readPlayerCards(hand, street)

                    self.readAction(hand, street)

                    
            self.readCollectPot(hand)
            self.readShownCards(hand)

            # finalise it (total the pot)
            hand.totalPot()
            self.getRake(hand)

            hand.writeHand(outfile)
            #if(hand.involved == True):
                #self.writeHand("output file", hand)
                #hand.printHand()
            #else:
                #pass #Don't write out observed hands

        outfile.close()
        endtime = time.time()
        print "Processed %d hands in %.3f seconds" % (len(self.hands), endtime - starttime)
    
    # These functions are parse actions that may be overridden by the inheriting class
    # This function should return a list of lists looking like:
    # return [["ring", "hold", "nl"], ["tour", "hold", "nl"]]
    # Showing all supported games limits and types
    
    def readSupportedGames(self): abstract

    # should return a list
    #   type  base limit
    # [ ring, hold, nl   , sb, bb ]
    # Valid types specified in docs/tabledesign.html in Gametypes
    def determineGameType(self): abstract

    # Read any of:
    # HID       HandID
    # TABLE     Table name
    # SB        small blind
    # BB        big blind
    # GAMETYPE  gametype
    # YEAR MON DAY HR MIN SEC   datetime
    # BUTTON    button seat number
    def readHandInfo(self, hand): abstract

    # Needs to return a list of lists in the format
    # [['seat#', 'player1name', 'stacksize'] ['seat#', 'player2name', 'stacksize'] [...]]
    def readPlayerStacks(self, hand): abstract
    
    def compilePlayerRegexs(self): abstract
    """Compile dynamic regexes -- these explicitly match known player names and must be updated if a new player joins"""
    
    # Needs to return a MatchObject with group names identifying the streets into the Hand object
    # so groups are called by street names 'PREFLOP', 'FLOP', 'STREET2' etc
    # blinds are done seperately
    def markStreets(self, hand): abstract

    #Needs to return a list in the format
    # ['player1name', 'player2name', ...] where player1name is the sb and player2name is bb, 
    # addtional players are assumed to post a bb oop
    def readBlinds(self, hand): abstract
    def readAntes(self, hand): abstract
    def readBringIn(self, hand): abstract
    def readButton(self, hand): abstract
    def readHeroCards(self, hand): abstract
    def readPlayerCards(self, hand, street): abstract
    def readAction(self, hand, street): abstract
    def readCollectPot(self, hand): abstract
    def readShownCards(self, hand): abstract
    
    # Some sites don't report the rake. This will be called at the end of the hand after the pot total has been calculated
    # an inheriting class can calculate it for the specific site if need be.
    def getRake(self, hand):
        hand.rake = hand.totalpot - hand.totalcollected #  * Decimal('0.05') # probably not quite right
    
    
    def sanityCheck(self):
        sane = False
        base_w = False
        #Check if hhbase exists and is writable
        #Note: Will not try to create the base HH directory
        if not (os.access(self.hhbase, os.W_OK) and os.path.isdir(self.hhbase)):
            print "HH Sanity Check: Directory hhbase '" + self.hhbase + "' doesn't exist or is not writable"
        else:
            #Check if hhdir exists and is writable
            if not os.path.isdir(self.hhdir):
                # In first pass, dir may not exist. Attempt to create dir
                print "Creating directory: '%s'" % (self.hhdir)
                os.mkdir(self.hhdir)
                sane = True
            elif os.access(self.hhdir, os.W_OK):
                sane = True
            else:
                print "HH Sanity Check: Directory hhdir '" + self.hhdir + "' or its parent directory are not writable"

        # Make sure input and output files are different or we'll overwrite the source file
        if(self.ofile == self.file):
            print "HH Sanity Check: output and input files are the same, check config"

        return sane

    # Functions not necessary to implement in sub class
    def setFileType(self, filetype = "text", codepage='utf8'):
        self.filetype = filetype
        self.codepage = codepage

    def splitFileIntoHands(self):
        hands = []
        self.obs = self.obs.strip()
        list = self.re_SplitHands.split(self.obs)
        list.pop() #Last entry is empty
        for l in list:
#           print "'" + l + "'"
            hands = hands + [Hand.Hand(self.sitename, self.gametype, l)]
        return hands

    def readFile(self):
        """Read in_path into self.obs or self.doc"""
        
        if(self.filetype == "text"):
            if self.in_path == '-':
                # read from stdin
                logging.debug("Reading stdin with %s" % self.codepage) # is this necessary? or possible? or what?
                in_fh = codecs.getreader('cp1252')(sys.stdin)
            else:
                logging.debug("Opening %s with %s" % (self.in_path, self.codepage))
                in_fh = codecs.open(self.in_path, 'r', self.codepage)
            self.obs = in_fh.read()
            in_fh.close()
        elif(self.filetype == "xml"):
            try:
                doc = xml.dom.minidom.parse(filename)
                self.doc = doc
            except:
                traceback.print_exc(file=sys.stderr)


    def getStatus(self):
        #TODO: Return a status of true if file processed ok
        return True

    def getProcessedFile(self):
        return self.ofile
