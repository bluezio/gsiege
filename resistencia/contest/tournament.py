# -*- coding: utf-8 -*-

###############################################################################
# This file is part of Resistencia en Cadiz: 1812.                            #
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

import math
import random

import gtk

from resistencia import configure, filenames

import round
import logging
import contest
import controlPartida

def isPowerTwo(num):
	return num != 0 and ((num & (num - 1)) == 0)

def closest_power2(num):
    exponente = math.ceil(math.log(num, 2))
    return math.pow(2, exponente)

def _auto_pairings(equiposIniciales):

    # Guardamos el número de equipos
    numEquiposIniciales = len(equiposIniciales)

    pairing = []
    equiposTotales = []

    # Si el número de equipos es una potencia de dos, la agrupación es trivial
    if isPowerTwo(numEquiposIniciales):
        equiposTotales = equiposIniciales[:]
    else:
        # Si no es una potencia de dos, hay que conseguir un número potencia de
        # dos de partidos en la primera eliminatoria para evitar que aparezcan
        # equipos fantasma en etapas posteriores

        # El número de partidos será la potencia de dos más cercana (por arriba)
        # a la mitad del número de equipos
        numPartidos = int(closest_power2(math.ceil(numEquiposIniciales / 2.0)))
        
        # Calculamos el número de equipos necesarios, que son dos por partido
        numEquiposNecesarios = numPartidos * 2

        # El número de equipos fantasma a añadir será la diferencia con el
        # número de equipos reales
        numEquiposFantasma = numEquiposNecesarios - numEquiposIniciales        
        # equiposFantasma = ['aux_ghost_team'] * numEquiposFantasma

        i = 0
        for i in range(numEquiposFantasma):
                equiposTotales.append(equiposIniciales[i])
                equiposTotales.append("aux_ghost_team")

        equiposTotales = equiposTotales + equiposIniciales[i+1:]        

    for q in range(0, len(equiposTotales), 2):
            pairing.append((equiposTotales[q], equiposTotales[q+1]))

    return pairing

def _extract_teams_from_pairing(elements):
    teams = []
    for i in elements:
        teams.append(i[0])
        teams.append(i[1])

class Tournament(contest.Contest):
    def __init__(self, teams, num_turns, pairings_done=False, log_folder = None):
            
        self.matchs = []
        self.teams = []
        self.round_winners = []
        self.round_reasons = []
        self.num_turns = num_turns

        self.log_folder = log_folder

        if pairings_done:
            self.matchs.append(teams)
            self.teams = _extract_teams_from_pairing(self.matchs)
        else:
            self.teams = teams

        self.translator = contest.generate_key_names(self.teams)
        self.keys = []

        for t in self.translator:
            self.keys.append(t)

        
        random.shuffle(self.keys)

        if not pairings_done:
            self.matchs.append(_auto_pairings(self.keys))

        self.current_round = 0
        self.rounds = []

        self.rounds.append(round.Round(self.matchs[self.current_round],
                                       self.translator,
                                       self.num_turns))

        self.number_of_rounds = int(math.log(len(self.matchs[0]), 2)) + 1
        
        logging.info("Torneo creado")
        logging.info("%s partidos en la primera ronda", str(len(self.matchs[0])))
        logging.info("%s rondas totales", str(self.number_of_rounds))

    def play_round(self, progress_bar, fast=False):
        if not controlPartida.flagCancelarCampeonato:
            r = self.rounds[self.current_round]
            n = r.get_number_of_games()

            for i in range(n):
                if controlPartida.flagCancelarCampeonato:
                        return

                if fast and progress_bar != None:
                    progress_bar.pulse()
                    while gtk.events_pending():
                        gtk.main_iteration(False)

                r.play_match(fast, True, log_folder = self.log_folder)

            winners = r.get_winners()
            reasons = r.get_reasons()
            self.round_winners.append(winners)
            self.round_reasons.append(reasons)

            self.current_round = self.current_round + 1
            self.league_completed = (self.current_round == self.number_of_rounds)

            if not self.league_completed:
                self.matchs.append(_auto_pairings(winners))
                self.rounds.append(round.Round(self.matchs[self.current_round],
                                               self.translator))

    def get_results_by_now(self):
        return self.round_winners



