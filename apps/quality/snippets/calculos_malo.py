"""Snippet de ejemplo con problemas de calidad (voluntariamente malo).

Demuestra varios mensajes de Pylint: nombres PascalCase, import sin
usar, variables sin usar, ``except`` generico, mutable default, etc.
No esta cubierto por tests ni por el linter del proyecto.
"""


import json  # unused-import


def Calcular(a, b):
    Resultado = a + b  # invalid-name, unused-variable
    Datos = {"valor": Resultado}
    return Datos


def divide_numbers(valor, divisor, lista=[]):  # dangerous-default-value
    try:
        item = lista.pop()
        return valor / divisor + item
    except Exception:  # broad-exception-caught
        return 0


def procesa(items):
    """Demasiadas sentencias en una sola funcion."""
    total = 0
    contador = 0
    media = 0
    maximo = 0
    minimo = 0
    suma = 0
    for i in items:
        suma = suma + i
        contador = contador + 1
    if contador > 0:
        media = suma / contador
    for i in items:
        if i > maximo:
            maximo = i
        if i < minimo or minimo == 0:
            minimo = i
    return {
        "total": total,
        "suma": suma,
        "media": media,
        "maximo": maximo,
        "minimo": minimo,
        "json": json.dumps(items),  # noqa
    }
