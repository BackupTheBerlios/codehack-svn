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

    def __init__(self, mind, contest, id, userid, emailid):
        """
        @param mind:    Client remote object
        @param contest: The contest object
        @param id:      The database row id of this user
        @param Userid:  User id
        @param emailid: emailid of the user
        """
        log.debug('AdminAvatar created - %s' % id)
        self.mind = mind
        self.id = id
        self.emailid = emailid
        self.contest = contest
        self.dbproxy = contest.dbproxy
        self.whoami = 'admin'

    def contestStarted(self):
        pass
    
    def contestStopped(self):
        "Callback on contest stop"
        self.mind.callRemote('contest_stopped')
    
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

    def perspective_start_contest(self, duration):
        self.contest.start_contest(duration)
        return self.perspective_get_contest_info()

    def perspective_stop_contest(self):
        self.contest.stop_contest()

    # Contest information

    def perspective_get_contest_info(self):
        """Returns name, duration, contestage tuple.

        Contest is not running of duration is None"""
        duration = self.contest.duration
        name = self.contest.name
        if duration:
            return name, duration, self.contest.get_contest_age()
        return name, None, None
    
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
