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

"""Low-level db api.

All database related code will be here, presenting a clean API to
higher level code

NOTE: Only SQLITE is supported
"""

# NOTE: Only SQLITE is supported

import pickle

from twisted.enterprise import adbapi

from codehack.util import reverse_dict, log

# Enumerated values of 'type' field of the user table
USER_TEAM = 0
USER_JUDGE = 1
USER_ADMIN = 2

# Reverse mappings (will help client to use strings)
__user_type = {
    'team': 0,
    'judge': 1,
    'admin': 2
}

# reverse the dictionary
__rev_user_type = reverse_dict(__user_type)

def get_type_id(typ):
    """
    @param typ: is one 'team', 'admin', 'judge'
    @returns: the id - 0,1,2
    """
    return __user_type[typ]
    
def get_type_name(typ_id):
    return __rev_user_type[typ_id]

# See admin.py avatar class for description 
# of UID - User Information dictionary

# Objects are stored as pickles
none_pickle = pickle.dumps(None)

class DBProxy(object):
    """Proxy between different DBMS's and the application logic.
    This is an abstract class (but DBMS independence is not our concern -
    only sqlite is supported :D )
    
    @ivar conn: The connection object
    """
    
    # table => method producing the tid/
    # see __init__
    tid_map = None
    
    # TODO: clean up code (due to architecture shift)
    
    # table => secondary key name
    seckey = {
        'users': 'userid',
        'submissions': 'ts',
    }
    
    def __init__(self):
        self.tid_map = {
            'users': self._uid,
            'submissions': self._sid,
            #'languages': self._lid,
            #'results': self._rid,
            #'problems': self._pid,
        }
        self.conn = None
    
    # The following _TABLE_* are template methods
    # For each such method (_TABLE_get for eg), methods like
    # <tablename>_get will be created that will just wrap this method
    # with table argument equal to the table name
    #
    # In brief, these will be curried
    
    # TODO: make this method the default
    def _TABLE_get_ex(self, table, tid, multiple=False):
        """This the improved version of _get
        
        @param table        : name of table
        @param tid          : tid which contains the == key,values
        @param multiple     : True if multiple results are expected
        """
        def fmt_result(result):
            if not result:
                return None
            def get_tid(res):
                #first_result = result[0]
                fields = [res[x] for x in range(1,len(res))]
                #fields = map(first_result.__getitem__, 
                #        range(1,len(first_result)))
                tid = self.tid_map[table](*(fields + [res[0]]))
                return tid
            if multiple is False:
                return get_tid(result[0])
            else:
                return [get_tid(x) for x in result]
        
        # Create list of where conditions
        set_list = []
        set_value_list = []
        for attr in tid.keys():
            val = tid[attr]
            set_list.append(attr + ' = %s')
            set_value_list.append(val)
        
        query = 'SELECT * FROM ' + table + ' where '+ \
                    'AND '.join(set_list)
        d = self.conn.runQuery(query, *set_value_list)
        d.addCallback(fmt_result)
        return d
        
    def _TABLE_get(self, table, identity, usekey=None, multiple=False):
        """Get row information
        
        @param identity     : id/seckey
        @param table        : name of table
        @param usekey       : Key to be used for `identity`
        @param multiple     : True if multiple results are returned
        @returns            : TID for identity
        """
        # This is ugly hack
        # FIXME: tell all callers to use get_ex or change the API at whole
        tid = {}
        if isinstance(identity, int):
            tid['id'] = identity
        else:
            if usekey:
                tid[usekey] = identity
            else:
                tid[self.seckey[table]] = identity
        return self._TABLE_get_ex(table, tid, multiple)

    def _TABLE_update(self, table, identity, tid):
        """Update row information
        
        @param user         : userid/id
        @param uid          : The new UID
        """
        query_cond = self._id_query_cond(table, identity, self.seckey[table])
        set_list = []
        set_value_list = []
        
        # Remove id
        try:
            del tid['id']
        except KeyError:
            pass
            
        # Create list of where conditions
        # conditionally as TID may not be complete
        for attr in tid.keys():
            val = tid[attr]
            if val:
                set_list.append(attr + ' = %s')
                set_value_list.append(val)
        
        set_value_list.append(identity) # for query_cond
        
        query = 'UPDATE ' + table + ' set ' + ', '.join(set_list) + \
                ' where ' + query_cond
        d = self.conn.runOperation(query, *set_value_list)
        return d
        

    def _TABLE_remove(self, table, identity):
        """Remove row"""
        query_cond = self._id_query_cond(table, identity, self.seckey[table])
        
        query_str = 'DELETE from ' + table + ' WHERE ' + query_cond
        d = self.conn.runOperation(
            query_str, identity)
        return d
    
    def _TABLE_get_all(self, table):
        """Get list of all rows.
        
        @returns: list of IDs
        """
        query_str = 'SELECT * from %s' % table
        d = self.conn.runQuery(query_str)
        def got_result(results):
            ids = {}
            for result in results:
                result_dict = {}
                for attr, value in result.items():
                    result_dict[attr] = value   
                ids[result['id']] = result_dict
            return ids
        d.addCallback(got_result)
        return d
    
    # Then the following methods cannot be curried as above are
    # 
    
    def users_add(self, uid):
        """Add a user
        
        @param uid: UID for new user
        """
        query_str = 'INSERT into users values(NULL, %s, %s, %s, %s, %s, %s)'
        d = self.conn.runOperation(query_str, 
                    uid['userid'],
                    uid['passwd'],
                    uid['name'],
                    uid['emailid'],
                    uid['type'], 
                    none_pickle )
        return d

    def submissions_add(self, sid):
        """Add a submission
        
        @param sid: SID for new submission
        """
        query_str = 'INSERT into submissions values(NULL, %s, %s, %s, %s, %s)'
        d = self.conn.runOperation(query_str, 
                    sid['users_id'],
                    sid['problem'],
                    sid['language'],
                    sid['ts'],
                    sid['result'] )
        return d

    
    
    # For non-reactor based code (used by code creating new contest)
    def add_user_sync(self, userid, password, name, emailid, type):
        """Add new user to users table. Doesn't uses twisted's adapi.
        So a reactor is not needed.
        
        @param userid: userid 
        @param password: password
        @param name: name else userid if name is None
        @param emailid: emailid
        @param type: type
        """
        if type not in [USER_ADMIN, USER_JUDGE, USER_TEAM]:
            raise ValueError, 'Invalid type'
        query_str = 'INSERT into users values(NULL, %s, %s, %s, %s, %s, %s)'
        import sqlite
        c = sqlite.connect(self.database, autocommit=True)
        cr = c.cursor()
        cr.execute(query_str, userid, password, name or userid, emailid, 
                  type, none_pickle)
        cr.close()
        c.close()

    def clear_submissions_sync(self):
        "Clear all records in submissions table"
        query = 'DELETE from submissions'
        import sqlite
        c = sqlite.connect(self.database, autocommit=True)
        cr = c.cursor()
        cr.execute(query)
        cr.close()
        c.close()
        
        
    # Returns the query condition based on argument (userid or id)
    def _id_query_cond(self, table, arg, seckey):
        # Tables for which id retrieval is meaningless
        no_id_retrieval = ['submissions']
        if isinstance(arg, int) and table not in no_id_retrieval:
            query_cond = 'id = %s'
        else:
            query_cond = seckey+' = %s'
        return query_cond
        
    # Returns UID
    def _uid(self, userid, passwd, name, emailid, type, score=None, id=None):
        uid = {
            'userid': userid,
            'passwd': passwd,
            'name': name,
            'emailid': emailid,
            'type': type
        }
        if score:
            uid['score'] = score
        if id:
            uid['id'] = id
        return uid

    def _sid(self, users_id, problem, language, ts, result, id=None):
        sid = {
            'users_id': users_id,
            'problem': problem,
            'language': language,
            'ts': ts,
            'result': result,
        }
        if id:
            sid['id'] = id
        return sid
        
# Instantiate _TABLE_* methods for each table and operation
for method in ['get_all', 'get_ex', 'get', 'update', 'remove']:
    for tablename in DBProxy.seckey.keys():
        # Set <tablename>_<method>
        def proxy_setter(table):
            # bcoz, otherwise table argument will be refered only during call
            attr = '%s_%s' % (table, method)
            comm_attr = getattr(DBProxy, '_TABLE_%s' % method)
            log.debug('Creating DB method: %s', attr)
            setattr(DBProxy, attr, lambda self, *args, **kwargs: \
                    comm_attr(self, table, *args, **kwargs))
        proxy_setter(tablename)



class SqliteDBProxy(DBProxy):
    """Sqlite light-weight DBMS - www.sqlite.org"""
    
    DB_MODULE = 'sqlite'
    
    def __init__(self, database):
        """
        @parama database : absolute or relative path to database file
        """
        super(SqliteDBProxy, self).__init__()
        self.database = database
        self.conn = adbapi.ConnectionPool(self.DB_MODULE, database=database)


