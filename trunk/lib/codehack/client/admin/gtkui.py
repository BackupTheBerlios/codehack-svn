# Copyright (C) 2004 Sridhar .R <sridhar@users.berlios.de>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software 
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

"""Team GTK+ GUI"""

from os.path import join
import gtk
import gobject
import time

from codehack import paths
from codehack.gwidget import GWidget, autoconnect_signals_in_class
from codehack import util
from codehack import validators
from codehack.client import dbedit, gui


READY = 'Ready'

class AdminGUI(gui.ClientGUI):
    
    GLADE_FILE = join(paths.DATA_DIR, 'glade', 'admin.glade')
    TOPLEVEL_WIDGET = 'wind_main'

    LBL_CONTEST_INFO = "<big><b>Contest is %srunning</b></big>"
    
    def __init__(self, perspective, userid, disconnect):
        super(AdminGUI, self).__init__(perspective, 
                        'Admin', userid, disconnect)

        # Logged in clients {userid=>(type, duration, duration_at)}
        self.clients = {}
        
        self._create_gui()
        self._initialize()
        
    def _create_gui(self):
        # Accounts
        wid = dbedit.DBEdit('users', self.call_remote, 'userid', 
                            lambda x: x['type'] == 'admin')
        wid.add_column('userid', str(), 'Userid', True)
        wid.add_column('passwd', str(), 'Password')
        wid.add_column('name', str(), 'Name', True)
        wid.add_column('emailid', str(), 'Email', True)
        wid.add_column('type', ('team', 'judge'), 'Type', True)
        wid.create(['type', 'userid', 'name', 'emailid'])
        self['vbox_accounts'].pack_start(wid)
        self.db_users = wid

        # Logged in clients 
        model = gtk.ListStore(str, str) # Userid, Type
        self['tv_logged'].set_model(model)
        for index, title in [(0,'Userid'), (1, 'Type')]:
            cell = gtk.CellRendererText()
            col = gtk.TreeViewColumn(title, cell, text=index)
            self['tv_logged'].append_column(col)
        self['tv_logged'].connect('cursor-changed', self._client_selected)
        self.clients_model = model
        

    def show(self):
        self.widget.show()
        self.db_users.show_all()

    def _initialize(self):
        # Get list of accounts
        self.db_users.populate()
        # Get contest time, duration ...
        def done(result):
            name, duration, age = result
            self._update_contest_ui(name, duration, age)
            self.call_remote('Getting logged in clients information', 
                         self.gotLoggedClients, 'get_clients')
        self.call_remote('Getting contest information', done, 
                         'get_contest_info')
    
    def gotLoggedClients(self, result):
        assert result
        self.clients = {}
        for userid, (typ, duration) in result.items():
            self.clients[userid] = (typ, duration, time.time())
        self._update_clients_ui()

    def contest_stopped(self):
        "Called by mind on stop of contest"
        self._update_contest_ui(None, None, 0)
        
    def _client_selected(self, tv, *args):
        mdl, iter = tv.get_selection().get_selected()
        userid = mdl.get_value(iter, 0)
        # Render info about userid
        typ, duration, duration_at = self.clients[userid]
        duration = duration + (time.time()-duration_at)
        self['lbl_client'].set_markup('Duration: %d seconds' % duration)
    
    def _update_clients_ui(self):
        """Update UI from self.clients"""
        model = self.clients_model
        model.clear()
        view_text = []
        [view_text.append((userid, typ)) for userid, (typ, duration, at) in \
                                    self.clients.items()]
        view_text.sort()
        for userid, typ in view_text:
            model.append((userid, typ))
        
    def _update_contest_ui(self, name, duration, age):
        """Updates UI based on contest info, duration is None if contest
        is not running"""
        if duration:
            self.contest_time(time.time()-age, duration)
        else:
            self.contest_time(0, None)
        self['lbl_contest'].set_markup(
                self.LBL_CONTEST_INFO % (not duration and 'NOT ' or ''))
        if name:
            self['lbl_title'].set_markup('<b>%s</b>' % name)
        ent = self['ent_duration']
        but_start = self['but_start_contest']
        but_stop = self['but_stop_contest']
        if duration:
            ent.set_text(str(duration))
        else:
            ent.set_text('')
        ent.set_sensitive(not duration)
        but_start.set_sensitive(not duration)
        but_stop.set_sensitive(not not duration)

        
    def on_but_start_contest__clicked(self, but, *args):
        duration = self['ent_duration'].get_text()
        try:
            duration = int(duration)
            if duration < 0:
                raise ValueError
        except ValueError:
            util.msg_dialog('Enter duration in seconds', gtk.MESSAGE_ERROR)
            self['ent_duration'].set_text('')
            return
        def done(result):
            name, duration, age = result
            # Start time
            self._update_contest_ui(name, duration, age)
        self.call_remote('Starting contest', done, 'start_contest', duration)

    def on_but_stop_contest__clicked(self, but, *args):
        def done(result):
            self._update_contest_ui(None, None, 0)
        self.call_remote('Stopping contest', done, 'stop_contest')

    def on_but_logout__clicked(self, *args):
        self.on_quit()
        print 'Hey, don\'t forget to come back!'
