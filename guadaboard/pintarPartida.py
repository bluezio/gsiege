#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
from pygame.locals import *

import sys
import pprint
import algoritmoDiferencias

# _Incluímos en el path de módulos el directorio raíz
sys.path.insert(0, "..")

from libguadalete import libguadalete, file_parser
from resistencia.xdg import get_data_path as xdg_data_path

class Boton(pygame.sprite.Sprite):
    """
    Representa un botón de la interfaz
    """

    def __init__(self, x, y, imagen, callback):
        self.callback = callback
        
        self.imagenNormal = pygame.image.load(xdg_data_path(imagen + ".png")).convert_alpha()
        self.imagenHover = pygame.image.load(xdg_data_path(imagen + "_sobre.png")).convert_alpha()
        self.imagenActive = pygame.image.load(xdg_data_path(imagen + "_pulsada.png")).convert_alpha()

        self.rect = self.imagenNormal.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.estado = "normal"

    def pintar (self, destino):
        if self.estado == "normal":
            destino.blit(self.imagenNormal, self.rect)
        elif self.estado == "hover":
            destino.blit(self.imagenHover, self.rect)

    def informarClick(self, pos):
        if self.rect.collidepoint(pos):
            self.callback()

    def informarHover(self, pos):
        if self.rect.collidepoint(pos):
            self.estado = "hover"
        else:
            self.estado = "normal"

class Ficha(pygame.sprite.Sprite):
    def __init__(self, equipo, identificador, valor, x, y, descubierta, visible = True):

        pygame.sprite.Sprite.__init__(self)

        self.x = x
        self.y = y
        self.valor = valor
        self.identificador = identificador
        self.descubierta = descubierta
        self.equipo = equipo
        self.visible = visible

        self.actualizarSuperficie()        

    def actualizarSuperficie(self):
        # Dependiendo del equipo elegiremos la pieza de un color u otro
        if self.equipo == 'A':
            imagenFicha = pygame.image.load(xdg_data_path("images/piece-orange.png"))
        else:
            imagenFicha = pygame.image.load(xdg_data_path("images/piece-violete.png"))

        # Cargamos la fuente para el rótulo con el valor de la ficha
        fuente = pygame.font.Font(xdg_data_path("fonts/LiberationMono-Bold.ttf"), 32)

        # Pintamos el rótulo en una superficie nueva
        if self.descubierta:
            imagenTexto = fuente.render("%d" % self.valor, 1, (255, 255, 255))
        else:
            imagenTexto = fuente.render("[%d]" % self.valor, 1, (255, 255, 255))

            # Bliteamos la superficie del texto en la superficie de la ficha original
        if self.descubierta:            
            imagenFicha.blit(imagenTexto, (19,11))
        else:
            imagenFicha.blit(imagenTexto, (0,11))
            
        # Asignamos a la imagen de la ficha la superficie compuesta convertida
        self.image = imagenFicha.convert()

        # El rectángulo inicialmente será el de la imagen...
        self.rect = self.image.get_rect()

        # ... pero con las coordenadas acordes a la posición de la ficha en el tablero
        self.posicionDestino = self.toGlobal()

        self.posicionActual = self.posicionDestino

        self.rect.x, self.rect.y = self.posicionActual
        self.opacidad = 255
        

    def pintar (self, destino):
        if self.visible:
            if round(self.posicionActual[0]) != round(self.posicionDestino[0]):
                variacion = (self.posicionDestino[0] - self.posicionActual[0]) / 15.0
                self.posicionActual[0] += variacion

            else:
                self.posicionActual[0] = self.posicionDestino[0]

            if round(self.posicionActual[1]) != round(self.posicionDestino[1]):
                variacion = (self.posicionDestino[1] - self.posicionActual[1]) / 15.0
                self.posicionActual[1] += variacion
            else:
                self.posicionActual[1] = self.posicionDestino[1]

        elif self.opacidad > 1:
            self.opacidad -= 10
            self.image.set_alpha(self.opacidad)
            
        self.rect.x, self.rect.y = self.posicionActual
        destino.blit(self.image, self.rect)

    def muerete(self):
        self.visible = False

    def actualizate(self, datos):
        self.posicionPrevia = self.posicionDestino
        self.x = datos[3]
        self.y = datos[4]
        
        if self.descubierta != datos[5]:
            self.descubierta = datos[5]
            self.actualizarSuperficie()
            
        self.posicionDestino = self.toGlobal()
    

    def toGlobal(self):
        return [float(10 + (self.x - 1) * 60),
                float(10 + (self.y - 1) * 60)]

