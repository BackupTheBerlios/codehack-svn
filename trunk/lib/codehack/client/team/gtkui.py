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

"""Team GTK+ GUI"""

import os.path
from os.path import join
import gtk
import gobject
import time

from codehack import paths, util
from codehack.gwidget import GWidget, autoconnect_signals_in_class
from codehack.client import gui

# TODO: refactor this (gui configuration?)
VBOX_SPACING=6


class ProblemPanel(gtk.VBox):
    """GUI for problem
    
    For a list of problems, a list of problem-panels will be created
    and added to the toplevel VBox"""
    
    # Label markup templates
    MRKUP_NAME = '<b>%s</b>'
    MRKUP_DESC = '<i>%s</i>'
    
    def __init__(self, gui, pr_no, pr_text=None, pr_status='New'):
        super(ProblemPanel, self).__init__(spacing=VBOX_SPACING)
        self.gui = gui
        self.info = gui.info
        self.pr_no = pr_no
        self.pr_text = pr_text
        self.pr_status = pr_status
        pr_text = '%d. %s' % (pr_no, pr_text )
        self.lbl_name = gtk.Label(self.MRKUP_NAME % (pr_text or 'Problem [no]'))
        self.lbl_name.set_use_markup(True)
        self.lbl_name.set_alignment(0, 0.5)
        self.lbl_status = gtk.Label(
                self.MRKUP_DESC % (pr_status))
        self.lbl_status.set_use_markup(True)
        self.lbl_status.set_alignment(0, 0.5)
        but_box = gtk.HButtonBox()
        but_box.set_layout(gtk.BUTTONBOX_START)
        
        # Add buttons
        ex_buttons = { # key, label_name
            'submit': 'Submit',
            #'view_stat': 'View stats'
        }
        buttons = {}
        for but_name, but_lbl in ex_buttons.items():
            but = gtk.Button(but_lbl)
            but.set_relief(gtk.RELIEF_NONE)
            buttons[but_name] = but
            but_box.add(but)
        autoconnect_signals_in_class(buttons.__getitem__, self)
        for item in [self.lbl_name, self.lbl_status, but_box]:
            self.pack_start(item, expand=False)
        
        self.pack_start(gtk.HSeparator())
        # Directory of last selected program
        self.selection_directory = os.path.abspath(os.path.curdir)  
        
    def set_status(self, status):
        "Set problem status"
        self.pr_status = status
        self.lbl_status.set_markup(self.MRKUP_DESC % status)
        
    def _get_language(self, filename):
        "Return the corresponding language for extension"
        if not filename or not os.path.isfile(filename):
            return None # not a file
        ext = os.path.splitext(filename)[1][1:]
        for lang, extensions in self.info['languages'].items():
            if ext in extensions:
                return lang
        return None
        
    def _get_filename_from_user(self):
        "Return user seleted file"
        dialog = gtk.FileChooserDialog("Choose program to send ...",
            self.gui.widget, gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        # TODO: how to set custom label for 'Open' button?
        dialog.set_default_response(gtk.RESPONSE_OK) 
        # set last opened directory
        dialog.set_current_folder(self.selection_directory)

        # show preview widget - file info, lang, problem
        info = gtk.Label('')
        dialog.set_preview_widget(info)
        def sel_changed(wid, *args):
            filename = wid.get_preview_filename()
            lang = self._get_language(filename)
            info.set_markup("<b>%s</b>\n<i>%s</i>" % (self.pr_text,
                            lang or '(Invalid)'))
        dialog.connect('selection-changed', sel_changed)
        
        # Extension filters
        # TODO: set filter for each language supported
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        dialog.add_filter(filter)
        response = dialog.run()
        filename = dialog.get_filename()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            # save selection directory for future use
            directory = os.path.split(filename)[1]
            self.selection_directory = os.path.abspath(directory)
            return filename
        elif response == gtk.RESPONSE_CANCEL:
            return None
        
    def on_submit__clicked(self, but, *args):
        filename = self._get_filename_from_user()
        if filename is None:
            return
        # save directory for future use
        self.selection_directory = os.path.split(filename)[0]
        language = self._get_language(filename)
        # On invalid extension, show msg and return
        if language is None:
            ext_info = '\n'.join(
                [x+': '+str(y) for x,y in self.info['languages'].items()]
            )
            util.msg_dialog('Invalid file extension' + \
                            '\n\n' + \
                            'File extensions allowed are:\n' + \
                            ext_info, gtk.MESSAGE_ERROR)
            return
        def done(result):
            #if result:
            #    util.msg_dialog('Ok')
            #else:
            #    util.msg_dialog('Something Wrong!!')
            pass
        self.gui.call_remote('Submitting %s' % filename, done, 
                            'submit_problem',
                         self.pr_no, file(filename).read(), language)


class TeamSubmissions(object):
        
    "Object representing all submissions of a team"
    
    # possible values in self.problem_result
    PR_NEW = "New"      # Yet to submit
    PR_ACC = "Accepted" # Submitted and accepted
    # positive value indicated number of failed attempts
    
    def __init__(self, gui):
        self.gui = gui
        self._initialize()
        self._create_gui()
        
    def _create_gui(self):
        # Runs list [no., Problem name, 
        liststore = gtk.ListStore(
                        str, # no.
                        str, # Problem name
                        str, # Result
                        str, # Language
                        str, # Timestamp
                    )
        view = gtk.TreeView(model=liststore)
        view.set_headers_clickable(True)
        index = 0
        for cName in ('No', 'Problem', 'Result', 'Language', 'Timestamp'):
            cell = gtk.CellRendererText()
            tvcolumn = gtk.TreeViewColumn(cName, cell, text=index)
            index = index + 1
            view.append_column(tvcolumn)
        sw = self.gui['runs_sw']
        sw.add_with_viewport(view)
        sw.show_all()
        self.runs = liststore
        
    def _initialize(self):
        if self.gui.info.has_key('problems'):
            self.nr_problems = len(self.gui.info['problems'])
        else:
            self.nr_problems = 0
        # We maintain different view of runs
        #
        
        # problem_no => [(ts, result)]
        self.runs_problem = dict([(x,[]) for x in range(self.nr_problems)])
        # (ts, problem_no, result)
        self.runs_all = []
        # problem_no => PR_*
        self.problem_result = dict([(x,self.PR_NEW) for x in range(self.nr_problems)] )
    
    def set_submissions(self, submissions):
        """Update list of submissions.
        
        submissions is list of (timestamp, pr_no, result)
        """
        self._initialize()
        self.runs_all = submissions[:]
        for ts, pno, lang, result in submissions:
            assert pno < self.nr_problems
            self.runs_problem[pno].append( (ts, lang, result) )
        for pno, runs in self.runs_problem.items():
            for ts, lang, result in runs:
                if result == self.gui.info['result_acc_index']:
                    self.problem_result[pno] = self.PR_ACC
                    break
                if self.problem_result[pno] == self.PR_NEW:
                    self.problem_result[pno] = 1
                else:
                    self.problem_result[pno] = self.problem_result[pno] + 1
        # update UI
        #
        
        # ProblemPanel
        for no, pp in self.gui.problem_panels.items():
            res = self.problem_result[no]
            if type(res) is int:
                res = '%d unaccepted submissions' % res
            pp.set_status(res)
            
        # Runs list
        self.runs.clear()
        run_no = 1
        for ts, pno, lang, result in submissions:
            pname = self.gui.info['problems'][pno]
            result = self.gui.info['results'][result]
            result = result.split('-',1)[0].strip()
            ts = str(ts)
            lang = lang
            row = [str(run_no), pname, result, lang, ts]
            self.runs.append(row)
            run_no = run_no + 1

class TeamGUI(gui.ClientGUI):
    
    GLADE_FILE = join(paths.DATA_DIR, 'glade', 'team.glade')
    TOPLEVEL_WIDGET = 'wind_main'

    def __init__(self, perspective, userid, disconnect):
        super(TeamGUI, self).__init__(perspective, 'Team', userid, disconnect)
        self.userid = userid
        self.info = {} # Contest info
        self.submissions = TeamSubmissions(self) # List of submissions (ts, pr_no, result)
        self.__problems_widget = None
        self._update_ui(False)
        self._initialize()

    def _update_submissions(self):
        def done(result):
            self.callLater(self.submissions.set_submissions, result)
         
        self.call_remote_sync('Updating submissions', done, 
                         'get_submissions')

    def show_result(self, problem , lang, ts, result):
        text = 'Result for %s\n\n%s\n\nLang: %s\nTime: %d'
        text = text % (self.info['problems'][problem],  
                       self.info['results'][result],
                       self.info['languages'][lang],
                       ts)
        self._update_submissions()
        util.msg_dialog(text)

    def update_info(self, name, details):
        "Update self.info from contest details tuple"
        self.info['name'] = name
        if details is None:
            for ky in ('duration', 'age', 'problems', 'languages', 'results', 'result_acc_index'):
                self.info[ky] = None
            return
        duration, age, problems, results, languages, result_acc_index = details
        self.info['duration'] = duration
        self.info['age'] = age
        self.info['problems'] = problems
        self.info['languages'] = languages
        self.info['results'] = results
        self.info['result_acc_index'] = result_acc_index
    
    def contest_started(self, name, details):
        self.update_info(name, details)
        self._update_ui(True, name)
    
    def contest_stopped(self):
        "Called by mind on stop of contest"
        self.update_info(None, None)
        self._update_ui(False)

    def _update_ui(self, isrunning, name=None):
        "Change widget attributes based on whether contest is running or not"
        if isrunning is False:
            self.contest_time(0, None)
        else:
            self.contest_time(time.time() - self.info['age'], 
                                self.info['duration'])
        info = '<b>%sContest is%s running</b>'
        if isrunning:
            info = info % ('%s: ' % name, '')
            self.show_problems()
        else:
            info = info % ('', ' NOT')
            self.unshow_problems()
        self['lbl_contest'].set_markup(info)
        self['nb'].set_sensitive(isrunning)

    def show_problems(self):
        # add ProblemPanel
        problems = self.info['problems']
        problem_panels = {}
        vbox = gtk.VBox(spacing=12)
        for no, problem in zip(range(0, len(problems)), problems):
            pp = ProblemPanel(self, no, problem)
            problem_panels[no] = pp
            vbox.pack_start(pp, expand=False)
        sw = self['pr_sw']
        sw.add_with_viewport(vbox)
        sw.show_all()
        self.__problems_widget = vbox
        self.problem_panels = problem_panels
        self._update_submissions()

    def unshow_problems(self):
        if self.__problems_widget:
            children = self['pr_sw'].get_children()
            self['pr_sw'].remove(children[0])
            self.__problems_widget = None
            self.problem_panels = None

    def _initialize(self):
        def done(result):
            isrunning, name, details = result
            if isrunning:
                self.contest_started(name, details)
            else:
                self.contest_stopped()
            
        self.call_remote('Getting contest information', done, 
                         'get_contest_info')

    def on_but_logout__clicked(self, *args):
        self.on_quit()
        print 'All the best'
