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

"""Codehack services or API for extension/profile writers

Import this module of codehack, but any other in package tree
for use with external code - eg. SubmissionHandler

Also see avatar/team.py. TeamAvatar also serves some Service methods
"""

import os.path

from twisted.internet import protocol, error
from twisted.internet import defer, reactor

from codehack.util import log


class SimplePP(protocol.ProcessProtocol):
    
    "A simple ProcessProtocol that callbacks on process exit"

    def __init__(self, callback):
        self.defer = defer.Deferred()
        self.defer.addCallback(callback)
        print 'SPP: init'

    def processEnded(self, status):
        print 'SPP: end ',status.value
        if isinstance(status.value, error.ProcessDone):
            self.defer.callback(0)
        elif isinstance(status.value, error.ProcessTerminated):
            self.defer.callback(status.value.exitCode)
        print 'SPP: XXX'

    def errReceived(self, data):
        print data,
    def outReceived(self, data):
        print data,


def system(callback, executable, args):
    "Asynchronous version of os.system using twisted's ProcessProtocol"
    pp = SimplePP(callback)
    log.debug('system exe:[%s] args:[%s]' % (executable, args))
    reactor.spawnProcess(pp, executable, args)
 
def _safe_exec(cmd_line, work_dir='.', res_limit_args=None):
    "Return executable, args for safeexec.py that will execute cmd_line"
    safe_wrapper_script = \
        os.path.join(os.path.split(__file__)[0], 'safeexec.py')
    # FIXME: ugly hack!
    executable = '/usr/bin/python'
    args = ['python', safe_wrapper_script, cmd_line, work_dir]
    if res_limit_args:
        args = args + res_limit_args
    return executable, args
    
def safe_system(callback, cmd_line, work_dir='.', res_limit_args=None):
    "Safe version of `system` that uses wrapper script"
    executable, args = _safe_exec(cmd_line, work_dir, res_limit_args)
    system(callback, executable, args)

def safe_spawn(pp, cmd_line, work_dir='.', res_limit_args=None):
    "Safe version of reactor.spawnProcess"
    executable, args = _safe_exec(cmd_line, work_dir, res_limit_args)
    log.debug('safe_spawn exe:[%s] args:[%s]' % (executable, args))
    reactor.spawnProcess(pp, executable, args)
