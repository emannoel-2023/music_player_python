#===================
# Módulo: main.py
#===================
from audio import AudioPlayer
from playlist import PlaylistManager
from ui import TerminalUI
import os

def main():
    # Verifica se existe um diretório de música padrão
    default_music_dir = os.path.expanduser("~/Music")
    if not os.path.exists(default_music_dir):
        default_music_dir = os.path.expanduser("~/Música")
    
    player = AudioPlayer()
    pm = PlaylistManager()
    
    # Carrega diretório padrão se existir
    if os.path.exists(default_music_dir):
        pm.load_directory(default_music_dir)
        if pm.current_playlist:
            player.load_song(pm.current_playlist[0])
            player.toggle_play_pause()
    
    ui = TerminalUI(player, pm)
    ui.update()

if __name__ == "__main__":
    main()