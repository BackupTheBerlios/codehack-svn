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

"""Contest manipulation"""

import time
import os
import os.path
from os.path import join, abspath
import string

import sqlite
from twisted.internet import reactor

from codehack import paths
from codehack.util import log
from codehack.evt import EventManager
from codehack.server.db import SqliteDBProxy
from codehack.server.db import USER_ADMIN, USER_TEAM

from avatar.team import TeamAvatar


class LiveAvatars(EventManager):
    
    """Logged in Avatars"""

    # Event Types
    EVT_LOGIN,\
    EVT_LOGOUT,\
    = range(2)
    
    def __init__(self):
        EventManager.__init__(self, self.EVT_LOGIN, self.EVT_LOGOUT)
        self._avatars = {}
        
    def get(self, avatarId):
        "Return the avatar which is logged in, None otherwise"
        if avatarId in self._avatars:
            return self._avatars[avatarId]
        return None
        
    def items(self):
        "Return self._avatars.items()"
        return self._avatars.items()
    
    def add(self, avatarId, avatar):
        "Called when an avatar logs in"
        log.debug('Avatar [%s] logs in' % avatarId)
        self._avatars[avatarId] = avatar
        self.post(self.EVT_LOGIN, avatar)
        #if self._avatars.has_key('admin'):
        #    # Notify admin
        #    self._avatars['admin'].liveClientsChanged()
        
    def remove(self, avatarId):
        "Called when an avatar logs out"
        log.debug('Avatar [%s] logs out' % avatarId)
        avatar = self._avatars[avatarId]
        avatar.logout()
        del self._avatars[avatarId]
        self.post(self.EVT_LOGOUT, avatar)
        #if self._avatars.has_key('admin'):
        #    # Notify admin
        #    self._avatars['admin'].liveClientsChanged()
    
    def disconnect(self, avatarId):
        "Disconnect an avatar"
        log.debug('Avatar [%s] will be disconnected' % avatarId)
        transport = self._avatars[avatarId].mind.broker.transport
        transport.loseConnection()


