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
Web exceptions
"""

class WebServiceError(Exception):

    "Error in WebService (nevow)"

    def __init__(self, *args):
        Exception.__init__(self)

    def getMessage(self):
        try:
            msg = self.args[0]
        except IndexError:
            msg = ''
        return self._prefixed(msg)

    def _prefixed(self, msg):
        "Apply any prefix, if any and return new message"
        return 'Error. ' + msg
        

class ContestNotRunning(WebServiceError):

    def _prefixed(self, msg):
        return 'Contest is not running. ' + msg


class InvalidFilename(WebServiceError):

    def _prefixed(self, msg):
        return 'Invalid filename. ' + msg
