"""Servicio de audio compartido por los estados del juego."""

from __future__ import annotations

from pathlib import Path

import pygame


class AudioManager:
    """Gestiona musica y efectos sin hacer depender a los estados del mixer."""

    MUSIC_FILES = {
        "menu": "MENUMUSIC.mp3",
        "game": "GAMEMUSIC.mp3",
    }

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path(__file__).resolve().parent
        self.audio_dir = self.project_root / "assets(beta)" / "audio"
        self.music_volume = 1.0
        self.sfx_volume = 1.0
        self.enabled = self._initialize_mixer()
        self._sounds: dict[str, pygame.mixer.Sound] = {}

    def _initialize_mixer(self) -> bool:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.set_volume(self.music_volume)
            return True
        except pygame.error as error:
            print(f"Audio desactivado: {error}")
            return False

    def _music_path(self, track_name: str) -> Path | None:
        filename = self.MUSIC_FILES.get(track_name)
        if filename is None:
            return None
        return self.audio_dir / filename

    def play_music(self, track_name: str, loops: int = -1) -> bool:
        """Reproduce una pista registrada y devuelve si pudo iniciarse."""
        if not self.enabled:
            return False

        track_path = self._music_path(track_name)
        if track_path is None or not track_path.exists():
            return False

        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(str(track_path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(loops)
            return True
        except pygame.error as error:
            print(f"No se pudo reproducir {track_name}: {error}")
            return False

    def stop_music(self) -> None:
        if self.enabled:
            pygame.mixer.music.stop()

    def pause_music(self) -> None:
        if self.enabled:
            pygame.mixer.music.pause()

    def resume_music(self) -> None:
        if self.enabled:
            pygame.mixer.music.unpause()

    def set_music_volume(self, volume: float) -> None:
        self.music_volume = max(0.0, min(1.0, volume))
        if self.enabled:
            pygame.mixer.music.set_volume(self.music_volume)

    def set_sfx_volume(self, volume: float) -> None:
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self._sounds.values():
            sound.set_volume(self.sfx_volume)

    def play_sfx(self, sound_name: str) -> bool:
        """Carga y reproduce un efecto opcional desde ``assets(beta)/audio``."""
        if not self.enabled:
            return False

        sound_path = self.audio_dir / sound_name
        if not sound_path.exists():
            return False

        try:
            sound = self._sounds.get(sound_name)
            if sound is None:
                sound = pygame.mixer.Sound(str(sound_path))
                sound.set_volume(self.sfx_volume)
                self._sounds[sound_name] = sound
            sound.play()
            return True
        except pygame.error as error:
            print(f"No se pudo reproducir el efecto {sound_name}: {error}")
            return False

    def play_menu_music(self) -> bool:
        return self.play_music("menu")

    def play_game_music(self, bg_type: int = 0) -> bool:
        del bg_type
        return self.play_music("game")


_audio_manager: AudioManager | None = None


def get_audio_manager() -> AudioManager:
    """Devuelve la instancia compartida usada por todos los estados."""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager


# Alias de compatibilidad para codigo antiguo que importe SoundPlayer.
SoundPlayer = AudioManager