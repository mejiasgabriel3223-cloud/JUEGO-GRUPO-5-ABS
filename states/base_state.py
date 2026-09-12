# states/base_state.py
class BaseState:
    def handle_events(self, events):
        """Procesa eventos de Pygame."""
        pass

    def update(self, dt):
        """Actualiza la lógica. Retorna el nombre del nuevo estado si debe cambiar."""
        return None

    def draw(self, screen):
        """Renderiza en pantalla."""
        pass