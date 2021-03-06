# -*- coding: utf-8 -*-
###############################################################################
# This file is part of Resistencia Cadiz 1812.                                #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# any later version.                                                          #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
# Copyright (C) 2010, Pablo Recio Quijano, <pablo.recioquijano@alum.uca.es>   #
###############################################################################

import os.path

import gtk

import time
import types

from guadaboard import guada_board
from resistencia import configure, xdg, filenames
from resistencia.tests import tests, selection
from resistencia.nls import gettext as _
from resistencia.gui import progress_bar_dialog as pbs
from libguadalete.parsear_fichero_reglas import leer_comentario
import tests_result

def _clean_dictionary(d):
    if type(d) == types.ListType:
        return d
    else:
        l = []
        for k in d:
            l.append(d[k])
            
        return l

class testDialog:
    # --- List and handler functions
    def addColumn(self, title, columnId):	
        column = gtk.TreeViewColumn(title, gtk.CellRendererText(),
                                    text=columnId)
        self.list_view.append_column(column)

    def file_chooser_rules_handler(self):
        self.rules_selected_file = self.file_chooser_rules.get_filename()
        assert(not(self.rules_selected_file == None))

    def file_chooser_formation_handler(self):
        self.formation_selected_file = self.file_chooser_formation.get_filename()
        assert(not(self.formation_selected_file == None))

    def apply_file_chooser_rules(self):

        self.file_chooser_rules_handler()
        self.file_chooser_rules.hide()

        if self.check_default_formations.get_active():
            self.formation_selected_file = filenames.devolverFormacionAsociada(self.file_chooser_rules.get_filename())[7:]
            self.tests_dialog.show()
            self.insert_element_list()
        else:
            self.file_chooser_formation.run()

    def apply_file_chooser_formation(self):
        self.file_chooser_formation_handler()
        self.file_chooser_formation.hide()
        self.tests_dialog.show()
        self.insert_element_list()

    def insert_element_list(self):
        s, rules_file_name = os.path.split(self.rules_selected_file)
        s, formation_file_name = os.path.split(self.formation_selected_file)
        self.files[rules_file_name] = self.rules_selected_file
        self.files[formation_file_name] = self.formation_selected_file

        name = filenames.extract_name_expert_system((rules_file_name,
                                                     formation_file_name))

        if not self.teams.has_key(name):
            self.teams[name] = (self.rules_selected_file, self.formation_selected_file)

            self.list_store.append((name, rules_file_name, formation_file_name, leer_comentario(self.rules_selected_file, wrap = False)))
            if len(self.teams) == 2:
                self.start_button.set_sensitive(True)
    # ---
    
    def __init__(self, parent):
        self.rules_main_team = ''
        self.formation_main_team = ''
        self.files = {}
        self.teams = {}

        builder = gtk.Builder()
        builder.add_from_file(xdg.get_data_path('glade/testDialog.glade'))

        self.tests_dialog = builder.get_object('tests_dialog')
        self.tests_dialog.set_transient_for(parent)

        # ---- Init file chooser buttons
        self.def_path = configure.load_configuration()['se_path']
        default_rules_path = self.def_path + '/rules'
        default_formations_path = self.def_path + '/formations'
        
        self.btn_rules = builder.get_object('btn_filechooser_rules')
        self.btn_formation = builder.get_object('btn_filechooser_formation')
        
        builder.get_object('btn_filechooser_rules').set_current_folder(default_rules_path)
        builder.get_object('btn_filechooser_formation').set_current_folder(default_formations_path)
        # ----

        self.num_rounds = 2
        self.spin_rounds = builder.get_object('spin_rounds')
        self.spin_rounds.set_range(2, 100)
        self.spin_rounds.set_increments(2,10)
        self.spin_rounds.set_value(self.num_rounds)
        
        self.num_turns = 120
        self.spin_turns = builder.get_object("spin_num_turns")
        self.spin_turns.set_range(50,300)
        self.spin_turns.set_increments(2,10)
        self.spin_turns.set_value(self.num_turns)

        self.all_teams = False
        self.frame_selection_teams = builder.get_object('frame_es_selection')

        self.start_button = builder.get_object('btn_apply')
        self.start_button.set_sensitive(False)
        
        #---------------------------
        self.cName = 0
        self.cRules = 1
        self.cFormation = 2
        
        self.sName = _("Name")
        self.sRules = _("Rules")
        self.sFormation = _("Formation")
        
        self.list_view = builder.get_object("list_es_view")
        self.list_view.set_reorderable(False)

        self.addColumn(self.sName, self.cName)
        self.addColumn(self.sRules, self.cRules)
        self.addColumn(self.sFormation, self.cFormation)
        self.addColumn(_("Description"), 3)

        self.list_store = builder.get_object("list_expert_system")
        #-----------------------------
        self.file_chooser_rules = builder.get_object('file_chooser_rules')
        self.file_chooser_formation = builder.get_object('file_chooser_formation')
        self.file_chooser_rules.set_current_folder(default_rules_path)
        self.file_chooser_formation.set_current_folder(default_formations_path)

        
        self.error_es = builder.get_object("error_no_es")
        self.error_es.connect('response', lambda d, r: d.hide())
        self.error_es.set_transient_for(self.tests_dialog)
        
        self.error_team = builder.get_object("error_no_team")
        self.error_team.connect('response', lambda d, r: d.hide())
        self.error_team.set_transient_for(self.tests_dialog)

        self.progress_bar = pbs.ProgressBarDialog(self.tests_dialog,
                                                  _('Running the test'))
        self.progress_bar_dialog = self.progress_bar.progress_bar_dialog

        self.check_default_formations = builder.get_object('check_default_formations')
        self.label_description = builder.get_object('label_description')

        builder.connect_signals(self)
    
    def on_tests_dialog_close(self, widget, data=None):
        """
        Function that handles the closing event of the dialog
        """
        self.tests_dialog.hide()

    def on_btn_filechooser_rules_file_set(self, widget, data=None):
        self.rules_main_team = widget.get_uri().replace('file://','')
        
        formacionAsociada = filenames.devolverFormacionAsociada(widget.get_uri())
        self.label_description.set_label(leer_comentario(widget.get_filename()))

        if formacionAsociada != None:			
            self.btn_formation.set_uri(formacionAsociada)
            self.formation_main_team = self.btn_formation.get_uri().replace('file://','')
    
    def on_btn_filechooser_formation_file_set(self, widget, data=None):
        self.formation_main_team = widget.get_uri().replace('file://','')

    def on_spin_rounds_change_value(self, widget, data=None):
        self.num_rounds = int(widget.get_value())

    def on_spin_rounds_value_changed(self, widget, data=None):
        self.num_rounds = int(widget.get_value())

    def on_spin_num_turns_change_value(self, widget, data=None):
        self.num_turns = int(widget.get_value())

    def on_spin_num_turns_value_changed(self, widget, data=None):
        self.num_turns = int(widget.get_value())

    def on_check_all_teams_toggled(self, widget, data=None):
        self.all_teams = widget.get_active()
        if self.all_teams:
            self.frame_selection_teams.set_sensitive(False)
            self.start_button.set_sensitive(True)
        else:
            self.frame_selection_teams.set_sensitive(True)
            if len(self.teams) >= 2:
                self.start_button.set_sensitive(True)
            else:
                self.start_button.set_sensitive(False)
            

    def on_list_es_view_cursor_changed(self, widget, data=None):
        self.treeiter = self.list_store.get_iter(widget.get_cursor()[0])        

    def on_btn_add_clicked(self, widget, data=None):
        self.file_chooser_rules.connect('response', lambda d, r: d.hide())
        #self.tests_dialog.hide()
        self.file_chooser_rules.run()
        
    def on_btn_remove_clicked(self, widget, data=None):
        del self.teams[self.list_store.get_value(self.treeiter, 0)]
        self.list_store.remove(self.treeiter)
        if len(self.teams) == 1:
            self.start_button.set_sensitive(False)

    def on_btn_formation_clicked(self, widget, data=None):
        self.rules_selected_file = self.def_path + "/rules/" + self.list_store.get_value(self.treeiter, 1)
        self.tests_dialog.hide()
        self.on_btn_remove_clicked(None)
        self.file_chooser_formation.show()

    
    def on_btn_file_chooser_rules_apply_clicked(self, widget):
        self.apply_file_chooser_rules()

    def on_file_chooser_rules_file_activated(self, widget):
        self.apply_file_chooser_rules()

    def on_btn_file_chooser_rules_close_clicked(self, widget):
        self.file_chooser_rules.hide()
        self.tests_dialog.show()
        del self.rules_selected_file

    def on_btn_file_chooser_formation_apply_clicked(self, widget):
        self.apply_file_chooser_formation()

    def on_file_chooser_formation_file_activated(self, widget):
        self.apply_file_chooser_formation()

    def on_btn_file_chooser_formation_close_clicked(self, widget):
        self.file_chooser_formation.hide()
        del self.rules_selected_file
        del self.formation_selected_file
    
    def on_btn_cancel_clicked(self, widget, data=None):
        self.tests_dialog.hide()

    def on_btn_apply_clicked(self, widget, data=None):
        correct = True
        if len(self.rules_main_team) == 0:
            self.error_es.run()
            correct = False
        if len(self.formation_main_team) == 0:
            self.error_team.run()
            correct = False

        if correct:
            main_team = (self.rules_main_team, self.formation_main_team)

            if self.all_teams:
                self.teams = selection.get_installed_teams()

            self.progress_bar.set_num_elements(self.num_rounds * len(self.teams))
            t = tests.TestSuite(main_team, _clean_dictionary(self.teams),
                                self.num_rounds, self.num_turns)
            self.progress_bar_dialog.show()
            while gtk.events_pending():
                gtk.main_iteration(False)
            t.run_test_suite(self.progress_bar)
            team = filenames.extract_name_expert_system(main_team)

            test = tests_result.testResult(t.get_test_stats(), team)
            self.progress_bar_dialog.hide()
            test.test_result.run()
            self.tests_dialog.destroy()

