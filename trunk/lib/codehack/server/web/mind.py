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
Codehack Nevow Mind
"""

from jsutil import JSUtil


class NevowMind:

    """Mind wrapper for Nevow clients.

    mind - original mind
    avatar - avatar for this mind
    page - The corresponding page *class*

    see: auth.py for mechanism
    """

    def __init__(self, mind, avatar, page):
        self.mind = mind
        self.avatar = avatar
        # Page instances must be created by the MindAdaptor
        # Only mind and avatar is handled by twisted.spread
        self.page = page(self)  # The page
        self.name = None        # Contest name
        self.isrunning = False
        self.js = JSUtil(mind)

    def __getattr__(self, attr):
        # Fallback to original mind's attribute
        return getattr(self.mind, attr)

    def init(self):
        "Called when the mind is first created (on user logon)"
        pass

    # Mind methods
    #

    def contestStopped(self):
        self.mind.alert("Contest is stopped")
        self.js.reload()
     
    def contestStarted(self, name, details):
        self.mind.alert("Contest is started")
        self.js.reload()
