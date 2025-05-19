#===================
# Módulo: audio.py
#===================
import pygame
import numpy as np
from pygame import mixer
import os
import time
import random

class AudioPlayer:
    def __init__(self):
        mixer.init(frequency=44100)
        self.current_song = None
        self.paused = False
        self.volume = 0.5
        self.spectrum_data = []
        self.start_time = 0
        self.song_length = 0
        
        mixer.music.set_volume(self.volume)
        # Adicionar evento para detectar o final da música para autoplay
        pygame.init()
        self.SONG_END = pygame.USEREVENT + 1
        mixer.music.set_endevent(self.SONG_END)

    def load_song(self, path):
        if os.path.exists(path):
            try:
                mixer.music.load(path)
                self.current_song = path
                self.start_time = time.time()
                self.paused = False
                
                sound = mixer.Sound(path)
                self.song_length = sound.get_length()
                return True
            except Exception as e:
                print(f"Erro ao carregar música: {e}")
                return False
        return False

    def toggle_play_pause(self):
        if not mixer.music.get_busy() and not self.paused:
            mixer.music.play()
            self.start_time = time.time()
        elif self.paused:
            mixer.music.unpause()
            self.paused = False
        else:
            mixer.music.pause()
            self.paused = True

    def stop(self):
        mixer.music.stop()
        self.paused = False
    
    def set_volume(self, vol):
        self.volume = max(0.0, min(1.0, float(vol)))
        mixer.music.set_volume(self.volume)
        return self.volume

    def get_spectrum(self):
        if not mixer.get_init() or not mixer.music.get_busy():
            return np.zeros(15)
            
        try:
            if self.current_song:
                progress = self.get_progress()
                # Espectro mais largo - multiplicar por 5 para aumentar a largura do espectro
                data = np.sin(np.linspace(0, 5, 10) + progress)
                return np.abs(data) * 5  # Aumentado de 2 para 5
        except Exception as e:
            print(f"Erro ao obter espectro: {e}")
        
        return np.zeros(15)

    def get_progress(self):
        if not self.current_song:
            return 0
            
        if self.paused:
            return mixer.music.get_pos() / 1000
            
        if mixer.music.get_busy():
            elapsed = time.time() - self.start_time
            return min(elapsed, self.song_length)
            
        return 0

    def get_current_song(self):
        if not self.current_song:
            return ""
        return os.path.basename(self.current_song)
    
    def check_song_end(self):
        """Verifica se ocorreu o evento de término da música"""
        for event in pygame.event.get():
            if event.type == self.SONG_END:
                return True
        return False