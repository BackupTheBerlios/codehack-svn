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
Javascript utility
"""

class JSUtil(object):

    def __init__(self, mind):
        "mind: mind.sendScript will be called"
        self.mind = mind

    def _send(self, ex):
        print 'JJJJJJJJJJ:', ex
        self.mind.sendScript(ex)

    def c_getid(self, id):
        return 'document.getElementById("%s")' % id
        
    def visible(self, id, visible):
        "Toggle the visibility"
        value = ['hidden', 'visible']
        ex = self.c_getid(id) + ".style.visibility = '%s';" % \
             value[int(visible)]
        self._send(ex)

    def set(self, id, innerHTML):
        self.mind.set(id, innerHTML)

    def alert(self, msg):
        self.mind.alert(msg)

    def reload(self):
        "Reload client page"
        self.mind.sendScript("window.location.reload();")
