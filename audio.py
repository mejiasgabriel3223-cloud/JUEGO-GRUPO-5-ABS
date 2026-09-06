# audio.py
from pathlib import Path

import pygame as py


class SoundPlayer:
    def __init__(self):
        py.mixer.init()
        self.menu_music = Path("assets(beta)/audio/music.mp3")
        self.game_music = Path("assets(beta)/audio/game_music.mp3")

    def _play_track(self, track_path):
        py.mixer.music.stop()

        if not track_path.exists():
            return

        py.mixer.music.load(track_path.as_posix())
        py.mixer.music.play(-1)

    def play_menu_music(self):
        self._play_track(self.menu_music)

    def play_game_music(self, bg_type=0):
        self._play_track(self.game_music)