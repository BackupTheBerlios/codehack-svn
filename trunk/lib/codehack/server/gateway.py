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

from twisted.cred import checkers, portal, error, credentials
from twisted.internet import reactor, defer
from twisted.spread import pb
from twisted.python import failure

from codehack.util import log
from codehack.server.avatar import team, admin
from codehack.server import db


# twisted.cred Authorization framework
class CodehackRealm:

    __implements__ = portal.IRealm
    
    def __init__(self, contest):
        """
        @param contest: The contest object.
        """
        # Currently logged in avatars
        self.loggedin = contest.avatars
        self.contest = contest
        
    # Authorizes the avatar
    def requestAvatar(self, avatarId, mind, *interfaces):
        log.debug('LOGIN: ' + avatarId + ' Mind? ' + str(mind is not None))
        if pb.IPerspective not in interfaces:
            raise NotImplementedError
        # Already logged in? then return the created Avatar.
        # TODO: better solution is to volunteerily logout the old avatar
        if avatarId in self.loggedin:
            return pb.IPerspective, self.loggedin[avatarId], lambda:None
        
        def cb_user(uid):
            assert uid
            typ = uid['type']
            emailid = uid['emailid']
            id = uid['id']
            userid = uid['userid']
            if typ == db.USER_TEAM:
                avatar_factory = team.TeamAvatar
            elif typ == db.USER_JUDGE:
                avatar_factory = judge.JudgeAvatar
            elif typ == db.USER_ADMIN:
                avatar_factory = admin.AdminAvatar
            else:
                raise RuntimeError, 'Invalid type returned by database'
            
            avatar = avatar_factory(mind, self.contest, int(time.time()),
                                id, userid, emailid)
            self.contest.client_loggedin(avatarId, avatar)
            return pb.IPerspective, avatar, \
                lambda : self.loggedin.__delitem__(avatarId)
            
        d = self.contest.dbproxy.users_get(avatarId)
        d.addCallback(cb_user)
        return d


# twisted.cred Authentication framework
class CodehackUsernamePasswordDatabase(object):

    __implements__ = checkers.ICredentialsChecker
    
    credentialInterfaces = (credentials.IUsernamePassword,
        credentials.IUsernameHashedPassword)
    
    def __init__(self, dbproxy):
        """
        @param dbproxy: Contest object's dbproxy
        """
        self.dbproxy = dbproxy
        super(CodehackUsernamePasswordDatabase, self).__init__()
    
    # Authenticates given credential information
    def requestAvatarId(self, cred):
        log.debug('Checking up credentials for ' + cred.username)
        def cb_user(uid):
            log.debug('uid = ' + str(uid))
            if uid is None:
                return failure.Failure(error.UnauthorizedLogin())
            def cb_checked(matched):
                if matched:
                    return cred.username
                return failure.Failure(error.UnauthorizedLogin())
           
            return defer.maybeDeferred( cred.checkPassword, uid['passwd']
                            ).addCallback(cb_checked)

        d = self.dbproxy.users_get(cred.username)
        d.addCallback(cb_user)
        return d

def start_server(contest):
    """I'm the main function.  I'll start the Twisted server
    
    @param contest: The contest object"""
    PORT=8800
    p = portal.Portal(CodehackRealm(contest))
    #p.registerChecker(checkers.InMemoryUsernamePasswordDatabaseDontUse
    #                    (user1="pass1"))
    p.registerChecker(CodehackUsernamePasswordDatabase(contest.dbproxy))
    reactor.listenTCP(PORT, pb.PBServerFactory(p))
    log.info('Starting reactor ...')
    reactor.callLater(0, log.info, 
                'Server Ready. Listening at port %d' % PORT)
    reactor.run()
    log.info('Reactor exited')
