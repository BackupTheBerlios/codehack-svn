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
Event Manager (MVC)
"""

from weakref import WeakKeyDictionary


class EventManager(object):
    
    """Manages events and notifes listeners

    Useful when deriving from this class"""
    
    def __init__(self, *event_types):
        self.__listeners = {} # evt_type -> listeners
        for et in event_types:
            self.__listeners[et] = WeakKeyDictionary()
        self.__listeners_id = {}  # id -> listener

    def registerListener(self, event_type, listener, rule=lambda *a: True):
        """Registers a listener.  Only events satisfying the given
        rule will be notified.
            if rule(event_data): then notify
        Returns registration id (used for unregistration)
        """
        lid = id(listener)
        self.__listeners[event_type][listener] = rule
        self.__listeners_id[lid] = (event_type, listener)
        return lid
        
    def unregisterListener(self, registration_id):
        event_type, listener = self.__listeners_id[registration_id]
        listeners = self.__listeners[event_type]
        if listener in listeners:
            del listeners[listener]
            
    def post(self, event_type, event):
        """Post an event"""
        for listener, rule in self.__listeners[event_type].items():
            if rule(event):
                listener(event)
    