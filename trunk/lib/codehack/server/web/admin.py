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

"""
Admin Web Mind
"""


class NevowAdminMind(object):
    
    def __init__(self, mind, avatar):
        self.mind = mind
        self.avatar = avatar

    def init(self):
        pass
        
    def info(self, msg):
        """Message from server"""
        pass

    def liveClients(self, clients):
        self.mind.sendScript('alert("liveClients");')
        # self.gui.gotLoggedClients(clients)

    def contestStopped(self):
        pass
        # self.gui.contestStopped()

    def contestStarted(self):
        pass
        # self.gui.contestStarted()
        
