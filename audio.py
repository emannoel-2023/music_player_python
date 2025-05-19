#===================
# Módulo: audio.py (atualizado)
#===================
import pygame
import numpy as np
from pygame import mixer
import os
import time
import random
import math

class AudioPlayer:
    def __init__(self):
        mixer.init(frequency=44100)
        self.current_song = None
        self.paused = False
        self.volume = 0.5
        self.spectrum_data = []
        self.start_time = 0
        self.song_length = 0
        self.last_spectrum_update = 0
        self.spectrum_delay = 0.05  # Atualiza o espectro a cada 50ms
        
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
        current_time = time.time()
        
        # Apenas atualiza o espectro após um pequeno intervalo para economizar CPU
        if current_time - self.last_spectrum_update < self.spectrum_delay:
            if hasattr(self, 'last_spectrum'):
                return self.last_spectrum
            else:
                self.last_spectrum = np.zeros(10)
                return self.last_spectrum
                
        self.last_spectrum_update = current_time
            
        if not mixer.get_init() or not mixer.music.get_busy() and not self.paused:
            self.last_spectrum = np.zeros(10)
            return self.last_spectrum
            
        try:
            if self.current_song:
                progress = self.get_progress()
                
                # Cria um espectro mais dinâmico e interessante
                # Usamos funções seno e cosseno com deslocamentos para gerar um espectro mais realista
                base = np.linspace(0, 10, 10)
                
                # Adiciona complexidade e dinamismo ao espectro
                data = np.zeros(10)
                for i in range(10):
                    # Frequências simuladas com base no tempo
                    freq1 = 0.5 + 0.5 * math.sin(progress * 0.2 + i * 0.3)
                    freq2 = 0.7 + 0.3 * math.cos(progress * 0.1 + i * 0.5)
                    
                    # Amplitudes simuladas com variação no tempo
                    amp1 = 0.6 + 0.4 * math.sin(progress * 0.3 + i * 0.2)
                    amp2 = 0.5 + 0.5 * math.cos(progress * 0.4 + i * 0.1)
                    
                    # Compõe ambas frequências com suas amplitudes
                    data[i] = abs(amp1 * math.sin(freq1 * progress + i) + 
                                 amp2 * math.cos(freq2 * progress + i * 2))
                
                # Normaliza para valores entre 0 e 8 (a altura preferida para visualização)
                data = 8 * data / np.max(data) if np.max(data) > 0 else data
                
                self.last_spectrum = data
                return data
        except Exception as e:
            print(f"Erro ao obter espectro: {e}")
        
        self.last_spectrum = np.zeros(10)
        return self.last_spectrum

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