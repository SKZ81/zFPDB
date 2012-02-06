#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Mucked.py

Mucked cards display for FreePokerTools HUD.
"""
#    Copyright 2008-2011,  Ray E. Barker
#    
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

#    to do

#    Standard Library modules
import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("hud")

#    pyGTK modules
import gtk
import gobject

#    FreePokerTools modules
import Card
import Popup

class Aux_Window(object):
    def __init__(self, hud, params, config):
        self.hud     = hud
        self.params  = params
        self.config  = config

#   Override these methods as needed
    def update_data(self, *args): pass
    def update_gui(self, *args):  pass
    def create(self, *args):      pass
    def relocate(self, *args):    pass
    def save_layout(self, *args): pass
    def update_player_positions(self, *args): pass
    def destroy(self):
        try:
            self.container.destroy()
        except:
            pass

############################################################################
#    Some utility routines useful for Aux_Windows
#
    def get_card_images(self, card_width=30, card_height=42):

        card_images = 53 * [0]
        suits = ('s', 'h', 'd', 'c')
        ranks = (14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2)
        deckimg = self.params['deck']
        try:
            pb = gtk.gdk.pixbuf_new_from_file(self.config.execution_path(deckimg))
        except:
            #FIXME: this can't be right? /usr will not exist on windows
            stockpath = '/usr/share/python-fpdb/' + deckimg
            pb = gtk.gdk.pixbuf_new_from_file(stockpath)
        
        for j in range(0, 13):
            for i in range(0, 4):
                card_images[Card.cardFromValueSuit(ranks[j], suits[i])] = self.cropper(pb, i, j, card_width, card_height)
#    also pick out a card back and store in [0]
        card_images[0] = self.cropper(pb, 2, 13, card_width, card_height)
        return(card_images)
#   cards are 30 wide x 42 high

    def cropper(self, pb, i, j, card_width, card_height):
        """Crop out a card image given an FTP deck and the i, j position."""
        cropped_pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, pb.get_has_alpha(),
                                    pb.get_bits_per_sample(), 30, 42)
        pb.copy_area(30*j, 42*i, 30, 42, cropped_pb, 0, 0)

        if card_height == 42:
            """ no scaling """
            return cropped_pb
        else:
            """Apply scaling to the the 30w x 42h card image """
            scaled_pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, pb.get_has_alpha(),
                                        pb.get_bits_per_sample(),
                                        card_width, card_height)
            scaled_card = cropped_pb.scale_simple(card_width, card_height,
                                                gtk.gdk.INTERP_BILINEAR)

            scaled_card.copy_area(0, 0, self.card_width, self.card_height,
                                        scaled_pb, 0, 0)
            return scaled_pb

    def has_cards(self, cards):
        """Returns the number of cards in the list."""
        n = 0
        for c in cards:
            if c != None and c > 0: n = n + 1
        return n

    def get_id_from_seat(self, seat):
        """Determine player id from seat number, given stat_dict."""
        for id, dict in self.hud.stat_dict.iteritems():
            if seat == dict['seat']:
                return id
        return None
        
class Stud_mucked(Aux_Window):
    def __init__(self, hud, config, params):

        self.hud     = hud       # hud object that this aux window supports
        self.config  = config    # configuration object for this aux window to use
        self.params  = params    # hash aux params from config

        try:
            site_params = self.config.get_site_parameters(self.hud.site)
            self.hero = site_params['screen_name']
        except:
            self.hero = ''

        self.mucked_list   = Stud_list(self, params, config, self.hero)
        self.mucked_cards  = Stud_cards(self, params, config)
        self.mucked_list.mucked_cards = self.mucked_cards

    def create(self):

        self.container = gtk.Window() 
        self.vbox = gtk.VBox()
        self.container.add(self.vbox)
        self.container.set_title(self.hud.table.name)

        self.mucked_list.create(self.vbox)
        self.mucked_cards.create(self.vbox)
        self.container.show_all()

    def update_data(self, new_hand_id, db_connection):
#    uncomment next line when action is available in the db
#        self.mucked_cards.update_data(new_hand_id, db_connection)
        self.mucked_list.update_data(new_hand_id, db_connection)
        
    def update_gui(self, new_hand_id):
        self.mucked_cards.update_gui(new_hand_id)
        self.mucked_list.update_gui(new_hand_id)
        
class Stud_list:
    def __init__(self, parent, params, config, hero):

        self.parent     = parent
        self.params  = params
        self.config  = config
        self.hero    = hero

    def create(self, container):
#       set up a scrolled window to hold the listbox
        self.container  = container
        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        self.container.add(self.scrolled_window)

#       create a ListStore to use as the model
        self.liststore = gtk.ListStore(str, str, str, str)
        self.treeview = gtk.TreeView(self.liststore)
        self.tvcolumn0 = gtk.TreeViewColumn('HandID')
        self.tvcolumn1 = gtk.TreeViewColumn('Cards')
        self.tvcolumn2 = gtk.TreeViewColumn('Net')
        self.tvcolumn3 = gtk.TreeViewColumn('Winner')

#       add tvcolumn to treeview
        self.treeview.append_column(self.tvcolumn0)
        self.treeview.append_column(self.tvcolumn1)
        self.treeview.append_column(self.tvcolumn2)
        self.treeview.append_column(self.tvcolumn3)

#       create a CellRendererText to render the data
        self.cell = gtk.CellRendererText()

        # add the cell to the tvcolumn and allow it to expand
        self.tvcolumn0.pack_start(self.cell, True)
        self.tvcolumn1.pack_start(self.cell, True)
        self.tvcolumn2.pack_start(self.cell, True)
        self.tvcolumn3.pack_start(self.cell, True)
        self.tvcolumn0.add_attribute(self.cell, 'text', 0)
        self.tvcolumn1.add_attribute(self.cell, 'text', 1)
        self.tvcolumn2.add_attribute(self.cell, 'text', 2)
        self.tvcolumn3.add_attribute(self.cell, 'text', 3)
#        resize the cols if nec
        self.tvcolumn0.set_resizable(True)
        self.tvcolumn1.set_resizable(True)
        self.tvcolumn2.set_resizable(True)
        self.tvcolumn3.set_resizable(True)
        self.treeview.connect("row-activated", self.activated_event)

        self.scrolled_window.add_with_viewport(self.treeview)

    def activated_event(self, path, column, data=None):
        pass
#        sel = self.treeview.get_selection()
#        (model, iter)  = sel.get_selected()
#        self.mucked_cards.update_data(model.get_value(iter, 0))
#        self.mucked_cards.update_gui(model.get_value(iter, 0))
        
    def update_data(self, new_hand_id, db_connection):
        """Updates the data needed for the list box."""

#        db_connection = Database.Database(self.config, 'fpdb', '')
        self.winners = db_connection.get_winners_from_hand(new_hand_id)
        pot = 0
        winners = ''
        for player in self.winners.keys():
            pot = pot + int(self.winners[player])
            if not winners == '':
                winners = winners + ", "
            winners = winners + player
        pot_dec = "%.2f" % (float(pot)/100)

        hero_cards = self.get_hero_cards(self.parent.hero, self.parent.hud.cards)
        self.info_row = ((new_hand_id, hero_cards, pot_dec, winners), )

    def get_hero_cards(self, hero, cards):
        """Formats the hero cards for inclusion in the tree."""
        trans = ('0', 'A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A')
        if hero == '':
            return "xxxxxx"
        else:
#    find the hero's seat from the stat_dict
            for stat in self.parent.hud.stat_dict.itervalues():
                if stat['screen_name'] == hero:
                    return Card.valueSuitFromCard(self.parent.hud.cards[stat['seat']][0]) +\
                           Card.valueSuitFromCard(self.parent.hud.cards[stat['seat']][1]) +\
                           Card.valueSuitFromCard(self.parent.hud.cards[stat['seat']][2])
        return "xxxxxx"
            
    def update_gui(self, new_hand_id):
        iter = self.liststore.append(self.info_row[0]) 
        sel = self.treeview.get_selection()
        #sel.select_iter(iter)

        vadj = self.scrolled_window.get_vadjustment()
        #vadj.set_value(vadj.upper)

class Stud_cards:
    def __init__(self, parent, params, config):

        self.parent    = parent
        self.params  = params
        self.config  = config
#        self.db_name = db_name

        self.card_images = self.parent.get_card_images()
        self.seen_cards = {}
        self.grid_contents = {}
        self.eb = {}

        self.rows = 8
        self.cols = 7

    def create(self, container):
        self.container  = container
        self.grid = gtk.Table(self.rows, self.cols + 4, homogeneous = False)

        for r in range(0, self.rows):
            for c in range(0, self.cols):
                self.seen_cards[(c, r)] = gtk.image_new_from_pixbuf(self.card_images[(0)])
                self.eb[(c, r)]= gtk.EventBox()

#    set up the contents for the cells
        for r in range(0, self.rows):
            self.grid_contents[( 0, r)] = gtk.Label("%d" % (r + 1))
            self.grid_contents[( 1, r)] = gtk.Label("player %d" % (r + 1))
            self.grid_contents[( 1, r)].set_property("width-chars", 12)
            self.grid_contents[( 4, r)] = gtk.Label("-")
            self.grid_contents[( 9, r)] = gtk.Label("-")
            self.grid_contents[( 2, r)] = self.eb[( 0, r)]
            self.grid_contents[( 3, r)] = self.eb[( 1, r)]
            self.grid_contents[( 5, r)] = self.eb[( 2, r)]
            self.grid_contents[( 6, r)] = self.eb[( 3, r)]
            self.grid_contents[( 7, r)] = self.eb[( 4, r)]
            self.grid_contents[( 8, r)] = self.eb[( 5, r)]
            self.grid_contents[(10, r)] = self.eb[( 6, r)]
            for c in range(0, self.cols):
                self.eb[(c, r)].add(self.seen_cards[(c, r)])
            
#    add the cell contents to the table
        for c in range(0, self.cols + 4):
            for r in range(0, self.rows):
                self.grid.attach(self.grid_contents[(c, r)], c, c+1, r, r+1, xpadding = 1, ypadding = 1)
                
        self.container.add(self.grid)

    def update_data(self, new_hand_id, db_connection):
        self.tips = []
        action = db_connection.get_action_from_hand(new_hand_id)
        for street in action:
            temp = ''
            for act in street:
                temp = temp + act[0] + " " + act[1] + "s "
                if act[2] > 0:
                    if act[2]%100 > 0:
                        temp = temp + "%4.2f\n" % (float(act[2])/100)
                    else:
                        temp = temp + "%d\n" % (act[2]/100) 
                else:
                    temp = temp + "\n"
            self.tips.append(temp)

    def update_gui(self, new_hand_id):
        self.clear()
        for c, cards in self.parent.hud.cards.iteritems():
            if c == 'common': continue
            self.grid_contents[(1, c - 1)].set_text(self.get_screen_name(c))
            for i in ((0, cards[0]), (1, cards[1]), (2, cards[2]), (3, cards[3]), 
                      (4, cards[4]), (5, cards[5]), (6, cards[6])):
                if not i[1] == 0:
                    self.seen_cards[(i[0], c - 1)]. \
                        set_from_pixbuf(self.card_images[i[1]])
##    action in tool tips for 3rd street cards
        for c in (0, 1, 2):
            for r in range(0, self.rows):
                #self.eb[(c, r)].set_tooltip_text(self.tips[0])
                pass

#    action in tools tips for later streets
        round_to_col = (0, 3, 4, 5, 6)
        #for round in range(1, len(self.tips)):
        #    for r in range(0, self.rows):
        #        self.eb[(round_to_col[round], r)].set_tooltip_text(self.tips[round])

    def get_screen_name(self, seat_no):
        """Gets and returns the screen name from stat_dict, given seat number."""
        for k in self.parent.hud.stat_dict.keys():
            if self.parent.hud.stat_dict[k]['seat'] == seat_no:
                return self.parent.hud.stat_dict[k]['screen_name']
        return _("No Name")

    def clear(self):
        for r in range(0, self.rows):
            self.grid_contents[(1, r)].set_text("             ")
            for c in range(0, 7):
                self.seen_cards[(c, r)].set_from_pixbuf(self.card_images[0])
                self.eb[(c, r)].set_tooltip_text('')

class Seat_Window(gtk.Window):
    """Subclass gtk.Window for the seat windows."""
    def __init__(self, aw = None, seat = None):
        super(Seat_Window, self).__init__()
        self.aw = aw
        self.seat = seat
        self.set_skip_taskbar_hint(True)  # invisible to taskbar
        self.set_gravity(gtk.gdk.GRAVITY_STATIC)
        self.set_decorated(False)    # kill titlebars
        self.set_focus(None)
        self.set_focus_on_map(False)
        self.set_accept_focus(False)
        self.connect("configure_event", self.aw.configure_event_cb, self.seat)


    def button_press_cb(self, widget, event, *args):
        """Handle button clicks in the event boxes."""
        #double-click events should be avoided
        # these are not working reliably on windows GTK 2.24 toolchain

        if event.button == 1:   # left button event
            self.button_press_left(widget, event, *args)
        elif event.button == 2:   # middle button event
            self.button_press_middle(widget, event, *args)
        elif event.button == 3:   # right button event
            self.button_press_right(widget, event, *args)


    def button_press_left(self, widget, event, *args): #move window
        self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
        
    def button_press_middle(self, widget, event, *args): pass 
  
    def button_press_right(self, widget, event, *args):  #show pop up
        pu_to_run = widget.get_ancestor(gtk.Window).aw.config.popup_windows[widget.aw_popup].pu_class
        Popup.__dict__[pu_to_run](seat = widget.aw_seat,
            stat_dict = widget.stat_dict,
            win = widget.get_ancestor(gtk.Window),
            pop = widget.get_ancestor(gtk.Window).aw.config.popup_windows[widget.aw_popup])
    
class Aux_Seats(Aux_Window):
    """A super class to display an aux_window or a stat block at each seat."""

    def __init__(self, hud, config, params):
        self.hud     = hud       # hud object that this aux window supports
        self.config  = config    # configuration object for this aux window to use
        self.params  = params    # dict aux params from config
        self.positions = {}      # dict of window positions
        self.displayed = False   # the seat windows are displayed
        self.uses_timer = False  # the Aux_seats object uses a timer to control hiding
        self.timer_on = False    # bool = Ture if the timeout for removing the cards is on

        self.aw_class_window = Seat_Window

#    placeholders that should be overridden--so we don't throw errors
    def create_contents(self): pass
    def create_common(self, x, y): pass
    def update_contents(self): pass

    def update_player_positions(self):
        # self.adj does not exist until .create() has been run
        try:
            adj = self.adj
        except AttributeError:
            return

        for i in (range(1, self.hud.max + 1)):
            (x, y) = self.hud.layout.location[self.adj[i]]
            self.positions[i] = self.card_positions(x, self.hud.table.x, y , self.hud.table.y)
            self.m_windows[i].move(self.positions[i][0], self.positions[i][1])

    def update_common_position(self):
        (x, y) = self.hud.layout.common
        self.positions["common"] = self.card_positions(x, self.hud.table.x, y , self.hud.table.y)
        self.m_windows["common"].move(self.positions["common"][0], self.positions["common"][1])
        
    def create(self):

        self.adj = self.hud.adj_seats(0, self.config)  # move adj_seats to aux and get rid of it in Hud.py
        
        self.m_windows = {}      # windows to put the card/hud items in

        for i in (range(1, self.hud.max + 1) + ['common']):   
            if i == 'common':
#    The common window is different from the others. Note that it needs to 
#    get realized, shown, topified, etc. in create_common
                (x, y) = self.hud.layout.common
                self.m_windows[i] = self.create_common(x, y)
            else:
                (x, y) = self.hud.layout.location[self.adj[i]]
                self.m_windows[i] = self.aw_class_window(self, i)
                self.m_windows[i].set_decorated(False)
                self.m_windows[i].set_property("skip-taskbar-hint", True)
                self.m_windows[i].set_focus_on_map(False)
                self.m_windows[i].set_focus(None)
                self.m_windows[i].set_accept_focus(False)
                self.m_windows[i].connect("configure_event", self.configure_event_cb, i)
                self.positions[i] =  self.card_positions(x, self.hud.table.x, y , self.hud.table.y)
                self.m_windows[i].move(self.positions[i][0], self.positions[i][1])
                if self.params.has_key('opacity'):
                    self.m_windows[i].set_opacity(float(self.params['opacity']))

#    the create_contents method is supplied by the subclass
#      for hud's this is probably Aux_Hud.stat_window
            self.create_contents(self.m_windows[i], i)

            self.m_windows[i].realize()
            self.hud.table.topify(self.m_windows[i])
            self.m_windows[i].show_all()
            if self.uses_timer:
                self.m_windows[i].hide()


    def card_positions(self, x, table_x, y, table_y):
        _x = int(x) + int(table_x)
        _y = int(y) + int(table_y)
        return (_x, _y)


    def update_gui(self, new_hand_id):
        """Update the gui, LDO."""

        for i in self.m_windows.keys():
            self.update_contents(self.m_windows[i], i)
        #reload latest player positions, in case another aux has changed them
        #these lines cause the propagation of block-moves across
        #tables without the need to kill the hud
        self.update_player_positions()
        self.update_common_position()

#   Methods likely to be of use for any Seat_Window implementation
    def destroy(self):
        """Destroy all of the seat windows."""
        try:
            for i in self.m_windows.keys():
                self.m_windows[i].destroy()
                del(self.m_windows[i])
        except AttributeError:
            pass

#   Methods likely to be useful for mucked card windows (or similar) only
    def hide(self):
        """Hide the seat windows."""
        for (i, w) in self.m_windows.iteritems():
            if w is not None: w.hide()
        self.displayed = False

    def save_layout(self, *args):
        """Save new layout back to the aux element in the config file."""
        """ this method is  overridden in the specific aux because
        the HUD's controlling stat boxes set the seat positions and
        the mucked card aux's control the common location
        This class method would only be valid for an aux which has full control
        over all seat and common locations
        """

        print ("Aux_Seats.save_layout called - this shouldn't happen")
        print ("save_layout method should be handled in the aux")


    def configure_event_cb(self, widget, event, i, *args):
        """This method updates the current location for each statblock"""
        if (i): 
            new_abs_position = widget.get_position() #absolute value of the new position
            new_rel_position = (new_abs_position[0]-self.hud.table.x, new_abs_position[1]-self.hud.table.y)
            #if i != "common" and int(i) == 5:
            #    print i, self.hud.table.x, self.hud.table.y, new_abs_position, new_rel_position
            self.positions[i] = new_abs_position     #write this back to our map
            if i != "common":
                self.hud.layout.location[self.adj[i]] = new_rel_position #update the hud-level dict, so other aux can be told
            else:
                self.hud.layout.common = new_rel_position


class Flop_Mucked(Aux_Seats):
    """Aux_Window class for displaying mucked cards for flop games."""

    def __init__(self, hud, config, params):
        super(Flop_Mucked, self).__init__(hud, config, params)
                
        self.card_height = int(self.params['card_ht'])
        if (self.card_height > 84): self.card_height = 84
        if (self.card_height < 21): self.card_height = 21
        self.card_width = int(30. * (self.card_height / 42.))
        
        self.card_images = self.get_card_images(self.card_width, self.card_height)
        self.uses_timer = True  # this Aux_seats object uses a timer to control hiding

    def create_common(self, x, y):
        "Create the window for the board cards and do the initial population."
        w = self.aw_class_window(self, "common")
        w.set_decorated(False)
        w.set_property("skip-taskbar-hint", True)
        w.set_focus_on_map(False)
        w.set_focus(None)
        w.set_accept_focus(False)
        w.connect("configure_event", self.configure_event_cb, "common")
        #self.positions["common"] = self.card_positions((x * self.hud.table.width) / 1000, self.hud.table.x, (y * self.hud.table.height) /1000, self.hud.table.y)
        self.positions["common"] = self.card_positions(x, self.hud.table.x, y, self.hud.table.y)
        w.move(self.positions["common"][0], self.positions["common"][1])
        if self.params.has_key('opacity'):
            w.set_opacity(float(self.params['opacity']))
#        self.create_contents(w, "common")
        return w

    def create_contents(self, container, i):
        """Create the widgets for showing the contents of the Aux_seats window."""
        container.eb = gtk.EventBox()
        container.eb.connect("button_press_event", self.button_press_cb)
        container.add(container.eb)
        container.seen_cards = gtk.image_new_from_pixbuf(self.card_images[0])
        container.eb.add(container.seen_cards)

    def update_contents(self, container, i):

        if not self.hud.cards.has_key(i): return
        
        cards = self.hud.cards[i]
        n_cards = self.has_cards(cards)
        if n_cards > 1:

#    scratch is a working pixbuf, used to assemble the image
            scratch = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8,
                                        self.card_width * n_cards,
                                        self.card_height)
            x = 0 # x coord where the next card starts in scratch
            for card in cards:
#    concatenate each card image to scratch
                if card == None or card ==0:
                    break

                self.card_images[card].copy_area(0, 0, 
                                        self.card_width, self.card_height,
                                        scratch, x, 0)
                x = x + self.card_width
            if container is not None:
                container.seen_cards.set_from_pixbuf(scratch)
                container.resize(1,1)
                container.move(self.positions[i][0], self.positions[i][1])   # here is where I move back
                container.show()

            self.displayed = True
            if i != "common":
                id = self.get_id_from_seat(i)
                # sc: had KeyError here with new table so added id != None test as a guess:
                if id is not None:
                    self.m_windows[i].eb.set_tooltip_text(self.hud.stat_dict[id]['screen_name'])
                    
    def save_layout(self, *args):
        """Save new common position back to the layout element in the config file."""
        new_locs = {}
        for (i, pos) in self.positions.iteritems():
            if i == 'common':
                new_locs[i] = ((pos[0] - self.hud.table.x), (pos[1] - self.hud.table.y))
            else:
                #seat positions are owned by the aux controlling the stat block
                # we share the locations from that aux, so don't write-back their
                # locations here
                pass

        self.config.save_layout_set(self.hud.layout_set, self.hud.max, new_locs, width=None, height=None)

    def update_gui(self, new_hand_id):
        """Prepare and show the mucked cards."""
        if self.displayed: self.hide()

#   See how many players showed a hand. Skip if only 1 shows (= hero)
        n_sd = 0
        for (i, cards) in self.hud.cards.iteritems():
            n_cards = self.has_cards(cards)
            if n_cards > 0 and i != 'common':
                n_sd = n_sd + 1
        if n_sd < 2: 
            return

        super(Flop_Mucked, self).update_gui(new_hand_id)

        if self.displayed and float(self.params['timeout']) > 0:
            self.timer_on = True
            gobject.timeout_add(int(1000*float(self.params['timeout'])), self.timed_out)

    def timed_out(self):
#    this is the callback from the timeout

#    if timer_on is False the user has cancelled the timer with a click
#    so just return False to cancel the timer
        if not self.timer_on:
            return False
        else:
            self.hide()
            return False

    def button_press_cb(self, widget, event, *args):
        """Handle button clicks in the event boxes."""

#    shift-any button exposes all the windows and turns off the timer
        if event.state & gtk.gdk.SHIFT_MASK:
            self.timer_on = False
            self.expose_all()
            return

        if event.button == 3:   # right button event
            pass

        elif event.button == 2:   # middle button event
            if self.timer_on == True:
                self.timer_on = False
            else:
                self.timer_on = False
                self.hide()

        elif event.button == 1:   # left button event
            window = widget.get_parent()
            window.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def expose_all(self):
        for (i, cards) in self.hud.cards.iteritems():
            self.m_windows[i].show()
            self.m_windows[i].move(self.positions[i][0], self.positions[i][1])   # here is where I move back
            self.displayed = True

