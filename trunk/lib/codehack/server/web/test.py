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

import time
from os.path import join

from twisted.cred import portal
from twisted.cred import checkers

from nevow import loaders
from nevow import rend
from nevow import tags as T
from nevow import liveevil
from nevow import inevow
from nevow import guard

from codehack import paths
from codehack.server import auth
from codehack.server import db


class NevowTeamMind(object):
    
    def __init__(self, mind):
        self.mind  = mind
        
    def info(self, msg):
        """Message from server"""
        pass

    def submissionResult(self, r):
        pass
        # self.gui.showSubmissionResult(r['problem'], r['language'], r['ts'], r['result'])

    def contestStopped(self):
        self.mind.sendScript('alert("Stopped");')
        # self.gui.contestStopped()

    def contestStarted(self, name, details):
        self.mind.sendScript('alert("Started");')
        # self.gui.contestStarted(name, details)


class NevowAdminMind(object):
    
    def __init__(self, mind):
        self.mind = mind
        
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
        

class WebRealm(auth.CodehackRealm):
    """A simple implementor of cred's IRealm.
       For web, this gives us the LoggedIn page.
    """
    __implements__ = portal.IRealm
    interface = inevow.IResource
    
    mind_adaptor = {
        db.USER_TEAM: NevowTeamMind,
        db.USER_ADMIN: NevowAdminMind,
        db.USER_JUDGE: None
    }
    
    def requestAnonymousAvatar(self, mind):
        return self.interface, LoginPage(), lambda: None
    
    def requestThisAvatar(self, avatarId, mind, remove_f):
        resc = MainPage(self.liveavatars.get(avatarId), mind)
        def logout():
            resc.logout()
            remove_f()
        return self.interface, resc, logout
    
    def WWrequestAvatar(self, avatarId, mind, *interfaces):
        for iface in interfaces:
            if iface is inevow.IResource:
                if avatarId is checkers.ANONYMOUS:
                    resc = LoginPage()
                    logout = lambda : None
                else:
                    from codehack.server.avatar import team, admin
                    avatar = team.TeamAvatar(
                        mind, self.contest, int(time.time()), id1, 
                        userid, emailid, webclient=True)
                    resc = MainPage(avatarId)
                    resc.mind = mind
                    self.liveavatars.add(avatarId, avatar)
                    logout = lambda : self.liveavatars.remove(avatarId)
                resc.realm = self
                return (inevow.IResource, resc, logout)
 
        raise NotImplementedError("Can't support that interface.")
        
def web_file(fil):
    return join(paths.WEB_DIR, fil)

class LoginPage(rend.Page):
    
    "The Login page"
    
    addSlash = True
    docFactory = loaders.xmlfile(web_file('login.html'))

    def render_loginForm(self, ctx, data): 
        return ctx.tag(action=guard.LOGIN_AVATAR, method='POST')

    def logout(self):
        pass


class MainPage(rend.Page):

    addSlash = True
    docFactory = loaders.xmlfile(web_file('main.html'))

    def __init__(self, avatar, mind):
        self.avatar = avatar
        self.mind = mind

    def render_loginname(self, ctx, data):
        return self.avatar.userid

    def render_logout(self, ctx, data):
        return ctx.tag(href=guard.LOGOUT_AVATAR)

    def render_glue(self, ctx, data):
        return liveevil.glue
    
    def fun(self):
        self.mind.sendScript('alert("Good boy!");')
        from twisted.internet import reactor
        reactor.callLater(3, self.fun)
    
    def logout(self):
        print 'Bye'
