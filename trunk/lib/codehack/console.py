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

"""GUI Console package

Allows one to print to Text widgets instead of printing in terminal.
"""

import gtk


class Console(object):
    
    """Log messages to the widget passed

    This is abstract class
    """
    
    def _print(self, msg, nl=True):
        """Behave like Python's print statement, but print to widget.
        nl is True of newline is to be printed.

        This method must be overriden by derived classes"""
        
    def write(self, msg, nl=True):
        self._print(msg, nl)
    
class TextViewConsole(Console):
    
    def __init__(self, textviewwidget):
        super(TextViewConsole, self).__init__()
        self.widget = textviewwidget
        textviewwidget.set_cursor_visible(False)
        textviewwidget.set_wrap_mode(gtk.WRAP_WORD)
        textviewwidget.set_editable(False)
    
    def _print(self, msg, nl=True):
        # Append to TextView widget
        tv = self.widget
        buffer = tv.get_buffer()
        if nl:
            msg = '%s\n' % msg
        buffer.insert(buffer.get_end_iter(), msg)
        
