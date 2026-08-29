import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent  

class GestorConfig:
    @staticmethod
    def cargar_configuracion():
        ruta_json = BASE_DIR / "menu_config.json"
        if not ruta_json.exists():
            print(" No se encontró el archivo menu_config.json")
            return {}
        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando menu_config.json: {e}")
            return {}