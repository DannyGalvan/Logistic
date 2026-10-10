"""Catalogo de mensajes Pylint en espanol.

Archivo cargado por ``MessageCatalog``. Cada entrada: codename,
simbolo, categoria, titulo, explicacion, ejemplo malo y bueno.
"""

from __future__ import annotations

CATALOG: list[dict[str, str]] = [
    {
        "code": "C0103",
        "symbol": "invalid-name",
        "category": "C",
        "title": "Nombre invalido",
        "explanation": "El nombre no cumple la convencion de naming (PEP 8).",
        "bad_example": "def MiFuncion(): pass",
        "good_example": "def mi_funcion(): pass",
    },
    {
        "code": "C0114",
        "symbol": "missing-module-docstring",
        "category": "C",
        "title": "Modulo sin docstring",
        "explanation": "Todos los modulos publicos deben tener un docstring.",
        "bad_example": "def add(a, b): return a + b",
        "good_example": "\"\"\"Operaciones basicas.\"\"\"\n\n\ndef add(a, b): return a + b",
    },
    {
        "code": "C0115",
        "symbol": "missing-class-docstring",
        "category": "C",
        "title": "Clase sin docstring",
        "explanation": "Las clases publicas deben documentar su proposito.",
        "bad_example": "class Calculator: pass",
        "good_example": "class Calculator:\n    \"\"\"Calculadora basica.\"\"\"\n    pass",
    },
    {
        "code": "C0116",
        "symbol": "missing-function-docstring",
        "category": "C",
        "title": "Funcion sin docstring",
        "explanation": "Documente el contrato de cada funcion publica.",
        "bad_example": "def greet(name): return f\"Hi {name}\"",
        "good_example": (
            "def greet(name):\n"
            "    \"\"\"Saluda al usuario.\"\"\"\n"
            "    return f\"Hi {name}\""
        ),
    },
    {
        "code": "C0301",
        "symbol": "line-too-long",
        "category": "C",
        "title": "Linea demasiado larga",
        "explanation": "Limite recomendado 100; sobre 96 hace superior.",
        "bad_example": (
            "x = \"string that exceeds the recommended line length limit set by the linter\""
        ),
        "good_example": (
            "x = (\n"
            "    \"string that exceeds the recommended line length limit\"\n"
            ")\n"
        ),
    },
    {
        "code": "R0901",
        "symbol": "too-many-ancestors",
        "category": "R",
        "title": "Demasiadas clases base",
        "explanation": "Herencia profunda reduce legibilidad.",
        "bad_example": (
            "class A: pass\n"
            "class B(A): pass\n"
            "class C(B): pass\n"
            "class D(C): pass\n"
            "class E(D): pass"
        ),
        "good_example": (
            "class A: pass\n"
            "class MixinA: pass\n"
            "class Service(A, MixinA): pass"
        ),
    },
    {
        "code": "R0903",
        "symbol": "too-few-public-methods",
        "category": "R",
        "title": "Muy pocos metodos publicos",
        "explanation": "Una clase con un solo metodo suele ser una funcion.",
        "bad_example": "class StringHelper:\n    def upper(self, s): return s.upper()",
        "good_example": "def upper(s): return s.upper()",
    },
    {
        "code": "R0913",
        "symbol": "too-many-arguments",
        "category": "R",
        "title": "Demasiados argumentos",
        "explanation": "Mas de 6 argumentos dificulta las pruebas.",
        "bad_example": "def f(a, b, c, d, e, f, g, h): return a + b + c + d + e + f + g + h",
        "good_example": "def f(*, a, b, c, d, e, f): return a + b + c + d + e + f",
    },
    {
        "code": "R0915",
        "symbol": "too-many-statements",
        "category": "R",
        "title": "Demasiadas sentencias",
        "explanation": "Funciones largas; extraer sub-funciones.",
        "bad_example": "def process(): [do_something() for _ in range(60)]",
        "good_example": "def process():\n    for step in steps:\n        do_step(step)",
    },
    {
        "code": "W0102",
        "symbol": "dangerous-default-value",
        "category": "W",
        "title": "Valor por defecto mutable",
        "explanation": "Los parametros por defecto se evaluan una vez.",
        "bad_example": (
            "def add(item, bag=[]): bag.append(item); return bag"
        ),
        "good_example": (
            "def add(item, bag=None):\n"
            "    if bag is None: bag = []\n"
            "    bag.append(item); return bag"
        ),
    },
    {
        "code": "W0718",
        "symbol": "broad-exception-caught",
        "category": "W",
        "title": "Excepcion demasiado amplia",
        "explanation": "Capturar ``Exception`` oculta bugs reales.",
        "bad_example": "try: x = 1/0\nexcept Exception: pass",
        "good_example": "try: x = 1/0\nexcept ZeroDivisionError: pass",
    },
    {
        "code": "W1203",
        "symbol": "logging-fstring-interpolation",
        "category": "W",
        "title": "Interpolacion con f-string en logging",
        "explanation": "Use ``%s`` para evitar evaluar la cadena si el nivel esta deshabilitado.",
        "bad_example": "log.info(f\"valor={x}\")",
        "good_example": "log.info(\"valor=%s\", x)",
    },
    {
        "code": "E1101",
        "symbol": "no-member",
        "category": "E",
        "title": "Miembro inexistente",
        "explanation": "Se accede a un atributo que no existe.",
        "bad_example": "result = math.PI",
        "good_example": "result = math.pi",
    },
    {
        "code": "E0401",
        "symbol": "import-error",
        "category": "E",
        "title": "Error de importacion",
        "explanation": "No se pudo importar un modulo requerido.",
        "bad_example": "from django import non_existent",
        "good_example": "from django import forms",
    },
    {
        "code": "F0001",
        "symbol": "fatal",
        "category": "F",
        "title": "Error fatal",
        "explanation": "Pylint no pudo analizar el modulo.",
        "bad_example": "def f(: pass",
        "good_example": "def f(): pass",
    },
]


__all__ = ["CATALOG"]
