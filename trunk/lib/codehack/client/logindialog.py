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

"""Login dialog GUI"""

from os.path import join
import inspect
import gtk

from twisted.spread import pb, flavors
from twisted.cred import credentials
from twisted.internet import reactor
from twisted.python import components

from codehack.gwidget import GWidget
from codehack import paths, util


# Timeout for login operation in seconds
TIMEOUT=30

class MindProxy(flavors.Referenceable):
    """Proxy to Minds of Team, Judge, Admin
    
    As we won't know in advance the type of user and mind must
    be passed during login, we use a common Mind object that we
    later use as a proxy to real (supposed to be) Mind object
    """

    def __init__(self):
        self._rmi_wait = []
    
    def __getattr__(self, attrname):
        "Proxy for RMI until set_target is called for populating real methods"
        def proxyit(*args, **kwargs):
            self._rmi_wait.append( (attrname, args, kwargs) )
        return proxyit
    
    def setTarget(self, target):
        """Set the target object to call methods for
        
        Call this method with target as the real Mind
        """
        del MindProxy.__getattr__
        for method, method_obj in inspect.getmembers(target):
            if inspect.ismethod(method_obj):
                setattr(self, method, method_obj)
        # Flush RMI queue
        for attrname, args, kwargs in self._rmi_wait:
            print '>> Flusing', attrname
            attr = getattr(self, attrname)
            attr(*args, **kwargs)
        del self._rmi_wait
    

class LoginDialog(GWidget):
    """LoginDialog.

    After logging in,

    self.user_type will be one of 'team', 'judge', 'admin'
    self.perspective is the perspective
    """
    
    GLADE_FILE = join(paths.DATA_DIR, 'glade', 'logindialog.glade')
    TOPLEVEL_WIDGET = 'wind_main'
    
    def __init__(self, cb_func):
        """
        @param cb_func: Function that will be passed the perspective
                        and user_type after successful login
        """
        self.cb_func = cb_func
        super(LoginDialog, self).__init__(self)
        self._statuscontext = self['statusbar'].get_context_id('Login dialog')
    
    def on_quit(self, *args):
        GWidget.on_quit(self)
        gtk.main_quit()
    
    def setStatus(self, msg):
        """Set the statusbar message"""
        self['statusbar'].push(self._statuscontext, msg)
        
    def on_but_login__clicked(self, button, *args):
        identity = self['ent_identity'].get_text()
        password = self['ent_password'].get_text()
        self.identity = identity
        # TODO: Get host, port from user
        #host = 'localhost'
        host = self['ent_hostname'].get_text().strip()
        port = self['ent_port'].get_text().strip()
        try:
            port = int(port)
            if port < 1024:
                raise ValueError, 'port must be positive number > 1024'
        except ValueError:
            util.msg_dialog('Enter valid port greater than 1024',
                            gtk.MESSAGE_ERROR)
            self['ent_port'].set_text('')
            return
        #host = 'cs.annauniv.edu'
        #port = 8800
        self.mind_proxy = MindProxy()
        if not identity or not password:
            self.setStatus('Please fill both the fields')
            return
        self.setStatus('Logging in ...')
        button.set_sensitive(False)
        # Login using pb
        f = pb.PBClientFactory()
        self.factory = f
        from twisted.internet import reactor
        reactor.connectTCP(host, port, f)
        creds = credentials.UsernamePassword(identity, password)
        f.login(creds, self.mind_proxy
            ).addCallbacks(self._cbGotPerspective, self._ebFailedLogin
            ).setTimeout(TIMEOUT
            )
        self.setStatus("Contacting server...")
        
    def _cbGotUserType(self, user_type):
        self.user_type = user_type
        self.setStatus('Logged in')
        reactor.callLater(0, self.cb_func, self.perspective, self.identity,
                            self.user_type, self.mind_proxy, 
                            self.factory.disconnect)
        self.widget.destroy()
    
    def _cbGotPerspective(self, perspective):
        self.perspective = perspective
        # Get the user type
        perspective.callRemote('whoami'
            ).addCallbacks(self._cbGotUserType, self._ebFailedLogin
            ).setTimeout(TIMEOUT
            )
        self.setStatus('Getting authorization information ...')
        
    def _ebFailedLogin(self, reason):
        self.setStatus('Login failed')
        reason = str(reason)
        util.msg_dialog(reason)
        self['but_login'].set_sensitive(True)