class PintarPartida(object):
    
    def __init__(self, ficheroOrigen, team_a, team_b, musica, hidden=False, cant_draw=False):
        
        self.team_a = team_a
        self.team_b = team_b
        self.musica = False #musica
        self.hidden = hidden
        self.cant_draw = cant_draw

        self.fps = 100.0
        self.intervalo = 1.0 / self.fps * 1000.0
        self.ticksAnterior = pygame.time.get_ticks()

        self.fichas = {}

        self.parseador = algoritmoDiferencias.ParseadorPartida(ficheroOrigen)

        print "Init terminado!!"

    def run(self):
        # Run..."

        # Inicializando pygame..."
        pygame.init()

        if self.musica:
            _music_path = xdg_data_path('music/walking_on_old_stones.ogg')
            pygame.mixer.music.load(_music_path)
            pygame.mixer.music.play()

        tamanoVentana = (760,560)
        
        print pygame.display.mode_ok(tamanoVentana)
        
        # Estableciendo el modo de pantalla..."
        self.pantalla = pygame.display.set_mode(tamanoVentana)

        # Estableciendo el título de la ventana..."
        pygame.display.set_caption("Reproduciendo partida")

        # Cargando imagen de fondo..."
        self.imagenFondoTemp = pygame.image.load(xdg_data_path("images/fondo.png"))

        # Convirtiendo la imagen de fondo al formato adecuado..."
        self.imagenFondo = self.imagenFondoTemp.convert()

        # Parseando el estado inicial..."
        organizacionInicial = self.parseador.avanzarTurno()

        # Cargamos la imagen de los marcos con los nombres..."
        imagenMarco = pygame.image.load(xdg_data_path("images/marco.png"))
        imagenMarco = imagenMarco.convert()

        posMarcosEquipos = 50 # 198

        # Bliteamos el marco en el fondo
        self.imagenFondo.blit(imagenMarco, (510, posMarcosEquipos))
        self.imagenFondo.blit(imagenMarco, (510, posMarcosEquipos + 62))

        # Cargamos la fuente para el rótulo con el valor de la ficha
        fuenteEquipos = pygame.font.Font(xdg_data_path("fonts/zektonbi.ttf"), 18)
        
        # Renderizamos los textos en superficies
        textoEquipoA = fuenteEquipos.render(self.team_a[0][:16], 1, (255,255,255))
        sombraTextoEquipoA = fuenteEquipos.render(self.team_a[0][:16], 1, (0,0,0))
        imagenEquipoA = pygame.transform.scale(pygame.image.load(self.team_a[1]), (30,30))

        textoEquipoB = fuenteEquipos.render(self.team_b[0][:16], 1, (255,255,255))
        sombraTextoEquipoB = fuenteEquipos.render(self.team_b[0][:16], 1, (0,0,0))
        imagenEquipoB = pygame.transform.scale(pygame.image.load(self.team_b[1]), (30,30))

        # Bliteamos las superficies de los marcadores
        self.imagenFondo.blit(imagenEquipoA, (515, posMarcosEquipos + 9))
        self.imagenFondo.blit(sombraTextoEquipoA, (552, posMarcosEquipos + 11))
        self.imagenFondo.blit(textoEquipoA, (550, posMarcosEquipos + 9))

        self.imagenFondo.blit(imagenEquipoB, (515, posMarcosEquipos + 71))
        self.imagenFondo.blit(sombraTextoEquipoB, (552, posMarcosEquipos + 73))
        self.imagenFondo.blit(textoEquipoB, (550, posMarcosEquipos + 71))

        fichaBlanca = pygame.image.load(xdg_data_path("images/piece-default.png"))
        fichaBlanca = fichaBlanca.convert()

        for i in range(8):
            for j in range (8):
                self.imagenFondo.blit(fichaBlanca, (10 + 60 * i, 10 + 60 * j))

        # Cargando las fichas iniciales..."
        for keyFicha in organizacionInicial.keys():
            ficha = organizacionInicial[keyFicha];
            self.fichas[keyFicha] = Ficha(ficha[0], ficha[1], ficha[2], 
                                       ficha[3], ficha[4], ficha[5])

        # Pintamos los botones
        botonesInterfaz = []
        botonesInterfaz.append(Boton(700, 500, "images/salir", self.callSalir))
        botonesInterfaz.append(Boton(120, 500, "images/flecha_izquierda2", None))
        botonesInterfaz.append(Boton(190, 500, "images/flecha_izquierda1", self.callRetrocederTurno))
        botonesInterfaz.append(Boton(260, 500, "images/flecha_derecha1", self.callAvanzarTurno))
        botonesInterfaz.append(Boton(330, 500, "images/flecha_derecha2", None))

        self.salir = False
        
        # Comienza el game loop"
        while not self.salir:

            # Gestión de eventos
            for eventos in pygame.event.get():
                
                if eventos.type == QUIT:
                    print "** HALT"
                    self.salir = True
                elif eventos.type == MOUSEBUTTONDOWN:
                    for btn in botonesInterfaz:
                        btn.informarClick(eventos.pos)

                elif eventos.type == MOUSEMOTION:
                    for btn in botonesInterfaz:
                        btn.informarHover(eventos.pos)

                elif eventos.type == KEYDOWN and eventos.key == 275:
                    self.callAvanzarTurno()


            # Pintamos el fondo
            self.pantalla.blit(self.imagenFondo, (0, 0))

            # Pintamos las fichas
            for keyFicha in self.fichas:
                self.fichas[keyFicha].pintar(self.pantalla)

            for btn in botonesInterfaz:
                btn.pintar(self.pantalla)

            # Volcamos la pantalla a la gráfica
            pygame.display.flip()

            ##############################
            # GESTIÓN DE LOS FPS

            # Cogemos los ticks actuales
            ticksActual = pygame.time.get_ticks()

            espera = self.intervalo - (ticksActual - self.ticksAnterior)

            if espera > 0:
                # Esperamos el tiempo necesario para mantener los FPS
                pygame.time.delay(int(espera))

            # Actualizamos los ticks anteriores
            self.ticksAnterior = ticksActual

        # Fin del game loop"
        pygame.mixer.music.stop()
        pygame.display.quit()
        return 0

    def callSalir(self, ):
        self.salir = True
        
    def callAvanzarTurno(self, ):
        # Cogemos las fichas del nuevo turno
        nuevasFichas = self.parseador.avanzarTurno()
        self.actualizarFichas(nuevasFichas)

    def callRetrocederTurno(self, ):
        print "Retroceder turno"
        nuevasFichas = self.parseador.retrocederTurno()

        if nuevasFichas != None:
            self.actualizarFichas(nuevasFichas)
    
    def actualizarFichas(self, nuevasFichas):
        if len(nuevasFichas) == 0:
            #self.salir = True
            pass
        else:
            # Recorremos las fichas que teníamos antes
            for f in self.fichas.keys():
            
                # Si alguna ficha ya no está
                if f not in nuevasFichas:
                    # Muere!
                    self.fichas[f].muerete()

                # Si sigue estando
                else:
                    # Actualízate con las cosas que veas nuevas
                    self.fichas[f].actualizate(nuevasFichas[f])

    


def main():
    """
    """

    P = PintarPartida(xdg_data_path('games/game_2011-04-14_20:36:19_Gent0ozaNoelia-vs-NoeliaPabloRecio.txt'),
                      ('Gent0ozaGent0oza', '/home/jose/gsiege/repo/trunk/data/images/piece-orange.png'),
                      ('Gent0ozaGent0oza', '/home/jose/gsiege/repo/trunk/data/images/piece-orange.png'),
                      3,4)
    P.run()
    

if __name__ == '__main__':
    main()