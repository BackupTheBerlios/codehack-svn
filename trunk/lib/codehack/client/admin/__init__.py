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

"""Admin GUI"""

from gtkui import AdminGUI

# Startup function
def run(perspective, mind_proxy, userid, disconnect):
    gui = AdminGUI(perspective, userid, disconnect)
    mind = Mind(gui)
    mind_proxy.set_target(mind)
    gui.show()


class Mind(object):
    """Mind object sent to twisted.cred in server
    
    Server calls methods in this class"""
    
    def __init__(self, gui):
        self.gui = gui
        
    def info(self, msg):
        """Message from server"""
        print '**Message:', msg

    def remote_client_loggedin(self, clients):
        self.gui.gotLoggedClients(clients)

    def remote_contest_stopped(self):
        self.gui.contest_stopped()

    def remote_contest_started(self):
        self.gui.contest_started()
