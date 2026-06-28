"""
connectors/base.py — Clase base para todos los conectores ETL.

Para agregar una fuente nueva:
  1. Crea un archivo en esta carpeta (ej: instagram.py)
  2. Crea una clase que herede de ConectorBase
  3. Implementa el método extraer(tags: list[str]) -> list[dict]
  4. Regístrala en registry.py
"""


class ConectorBase:
    nombre: str = "base"

    def extraer(self, tags: list[str]) -> list[dict]:
        raise NotImplementedError(f"El conector '{self.nombre}' no implementa extraer()")