class Contest(object):
    """The contest.
    
    The server requires a (single) contest object.
    
    @ivar name:      Contest name
    @ivar directory: Contest directory
    @ivar dbpath:    Path to contest database
    @ivar avatars:   Dictionary of loggedin avatars (userid=>avatar object)
    @ivar duration:  Duration of the contest in seconds
    @ivar profile:   Contest Profile object
    @ivar ts_start:  Timestamp during start of contest
    @ivar dbproxy:   The database proxy object which has methods to manipulate
                     the database.
    @ivar dirs:      Special directories (name=>absolute path)
                     team - Team related files
                     judge - Judge's files
                     stat - Contest statistics related files
    """
    
    # Properties
    duration = property(lambda s: s._duration)
    profile = property(lambda s: s._profile)
    ts_start = property(lambda s: s._ts_start)
    
    def __init__(self, name, directory):
        """
        @param name         : name of the contest (dir name also)
        @param directory    : Parent directory of this contest directory
        """
        self.name = name
        self.directory = abspath(join(directory, name))
        self.dbpath = join(self.directory, 'repos', self.name)
        self.liveavatars = LiveAvatars()
        self._duration = None # If int, then time left to stop started contest
        self._profile = None  # Profile object
        self._ts_start = None # Timestamp during start of contest

        dirs = {}
        for dr in ['repos', 'team', 'judge', 'stat']:
            dirs[dr] = join(self.directory, dr)
        self.dirs = dirs

    def create(self, admin_passwd, admin_email):
        """Create the contest. This also opens it.
        
        @param admin_passwd: Password for 'admin' account
        @param admin_email:  Emailid of 'admin' account
        """
        if True in [x.isspace() for x in self.name]:
            raise ValueError, 'contest_name must not contain any white space'
        
        # Create directories
        dirs = [self.directory]             # Top-level
        dirs.extend(self.dirs.values())     # others ..
        [os.mkdir(dr) for dr in dirs]

        # Init DB
        dbpath = join(self.dirs['repos'], self.name) # Only one database
        db = sqlite.connect(dbpath, autocommit=True)
        cursor = db.cursor()
        queries = _get_queries(file(join(paths.DATA_DIR, 'contest-sqlite.sql')))
        [cursor.execute(query) for query in queries]
        cursor.close()
        db.close()


        # Open the contest and add admin account to db
        self.open()
        # We use *_sync method as we don't use Twisted's reactor yet!!
        self.dbproxy.add_user_sync('admin', admin_passwd, 'Contest Admin', 
                              admin_email, USER_ADMIN)
        
        
    def open(self, resume=False):
        """Open the contest (connect to db, ...).  Must have been
        created before
        
        @param resume: Whether the contest must be resumed
        """
        if not os.path.isdir(self.directory):
            raise "No such contest '%s' exists - %s not found" % \
                (self.name, self.directory)
        self.dbproxy = SqliteDBProxy(self.dbpath)
        if not resume:
            self.dbproxy.clear_submissions_sync()

    def startServer(self, profile):
        """Start the contest server
        
        @param profile: ContestProfile object (see profile.__init__.py)
        """
        if not hasattr(self, 'dbproxy'):
            raise RuntimeError, 'Contest must be opened (contest.open) first'
        import gateway
        self._profile = profile
        profile.setContest(self)

        # DEBUG - start contest now
        self.startContest(60*100)

    def getContestAge(self):
        "Return number of seconds since start of contest"
        assert self.isrunning() is True, 'Contest is not running!!'
        return int(time.time()) - self._ts_start
    
    def startContest(self, duration):
        """Start accepting submissions

        @param duration: Duration (in seconds) before stopping the contest"""
        if self.isrunning():
            return
        self._duration = duration
        self._ts_start = int(time.time())
        reactor.callLater(duration, self.stopContest)
        for avatarId, avatar in self.liveavatars.items():
            avatar.contestStarted()
        log.info('Contest started with duration=%d seconds' % duration)
        
    def stopContest(self):
        """stop the contest"""
        if self.isrunning() is False:
            return
        self._duration = None
        self._ts_start = None
        # Tell avatars
        for avatarId, avatar in self.liveavatars.items():
            avatar.contestStopped()
        log.info('Contest stopped')
        
    def isrunning(self):
        """Whether contest is running?"""
        return self._duration is not None
    
    def getTeamAvatars(self):
        "Return the list of all (DBid, Team AvatarIds) from database"
        def _cbGotUsers(teams):
            avatarIds = []
            for dbid, team in teams.items():
                avatarIds.append((dbid, team['userid']))
            return avatarIds
        d = self.dbproxy.users_get_all({'type': str(USER_TEAM)})
        return d.addCallback(_cbGotUsers)
    
    def copyFile(self, avatar, instantid, filename, filecontent):
        """Copy the file to user data directory within directory named 
        instantid 

        @param avatar:      The avatar object which needs the file
        @param instantid:   The instantid that differentiates with other
                            instances of same avatar (eg. timestamp)
        @param filename:    Filename to write
        @param filecontent: File contents

        @return:            Created filepath
        """
        # Create directory if doesn't exist
        instantid = str(instantid)
        userdir_parent = join(self.directory, avatar.whoami, avatar.userid)
        userdir = join(userdir_parent, instantid)

        # If the instantid is not unique, modify it by prepending it
        # with sequence number
        old_instantid, seq_num = instantid, 1
        while os.path.isdir(userdir):
            instantid = old_instantid + '-' + str(seq_num)
            userdir = join(userdir_parent, instantid)
            seq_num = seq_num + 1
        os.makedirs(userdir)

        # Create file named filename with content filecontent
        filename = join(userdir, filename)
        fh = file(filename, 'w')
        try:
            fh.write(filecontent)
        finally:
            fh.close()
        return filename

        
def _get_queries(sql_file):
    """Get queries from sql_file.  # comments are ignored.
    Queries must be seperated by single blank line.  Query
    must be continuous without line break."""
    lines = [x.strip() for x in sql_file.readlines()]
    # strip comments
    lines = [x for x in lines if not x.startswith('#')]
    query = ''
    queries = []
    for line in lines:
        if line:
            query = query + line
        else:
            if query:
                queries.append(query)
            query = ''
    if query:
        queries.append(query)
    return queries
