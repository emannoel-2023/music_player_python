#===================
# Módulo: playlist.py
#===================
import os
import json

class PlaylistManager:
    def __init__(self):
        self.playlists = {}
        self.current_playlist = []
        self.favorites = []
        self.current_index = 0
        self.library = []
        self.load_state()

    def load_directory(self, path):
        valid_ext = ['.mp3', '.wav', '.flac', '.ogg']
        try:
            files = os.listdir(path)
            self.library = sorted(
                [os.path.join(path, f) for f in files 
                if os.path.splitext(f)[1].lower() in valid_ext]
            )
            self.current_playlist = self.library.copy()
            self.current_index = 0
            # Retornar a lista de músicas para verificar se tem mais de uma
            return self.current_playlist
        except Exception as e:
            print(f"Erro ao carregar diretório: {str(e)}")
            return []

    def create_playlist(self, name):
        if name not in self.playlists:
            self.playlists[name] = []
            return True
        return False

    def add_to_playlist(self, playlist_name, song_path):
        if playlist_name in self.playlists and song_path not in self.playlists[playlist_name]:
            self.playlists[playlist_name].append(song_path)
            return True
        return False

    def remove_from_playlist(self, playlist_name, index):
        if playlist_name in self.playlists and 0 <= index < len(self.playlists[playlist_name]):
            del self.playlists[playlist_name][index]
            return True
        return False

    def save_state(self):
        try:
            with open('player_state.json', 'w') as f:
                json.dump({
                    'playlists': self.playlists,
                    'favorites': self.favorites
                }, f)
            return True
        except Exception as e:
            print(f"Erro ao salvar estado: {str(e)}")
            return False

    def load_state(self):
        try:
            with open('player_state.json', 'r') as f:
                data = json.load(f)
                self.playlists = data.get('playlists', {})
                self.favorites = data.get('favorites', [])
            return True
        except FileNotFoundError:
            # Arquivo ainda não existe, não é erro
            return True
        except Exception as e:
            print(f"Erro ao carregar estado: {str(e)}")
            return False

    def search_songs(self, query):
        results = [song for song in self.library if query.lower() in os.path.basename(song).lower()]
        return results
    
    def get_playlist_names(self):
        """Retorna uma lista com os nomes de todas as playlists"""
        return list(self.playlists.keys())
    
    def set_playlist(self, name):
        """Define a playlist atual com base no nome"""
        if name in self.playlists:
            self.current_playlist = self.playlists[name].copy()
            self.current_index = 0
            return True
        return False