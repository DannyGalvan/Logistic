"""Registro publico de snippets didacticos."""

from __future__ import annotations

DEMO_SNIPPETS: dict[str, dict[str, str]] = {
    "calculos_malo": {
        "title": "Calculos (mala calidad)",
        "description": "Demuestra nombres invalidos, imports sin usar y "
                       "excepciones genericas.",
        "path": "apps/quality/snippets/calculos_malo.py",
    },
    "calculos_bueno": {
        "title": "Calculos (calidad corregida)",
        "description": "Version corregida del snippet anterior.",
        "path": "apps/quality/snippets/calculos_bueno.py",
    },
    "demasiados_argumentos": {
        "title": "Demasiados argumentos",
        "description": "Dispara ``too-many-arguments``.",
        "path": "apps/quality/snippets/demasiados_argumentos.py",
    },
    "except_generico": {
        "title": "except Exception",
        "description": "Dispara ``broad-exception-caught``.",
        "path": "apps/quality/snippets/except_generico.py",
    },
    "imports_desordenados": {
        "title": "Imports desordenados",
        "description": "Dispara ``wrong-import-order``.",
        "path": "apps/quality/snippets/imports_desordenados.py",
    },
    "mutable_default": {
        "title": "Parametro mutable por defecto",
        "description": "Dispara ``dangerous-default-value``.",
        "path": "apps/quality/snippets/mutable_default.py",
    },
    "clase_dios": {
        "title": "Clase dios",
        "description": "Demuestra muchas responsabilidades en una sola clase.",
        "path": "apps/quality/snippets/clase_dios.py",
    },
}


__all__ = ["DEMO_SNIPPETS"]
