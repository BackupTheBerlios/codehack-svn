# Copyright (C) 2004 R. Sridhar <sridharinfinity AT users DOT sf DOT net>.
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

"""Client side database edit widget"""

import gtk

from codehack import util


class DBEdit(gtk.HBox):
    """Widget to edit database from twisted client side broker
    
    1. Create DBEdit instance
    2. add_column() to add columns
    3. create() to create widgets
    4. populate() to populate the view with table row    
    """
    
    # Button labels
    LBL_CREATE = 'Create'
    LBL_EDIT = 'Update'
    
    def __init__(self, table, call_remote_func, sec_key, 
                 readonly=lambda x:False):
        """
        @param table:            Name of the table
        @param call_remote_func: A funtion that takes the following arguments
            1. desc - Description of current operation (shown in statusbar)
            2. done - callback to be called on deferred (final callback)
            3. method - remote method name
        followed *args, **kwargs passed to that remote method
        @param sec_key:  Secondary key for table
        @param readonly: Funtion that returns true if TID is readonly
        
        $(table_name)_X where X is {get_all, get, update, add, remove) represent
        the remote methods.
        
        TID (tid) is a generic name - Table Information Dictionary
        """
        super(DBEdit, self).__init__(spacing=6)
        self.set_spacing(6)
        self.set_border_width(6)
        self.table = table
        self.call_remote = call_remote_func
        self.is_readonly_tid = readonly
        self.sec_key = sec_key
        self.columns = {} # Columns
        d = {}
        d['type'] = int()
        d['name'] = 'ID'
        d['view'] = False
        self.columns['id'] = d
        self.tv_indices = {} # ID -> index in treeview column

    def show_all(self):
        gtk.HBox.show_all(self)
        self._fields_visible(False)
        
    def add_column(self, key, key_typ, name, view=False):
        """Add new column of database table
        
        @param key:  The corresponding key to be passed in ID (Information dictionary)
        @param key_typ: is the type of `key`, specified as an instance of that type
        @param name: Descriptive name
        @param view: whether it will be visible in list view
        """
        d = {}
        self.columns[key] = d
        d['type'] = key_typ
        d['name'] = name
        d['view'] = view
        self.readonly_keys = ['id'] # cannot be edited
        
    def create(self, column_order):
        """Create children widgets.
        Must be called after all 'add_column'
        
        @param column_order: List of key (ID) specifying the 
                             column order in view
        """
        
        # Left - Table View
        # 
        
        # ScrolledWindow
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.pack_start(sw)
        
        # TreeView
        
        # 'id' must be first in order
        if 'id' not in column_order:
            column_order.insert(0, 'id')
        column_order_orig = column_order[:]
        
        # column_order list may not be complete, so we complete it
        for x in self.columns.keys():
            if x not in column_order_orig:
                column_order.append(x)
        self.column_order = column_order
        model_id = column_order
        model_id_type = map(lambda x: type(self.columns[x]['type']), model_id)
        l = []
        for x in model_id_type: # convert to tuple (enum) to str (match render)
            if x is tuple:
                x = str
            l.append(x)
        model_id_type = l
        tm = gtk.ListStore(*model_id_type)
        tv = gtk.TreeView(tm)
        
        # hash of key => index in TreeView
        self.tv_indices = dict(zip(model_id, range(len(model_id))))
        
        # create TV columns
        for key in model_id:
            if self.columns[key]['view']:
                index = self.tv_indices[key]
                title = self.columns[key]['name']
                typ = self.columns[key]['type']
                cell = gtk.CellRendererText()
                column = gtk.TreeViewColumn(title, cell, text=index)
                tv.append_column(column)
        sw.add_with_viewport(tv)
        
        # Multiple selection mode for TreeView
        sel = tv.get_selection()
        sel.set_mode(gtk.SELECTION_MULTIPLE)
        
        # Right - Manage rows
        # 
        
        # Frame
        frame = gtk.Frame('Manage '+self.table)
        
        vbox = gtk.VBox()
        frame.add(vbox)
        
        # add, edit
        hbutbox = gtk.HButtonBox()
        hbutbox.set_border_width(6)
        hbutbox.set_layout(gtk.BUTTONBOX_SPREAD)
        hbutbox.set_spacing(6)
        but_add = gtk.Button(stock=gtk.STOCK_ADD)
        but_edit = gtk.Button(stock=gtk.STOCK_JUSTIFY_FILL)
        but_edit.set_label('Edit selected')
        map(hbutbox.add, [but_add, but_edit])
        vbox.pack_start(hbutbox, expand=False)
        
        # edit table
        tbl = gtk.Table(
            rows=1+len(self.columns),  # columns + update,cancel buttons
            columns=2,                 # label + edit widget
        )
        tbl.set_border_width(6)
        tbl.set_row_spacings(6)
        tbl.set_col_spacings(12)
        tbl_items = {} # key(l,r,t,b) => wid
        
        st_row = 1
        wid_fields = {}  # edit widgets
        for key in self.column_order:
            key_dict = self.columns[key]
            name = key_dict['name']
            typ = key_dict['type']
            lbl = gtk.Label(name+':')
            if type(typ) is str or type(typ) is int:
                if key in self.readonly_keys:
                    wid = gtk.Label()
                else:
                    wid = gtk.Entry()
                wid_fields[key] = wid
            elif type(typ) is tuple: # like enum (eg. team, judge)
                # radio buttons
                button = None
                buttons = []
                hbox = gtk.HBox()
                for enum in typ:
                    button = gtk.RadioButton(button, enum)
                    buttons.append(button)
                    hbox.pack_start(button)
                wid = hbox
                wid_fields[key] = tuple(buttons)
            else:
                raise AssertionError, '%s is not valid type' % str(type(typ))
            
            tbl_items[(0,1,st_row, st_row+1)] = lbl
            tbl_items[(1,2,st_row, st_row+1)] = wid
            st_row = st_row + 1
        
        for (l,r,t,b), wid in tbl_items.items():
            tbl.attach(wid, l,r,t,b)
            
        # update/add, cancle
        hbutbox = gtk.HButtonBox()
        hbutbox.set_layout(gtk.BUTTONBOX_SPREAD)
        but_done = gtk.Button(stock=gtk.STOCK_ADD)
        but_cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        map(hbutbox.add, [but_done, but_cancel])
        tbl.attach(hbutbox, 0,2, st_row, st_row+1)
        
        vbox.pack_start(tbl, expand=False, fill=True)
        
        # Divider
        sep = gtk.HSeparator()
        vbox.pack_start(sep, expand=False)
        
        # Delete button
        hbutbox = gtk.HButtonBox()
        hbutbox.set_border_width(6)
        hbutbox.set_layout(gtk.BUTTONBOX_SPREAD)
        but_delete = gtk.Button(stock=gtk.STOCK_DELETE)
        but_delete.set_label('Delete selected')
        hbutbox.add(but_delete)
        vbox.pack_start(hbutbox, expand=False)
        
        self.pack_start(frame, expand=False)
        
        # Store widgets 
        self.but_add = but_add
        self.but_edit = but_edit
        
        self.but_done = but_done
        self.but_cancel = but_cancel
        
        self.but_delete = but_delete
        
        self.tv = tv    # DB List view
        self.tm = tm
        
        self.tbl = tbl
        self.wid_fields = wid_fields
        
        for widname in [
            'but_add', 'but_edit', 'but_done', 'but_cancel', 'but_delete'
        ]:
            wid = getattr(self, widname)
            hdlr_name = 'on_%s__clicked' % widname
            hdlr = getattr(self, hdlr_name)
            wid.connect('clicked', hdlr)
            
    # END of self.create()
    
    def populate(self):
        """Populate the list view with rows from database server"""
        def got_rows(tids):
            for id, tid in tids.items():
                self.ui_list_add(tid)
        self.call_remote(
            'Getting %s list' % self.table,
            got_rows,
            self._rmfunc('get_all')
        )
    
    # Account management callbacks
    def on_but_add__clicked(self, but, *args):
        self._fields_visible(True, self.LBL_CREATE)
        self._fields_init()
            
    def on_but_edit__clicked(self, but, *args):
        tids = self._tv_get()
        # Editting operation can be done only if exactly 1 row is selected
        if len(tids) != 1:
            util.msg_dialog('Select exactly one row')
            return
        tid = tids.values()[0]
        # Readonly row cannot be edited
        if self.is_readonly_tid(tid):
            util.msg_dialog('Readonly entries cannot be edited')
            return
        self._fields_visible(True, self.LBL_EDIT)
        self._fields_put(tid)
        
    def on_but_done__clicked(self, but, *args):
        tid = self._fields_get()
        # TODO: Input validation
        
        if but.get_label() == self.LBL_CREATE:
            # Add to table
            def cb_done(result):
                # Now get the id
                def cb_id_done(_tid):
                    self._fields_visible(False)
                    tid['id'] = _tid['id']
                    self.ui_list_add(tid)
                    
                self.call_remote(
                    'Receiving id for added %s' % self.table, cb_id_done,
                    self._rmfunc('get'), tid[self.sec_key]
                )
            self.call_remote(
                'Adding new %s' % (self.table),
                cb_done,
                self._rmfunc('add'), tid
            )
        elif but.get_label() == self.LBL_EDIT:
            # Update current row
            def cb_done(result):
                self._fields_visible(False)
                self.ui_list_update(tid)
            self.call_remote(
                'Updating information for %s "%s"' % (self.table, tid['id']),
                cb_done,
                self._rmfunc('update'), tid
            )
        else:
            raise RuntimeError, 'Invalid button text [%s] for but_done' % \
                but.get_label()
        
    def on_but_cancel__clicked(self, but, *args):   
        self._fields_visible(False)
        
    def on_but_delete__clicked(self, but, *args):
        tids = self._tv_get()
        if len(tids) == 0:
            util.msg_dialog('Select atleat one row to delete')
            return
        # Readonly row cannot be edited
        if True in map(self.is_readonly_tid, tids.values()):
            util.msg_dialog('You selected atleast one readonly entry. Deselect it')
            return
        def cb_done(result):
            self.ui_list_remove(tids.keys())
        self.call_remote(
            'Removing %d %s' % (len(tids), self.table),
            cb_done,
            self._rmfunc('remove'),
            tids.keys()
        )

    
    # UI population functions
    def ui_list_add(self, tid):
        values = []
        for key in self.column_order:
            values.append(tid[key])
        self.tm.append(values)
        
    def ui_list_update(self, tid):
        sel = self.tv.get_selection()
        model, pathlist = sel.get_selected_rows()
        assert len(pathlist) == 1 , 'Expecting single selected row'
        iter = model.get_iter(pathlist[0])
        assert model.get_value(iter, self.tv_indices['id']) == tid['id']
        for key, index in self.tv_indices.items():
            model.set_value(iter, index, tid[key])
            
    def ui_list_remove(self, tids):
        iter = self.tm.get_iter_first()
        while iter:
            nextiter = self.tm.iter_next(iter) # bcoz, iter will be invalidated
            id = self.tm.get_value(iter, self.tv_indices['id']) 
            if id in tids:
                tids.remove(id)
                self.tm.remove(iter)
            iter = nextiter
        
    def show_all(self, *args):
        # Show all, but specific (supposed to be) hidden widgets
        super(DBEdit, self).show_all()
        initially_hidden = [self.tbl]
        for wid in initially_hidden:
            wid.set_property('visible', False)
        
    # utils
    def _rmfunc(self, suffix):
        return '%s_%s' % (self.table, suffix)

    def _fields_visible(self, status, done_label=''):
        """Make the Edit filelds visible or not
        
        @param status:     True/False stating visibility
        @param done_label: Label for but_done
        """
        self.but_done.set_label(done_label)
        # Lock/Unlock other widgets
        lock_widgets = ['but_add', 'but_edit', 'but_delete',
                        'tv']
        for wid in lock_widgets:
            wid = getattr(self, wid)
            wid.set_sensitive(not status)
        self.tbl.set_property('visible', status)
        
    def _fields_init(self):
        """Initialize the fields"""
        for key, wid in self.wid_fields.items():
            if type(wid) is tuple: # radio button
                wid[0].set_active(True)
            else: # possibly entry widget
                wid.set_text('')
        
    def _fields_put(self, tid):
        """Populate the filelds with tid"""
        for key, wid in self.wid_fields.items():
            if type(wid) is tuple: # enum, radio
                # get the supposed to be active radio button
                wid = filter(lambda x: x.get_label()==tid[key], wid)[0]
                wid.set_active(True)
            else:
                wid.set_text(str(tid[key]))
                
    def _fields_get(self):
        """Return the tid for data in fields"""
        tid = {}
        for key, wid in self.wid_fields.items():
            if key == 'id': # which may be optional
                txt = wid.get_text()
                try:
                    tid[key] = int(txt)
                except ValueError:
                    # probably `id` not needed for the caller 
                    # (eg. will be assigned)
                    pass
            elif type(wid) is tuple: # enum, radio
                # get the ctive radio button
                wid = filter(lambda x: x.get_active(), wid)[0]
                tid[key] = wid.get_label()
            else:
                typ = type(self.columns[key]['type'])
                tid[key] = typ(wid.get_text())
        return tid
        
    def _tv_get(self):
        """Return the TIDs of selected rows
        key(id) => TID
        """
        sel = self.tv.get_selection()
        model, pathlist = sel.get_selected_rows()
        tids = {}
        for path in pathlist:
            iter = self.tm.get_iter(path)
            tid = {}
            for key, index in self.tv_indices.items():
                tid[key] = self.tm.get_value(iter, index)
            tids[int(tid['id'])] = tid
        return tids
