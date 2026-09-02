import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "menu"


class GestorConfig:
    @staticmethod
    def resolver_ruta(ruta):
        if not ruta:
            return ""

        ruta_path = Path(str(ruta).replace("\\", "/"))
        if ruta_path.is_absolute():
            return str(ruta_path)

        return str((BASE_DIR / ruta_path).resolve())

    @staticmethod
    def cargar_configuracion():
        ruta_json = CONFIG_DIR / "menu_config.json"
        if not ruta_json.exists():
            print(f"No se encontró el archivo: {ruta_json}")
            return {}
        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando {ruta_json}: {e}")
            return {}