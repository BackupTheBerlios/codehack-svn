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

"""Team GUI"""

from gtkui import TeamGUI

# Startup function
def run(perspective, mind_proxy, userid, disconnect):
    gui = TeamGUI(perspective, userid, disconnect)
    mind = Mind(gui)
    mind_proxy.setTarget(mind)
    gui.widget.show_all()


class Mind(object):
    """Mind object sent to twisted.cred in server
    
    Server calls methods in this class"""
    
    def __init__(self, gui):
        self.gui = gui
        
    def remote_info(self, msg):
        """Message from server"""
        print '**Message:', msg

    def remote_submissionResult(self, r):
        self.gui.showSubmissionResult(r['problem'], r['language'], r['ts'], r['result'])

    def remote_contestStopped(self):
        self.gui.contestStopped()

    def remote_contestStarted(self, name, details):
        self.gui.contestStarted(name, details)
