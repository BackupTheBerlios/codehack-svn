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

"""Admin Avatar"""

import time

from twisted.spread import pb
from twisted.python import components
from twisted.internet import defer

from codehack.util import log
from codehack import util
from codehack.server import db


class AdminAvatar(pb.Avatar):

    """
    * UID = User Information dictionary
            (userid, passwd, name, emailid, type)
            - type is number in avatar and string in client
    """

    def __init__(self, mind, contest, loginat, id, userid, emailid):
        """
        @param mind:    Client remote object
        @param contest: The contest object
        @param loginat: Timestamp when logged in
        @param id:      The database row id of this user
        @param Userid:  User id
        @param emailid: emailid of the user
        """
        log.debug('AdminAvatar created - %s' % id)
        self.mind = None # see self.ready()
        self.id = id
        self.userid = userid
        self.emailid = emailid
        self.contest = contest
        self.dbproxy = contest.dbproxy
        self.loginat = loginat
        self.whoami = 'admin'

    def ready(self, mind):
        """Called when avatar is ready for operation.  Untill this
        avatar should wait for anything.

        This method is guaranteed to be called *immediately* after
        creating the Avatar object"""
        self.mind = mind
        self.registration_ids = []
        # Register listeners
        la = self.contest.liveavatars
        for evt in (la.EVT_LOGIN, la.EVT_LOGOUT):
            regid = la.registerListener(evt, 
                lambda avatar: self.liveClientsChanged())
            self.registration_ids.append(regid)
            
    def logout(self):
        """Called when this avatar logouts"""
        # UnRegister listeners
        la = self.contest.liveavatars
        for regid in self.registration_ids:
            la.unregisterListener(regid)
        
    def connectionAge(self):
        "Return the duration in seconds when avatar is logged in"
        return int(time.time()-self.loginat)
        
# -------------------------------------------------------------------------- #
#   1. startContest(duration):              getInformation()
#   2. stopContest():
#   3. disconnectClient(avatarId):
#   4. getLiveClients():                    dict
#   5. getInformation():                    dict
#
#   1. users_get_all:                       dict
#   2. users_get(user):
#   3. users_add(uid):
#   4. users_update(uid):
#   5. users_remove(users):
# -------------------------------------------------------------------------- #

    def perspective_whoami(self):
        """Return the string representing this avatar,
        which could be one of the following.
        1. team
        2. judge
        3. admin
        """
        return self.whoami
    
    def perspective_echo(self, obj):
        """Test method that echoes back the object"""
        return obj

    def perspective_startContest(self, duration):
        self.contest.startContest(duration)
        return self.perspective_getInformation()

    def perspective_stopContest(self):
        self.contest.stopContest()

    def perspective_disconnectClient(self, avatarId):
        "Disconnect a client"
        self.contest.liveavatars.disconnect(avatarId)
    
    def perspective_getLiveClients(self):
        """Return logged in clients dict
        {userid=>(typ, duration)}"""
        clients = {}
        for userid, avatar in self.contest.liveavatars.items():
            clients[userid] = (avatar.whoami, avatar.connectionAge())
        return clients
    
    # Contest information

    def perspective_getInformation(self):
        """Returns name, duration, age tuple.

        Contest is not running if duration is None"""
        age = None
        if self.contest.duration:
            age = self.contest.getContestAge()
        return {
            'name': self.contest.name,
            'duration': self.contest.duration,
            'age': age
        }
        
    # GET ALL - Get list of rows
    #
    
    def perspective_users_get_all(self):
        """Get the list of UID
        
        @returns: dictionary id=> {userid, passwd, name, emailid, type}
        """
        d = self.dbproxy.users_get_all()
        
        def filter_result(results):
            for result in results.values():
                self._update_user_dict(result, db.get_type_name)
            return results
        d.addCallback(filter_result)
        return d
        
    # GET - Get a single row
    #
    
    def perspective_users_get(self, user):
        """Get the UID for user
        
        @param user: id/userid
        """
        return self.dbproxy.users_get(user)
        
        
    # ADD - Add a single row
    #
        
    def _tmpl_add(self, seckey, dbget, dbadd, tid):
        
        # if already exists ...
        d = dbget(tid[seckey])
        def cur_user(result):
            if result:
                return util.getError('%s already exists' % \
                                       tid[seckey])
            return dbadd(tid)
        d.addCallback(cur_user)
        return d
        
    def perspective_users_add(self, uid):
        """Add a user."""
        self._update_user_dict(uid)
        return self._tmpl_add('userid', self.dbproxy.users_get, 
                               self.dbproxy.users_add, uid)
        
    # UPDATE
    #
        
    def _tmpl_update(self, dbget, dbupdate, tid):
        """Update"""
        # TODO also check for uniq fields like userid, ..
        # if user doesn't exists ...
        d = dbget(tid['id'])
        def cur_user(result):
            if not result:
                return util.getError("[%d] doesn't exists" % \
                                       tid['id'])
            return dbupdate(tid['id'], tid)
            
        d.addCallback(cur_user)
        return d
        
    def perspective_users_update(self, uid):
        """Update user account"""
        self._update_user_dict(uid)
        return self._tmpl_update(self.dbproxy.users_get, 
                                self.dbproxy.users_update, uid)
        
    # REMOVE
    #
        
    def _tmpl_remove(self, dbremove, rows):
        high_defer = defer.Deferred()
        def cb_done(result, removed):
            if removed:
                # first row removed!
                del rows[0]
            if len(rows) == 0:
                # done removing all
                high_defer.callback(None)
                return
            # remove first row
            d = dbremove(rows[0])
            d.addCallback(cb_done, True)
            return d
        cb_done(None, False)
        return high_defer
        
    def perspective_users_remove(self, users):
        """Remove all users specified in userids list
        
        @param users: list of userids/ids
        """
        return self._tmpl_remove(self.dbproxy.users_remove, users)
        
# -------------------------------------------------------------------------- #
        
    # client pass string value to key `type`, we convert it into 
    # number used by database
    def _update_user_dict(self, uid, db_filter=db.get_type_id):
        """Change str repr of type to num (database id)"""
        typ = uid['type']
        try:
            typ_id = db_filter(typ)
        except KeyError,o:
            raise RuntimeException, "Invalid user type passed - " + str(o)
        uid['type'] = typ_id

    def contestStarted(self):
        pass
    
    def contestStopped(self):
        "Callback on contest stop"
        self.mind.contestStopped()
    
    def liveClientsChanged(self):
        "Notification when a client logs-in/logs-out"
        self.mind.liveClients(
                        self.perspective_getLiveClients())
