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

"""Contains Twisted's Portal, Realm, ..."""

import time

from twisted.application import service, internet
from twisted.internet import reactor, defer
from twisted.cred import checkers
from twisted.cred import portal
from twisted.cred import error
from twisted.cred import credentials
from twisted.spread import pb
from twisted.python import failure

from nevow import appserver
from nevow import liveevil
from nevow import guard

from codehack.util import log
from avatar import team, admin
import db
import auth


class DefaultMindAdaptor(object):
    
    "Adapts mind of twisted.spread client"
    
    def __init__(self, mind, avatar):
        self.mind = mind
        self.avatar = avatar

    def __getattr__(self, attr):
        def proxy(*args, **kwargs):
            self.mind.callRemote(attr, *args, **kwargs)
        return proxy

# twisted.cred Authorization framework
class Realm(auth.CodehackRealm):

    __implements__ = portal.IRealm
    
    interface = pb.IPerspective
    mind_adaptor = {
        db.USER_TEAM: DefaultMindAdaptor,
        db.USER_ADMIN: DefaultMindAdaptor,
        db.USER_JUDGE: DefaultMindAdaptor
    }
    
    def __init__(self, contest):
        self.contest = contest
        self.liveavatars = contest.liveavatars
        
    def requestThisAvatar(self, avatarId, mind, remove_f):
        return self.interface, self.liveavatars.get(avatarId), remove_f

def getApplication(contest, port, backlog=500, backlog_web=500):
    """Return application that must be run
    .tac file calls this function"""
    app = service.Application('codehack')
    
    realm = Realm(contest)
    portal_ = portal.Portal(realm)
    portal_.registerChecker(auth.CodehackChecker(contest.dbproxy))
    
    # The Distributed service (twisted.spread)
    coreservice = internet.TCPServer(port, pb.PBServerFactory(portal_), backlog)
    coreservice.setServiceParent(app)
    
    # The Web service (nevow)
    from web import base
    realm = base.WebRealm(contest)
    myChecker = auth.CodehackChecker(contest.dbproxy)
    portal_ = portal.Portal(realm)
    portal_.registerChecker(myChecker)
    portal_.registerChecker(
        checkers.AllowAnonymousAccess(), credentials.IAnonymous)
    site = appserver.NevowSite(resource=guard.SessionWrapper(
        portal_, mindFactory=liveevil.LiveEvil) )
    webservice = internet.TCPServer(8080, site, backlog_web)
    webservice.setServiceParent(app)
    
    return app
