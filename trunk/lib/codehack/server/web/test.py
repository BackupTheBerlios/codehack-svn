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
Nevow Test - REMOVE or rename later
"""

from twisted.cred import portal
from twisted.cred import checkers

from nevow import loaders
from nevow import rend
from nevow import tags as T
from nevow import liveevil
from nevow import inevow
from nevow import guard

### Authentication
def noLogout():
    return None

class WebRealm:
    """A simple implementor of cred's IRealm.
       For web, this gives us the LoggedIn page.
    """
    __implements__ = portal.IRealm
 
    def requestAvatar(self, avatarId, mind, *interfaces):
        for iface in interfaces:
            if iface is inevow.IResource:
                if avatarId is checkers.ANONYMOUS:
                    # Show the Login page
                    resc = MainPage()
                    resc.realm = self
                    return (inevow.IResource, resc, noLogout)
                else:
                    # Show LoggedinPage through MainPage
                    resc = MainPage(avatarId)
                    resc.realm = self
                    return (inevow.IResource, resc, resc.logout)
 
        raise NotImplementedError("Can't support that interface.")

class LoggedinPage(rend.Page):

    docFactory = loaders.stan(
        T.html[
            T.body[
                    T.h2["Welcome to OPC"],
                    T.p["You don't need to refresh, this page will be \
                    refreshed asynchronously!"]
                ]
            ]
        )
        
tags = T
class MainPage(rend.Page):
    addSlash = True
    docFactory = loaders.stan(
    tags.html[
        tags.head[tags.title["Hi Boy"]],
        tags.body[
            tags.invisible(render=tags.directive("isLogged"))[
                tags.div(pattern="False")[
                    tags.form(action=guard.LOGIN_AVATAR, method='POST')[
                        tags.table[
                            tags.tr[
                                tags.td[ "Username:" ],
                                tags.td[ tags.input(type='text',name='username') ],
                            ],
                            tags.tr[
                                tags.td[ "Password:" ],
                                tags.td[ tags.input(type='password',name='password') ],
                            ]
                        ],
                        tags.input(type='submit'),
                        tags.p,
                    ]
                ],
                tags.invisible(pattern="True")[
                    tags.h3["Hi bro"],
                    tags.invisible(render=tags.directive("sessionId")),
                    tags.br,
                    tags.a(href=guard.LOGOUT_AVATAR)["Logout"],
                    LoggedinPage()
                ]
            ]
        ]
    ])
 
    # These are stolen from guarded2.tac nevow example
    # have no idea of how they work ;)
    def __init__(self, avatarId=None):
        rend.Page.__init__(self)
        self.avatarId=avatarId
 
    def render_isLogged(self, context, data):
        true_pattern = context.onePattern('True')
        false_pattern = context.onePattern('False')
        if self.avatarId: return true_pattern or context.tag().clear()
        else: return false_pattern or context.tag().clear()
 
    def render_sessionId(self, context, data):
        sess = inevow.ISession(context)
        return context.tag[sess.uid]
 
    def logout(self):
        print "Bye"


