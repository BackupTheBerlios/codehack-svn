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
Codehack Nevow Webserver package - Base module
"""

from twisted.cred import portal
from nevow import inevow

from codehack.server import auth
from codehack.server import db


import page
import team, admin

class WebRealm(auth.CodehackRealm):
    """A simple implementor of cred's IRealm.
       For web, this gives us the LoggedIn page.
    """
    __implements__ = portal.IRealm
    interface = inevow.IResource
    
    mind_adaptor = {
        db.USER_TEAM: team.NevowTeamMind,
        db.USER_ADMIN: admin.NevowAdminMind,
        db.USER_JUDGE: None
    }
    
    def requestAnonymousAvatar(self, mind):
        return self.interface, page.LoginPage(), lambda: None

    def requestThisAvatar(self, avatarId, mind, remove_f):
        def logout():
            resc.logout()
            remove_f()
        return self.interface, mind.page(mind), logout

