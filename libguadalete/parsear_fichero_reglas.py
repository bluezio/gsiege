#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

if __name__ == '__main__':
    _ = lambda x: x
else:
    from resistencia.nls import gettext as _

def leer_comentario(rutaFichero, wrap = True):
    try:
        fichero = open(rutaFichero, 'r')
    except IOError:
        return "ERROR"

    primeraLinea = fichero.readline().strip()
    # Un comentario válido será aquél cuya línea empiece con ; DOC: Lorem ipsum dillum...
    busqueda = re.match(r"^\s*;\s*DOC\s*:\s*(.*)$", primeraLinea)
    if busqueda:
        cadena = busqueda.group(1)

        if wrap:
            nuevaCadena = ""
            # Vamos a añadir un salto de línea cada X caracteres
            anchoMaximo = 40
            for i in range(0, len(cadena), anchoMaximo):
                nuevaCadena += cadena[i : i + anchoMaximo] + "\n"

            return nuevaCadena[:-1]
        else:
            return cadena

    return _("No comment")

def main():
    for f in range(1,4):
        print leer_comentario("rag%i.clp" % f )
    
if __name__ == '__main__':
    main()

