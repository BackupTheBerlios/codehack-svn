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

"""Standalone python script for Safe execution of process
"""


import sys
import os
import resource

# FIXME/TODO: Is there a way to avoid usage of sockets, signal ...??!
#             A simple scanning of source files is not enough, as
#             we will be receiving source for different languages,
#             (think dynamism of Python)

# Shell command to execute given command string
# FIXME: This requires UNIX system, any portable solution??
sh_cmd = '/bin/sh'
sh_cmd_args = ['/bin/sh', '-c']

if __name__ != '__main__':
    print 'WARNING: This script cannot be imported'


def usage():
    usage_str = '\n'.join([
    "python safeexec.py cmd_line work_dir [res=soft,hard  ..]",
    "",
    "res is one of the below possible strings",
    "   RLIMIT_CORE -  Maximum size (in bytes) of a core file",
    "   RLIMIT_CPU  -  Maximum processor time (in seconds)",
    "   RLIMIT_FSIZE - Maximum size of a file which the process may create",
    "   RLIMIT_DATA  - Maximum heap size (in bytes)",
    "   RLIMIT_STACK - Maximum stack size (in bytes)",
    "   RLIMIT_RSS   - Maximum resident set size (in bytes)",
    "   RLIMIT_NPROC - Maximum number of processes current process may create",
    "   RLIMIT_NOFILE - Maxinum number of open file descriptors",
    "   RLIMIT_MEMLOCK- maximum address space which may be locked in memory",
    "   RLIMIT_VMEM   - Largest area of mapped memory",
    "   RLIMIT_AS     - Maximum area (in bytes) of address space"
    ])
    print usage_str


if len(sys.argv) < 3:
    usage()
    sys.exit(1)

cmd_line = sys.argv[1]
work_dir = sys.argv[2]

for res_opt in sys.argv[3:]:
    res, value = res_opt.split('=')
    res_no = getattr(resource, res)
    value = tuple(map(int, value.split(',')))
    resource.setrlimit(res_no, value)
    
cmd = sh_cmd_args + [cmd_line]
os.chdir(work_dir)
#print '******SAFEEXEC******:', sh_cmd, cmd

os.execl(sh_cmd, *cmd)

