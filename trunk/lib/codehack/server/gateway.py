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

from twisted.internet import reactor, defer
from twisted.cred import checkers
from twisted.cred import portal
from twisted.cred import error
from twisted.cred import credentials
from twisted.spread import pb
from twisted.python import failure

from codehack.util import log
from codehack.server.avatar import team, admin
from codehack.server import db


# twisted.cred Authorization framework
class CodehackRealm:

    __implements__ = portal.IRealm
    
    def __init__(self, contest):
        self.contest = contest
        
    # Authorizes the avatar
    def requestAvatar(self, avatarId, mind, *interfaces):
        log.debug('LOGIN: ' + avatarId + ' Mind? ' + str(mind is not None))
        if pb.IPerspective not in interfaces:
            raise NotImplementedError

        # Already logged in? then return the created Avatar.
        # TODO: better solution is to volunteerily logout the old avatar
        avatar = self.contest.getAvatar(avatarId)
        if avatar is not None:
            log.warn('Avatar %s logs in again!' % avatarId)
            return pb.IPerspective, avatar, lambda:None

        d = self.contest.dbproxy.users_get(avatarId)
        return d.addCallback(self.getAvatar, avatarId, mind)
        return d
        
    def getAvatar(self, uid, avatarId, mind):
        assert uid
        typ = uid['type']
        emailid = uid['emailid']
        id1 = uid['id']
        userid = uid['userid']
        
        typ_map = {
            db.USER_TEAM: team.TeamAvatar,
            db.USER_JUDGE: None, #judge.JudgeAvatar,
            db.USER_ADMIN: admin.AdminAvatar
        }
        try:
            avatar_factory = typ_map[typ]
        except KeyError:
            raise RuntimeError, 'Invalid type returned by database'
            
        avatar = avatar_factory(mind, self.contest, int(time.time()),
                                id1, userid, emailid)
        self.contest.avatars_add(avatarId, avatar)
        return pb.IPerspective, avatar, \
                lambda : self.contest.avatars_remove(avatarId)
            

# twisted.cred Authentication framework
class CodehackChecker:

    __implements__ = checkers.ICredentialsChecker
    
    credentialInterfaces = (credentials.IUsernamePassword,
        credentials.IUsernameHashedPassword)
    
    def __init__(self, dbproxy):
        self.dbproxy = dbproxy
    
    # Authenticates given credential information
    def requestAvatarId(self, cred):
        """Return the avatar id of the avatar which can be accessed using
        the given credentials.

        credentials will be an object with username and password attributes
        we need to raise an error to indicate failure or return a username
        to indicate success. requestAvatar will then be called with the avatar
        id we returned.
        """
        log.debug('Checking up credentials for ' + cred.username)
        d = self.dbproxy.users_get(cred.username)
        return d.addCallback(self.verify, cred)

    def verify(self, uid, cred):
        log.debug('uid = ' + str(uid))
        if uid is None:
            # No user with that name found
            return error.UnauthorizedLogin()
        return defer.maybeDeferred(
            cred.checkPassword, uid['passwd']).addCallback(
            self._cbPasswordMatch, cred.username)

    def _cbPasswordMatch(self, matched, username):
        if matched:
            return username
        else:
            return failure.Failure(error.UnauthorizedLogin())


# TODO: This is ugly.  Must use .tac
def start_server(contest):
    """I'm the main function.  I'll start the Twisted server
    """
    PORT=8800
    p = portal.Portal(CodehackRealm(contest))
    p.registerChecker(CodehackChecker(contest.dbproxy))
    reactor.listenTCP(PORT, pb.PBServerFactory(p))
    log.info('Starting reactor ...')
    reactor.callLater(0, log.info, 
                'Server Ready. Listening at port %d' % PORT)
    reactor.run()
    log.info('Reactor exited')
