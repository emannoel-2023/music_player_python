#===================
# Módulo: ui.py (atualizado)
#===================
import curses
import psutil
import time
import os

class TerminalUI:
    def __init__(self, player, playlist_manager):
        self.stdscr = curses.initscr()
        self.player = player
        self.pm = playlist_manager
        self.process = psutil.Process(os.getpid())
        self.last_cpu_measure_time = time.time()
        self.last_cpu_percent = 0
        
        # Configurar curses
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_BLUE, -1)
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        self.stdscr.keypad(1)
        
        # Atualiza a CPU pela primeira vez
        self.update_cpu_usage()

    def update_cpu_usage(self):
        current_time = time.time()
        if current_time - self.last_cpu_measure_time >= 1.0:  # Intervalo de 1 segundo
            self.last_cpu_percent = self.process.cpu_percent()
            self.last_cpu_measure_time = current_time
        return self.last_cpu_percent

    def draw_progress(self, y):
        progress = self.player.get_progress()
        total = self.player.song_length
        song_name = self.player.get_current_song()[:40]
        bar_width = 40
        filled = int(bar_width * (progress / total)) if total > 0 else 0
        # Movendo a exibição do nome da música para baixo
        self.stdscr.addstr(24, 0, f"▶ Tocando: {song_name}", curses.color_pair(3))
        self.stdscr.addstr(y+1, 0, f"[{'█'*filled}{' '*(bar_width-filled)}] {progress:.1f}/{total:.1f}s")

    def draw_spectrum(self, y):
        spectrum = self.player.get_spectrum()
        spectrum_width = 40  # Largura total do espectro
        
        # Desenha o eixo horizontal do espectro
        for i in range(min(10, len(spectrum))):
            # Calcula a altura da barra normalizada para o espectro
            height = min(int(spectrum[i] * 2), 15)  # Limita a altura máxima a 15
            
            # Escolhe a cor da barra baseada na sua altura
            if height <= 3:
                color = curses.color_pair(1)  # Verde para baixas frequências
            elif height <= 7:
                color = curses.color_pair(3)  # Amarelo para médias frequências
            elif height <= 10:
                color = curses.color_pair(5)  # Magenta para altas-médias frequências
            else:
                color = curses.color_pair(4)  # Vermelho para altas frequências
            
            # Desenha a barra horizontal
            bar = '█' * height
            self.stdscr.addstr(y + i, 0, bar, color)

    def draw_volume_bar(self, y, x):
        """Desenha uma barra de volume horizontal"""
        vol_percent = int(self.player.volume * 100)
        bar_width = 20
        filled = int(bar_width * self.player.volume)
        
        self.stdscr.addstr(y, x, f"Volume: [{('|' * filled) + (' ' * (bar_width - filled))}] {vol_percent}%")
        self.stdscr.addstr(y, x + 35, "[+/-] Ajustar", curses.color_pair(2))

    def draw_system_stats(self, y):
        # Usa o psutil mais corretamente para obter métricas apenas deste processo
        mem = self.process.memory_percent()
        cpu = self.update_cpu_usage()
        
        self.stdscr.addstr(y, 0, f"RAM: {mem:.1f}%", curses.color_pair(1))
        self.stdscr.addstr(y, 20, f"CPU: {cpu:.1f}%", curses.color_pair(1))

    def draw_playlist(self, start_y, start_x):
        max_items = 8
        for idx, song in enumerate(self.pm.current_playlist[:max_items]):
            song_name = os.path.basename(song)[:25]
            status = "▶" if idx == self.pm.current_index else " "
            self.stdscr.addstr(8 + idx, 45, f"{status} {idx+1}. {song_name}")

    def draw_commands(self):
        commands = [
            ("[1] Abrir diretório", "[2] Play/Pause"),
            ("[3] Parar", "[4] Próxima"),
            ("[5] Anterior", "[+/-] Volume"),
            ("[7] Criar playlist", "[8] Add"),
            ("[P] Playlists", "[9] Remover"),
            ("[F] Pesquisar", "[B] Biblioteca"),
            ("[Q] Sair", "[0] Favoritos")
        ]
        
        for row, (left, right) in enumerate(commands):
            self.stdscr.addstr(16 + row, 0, left.ljust(20), curses.color_pair(2))
            self.stdscr.addstr(16 + row, 25, right, curses.color_pair(2))

    def show_input(self, prompt, y=20):
        curses.endwin()
        import tkinter as tk
        from tkinter import simpledialog
        
        root = tk.Tk()
        root.withdraw()
        input_str = simpledialog.askstring("Input", prompt, parent=root)
        root.destroy()
        
        self.stdscr = curses.initscr()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        
        return input_str if input_str else ""

    def handle_input(self):
        try:
            key = self.stdscr.getch()
            
            if key == ord('0'):
                if self.player.current_song:
                    self.pm.favorites.append(self.player.current_song)
            elif key == ord('q') or key == ord('Q'):
                self.pm.save_state()
                return False
            elif key == ord('1'):
                try:
                    path = self.show_input("Caminho do diretório:")
                    if path and os.path.isdir(path):
                        self.pm.load_directory(path)
                        if self.pm.current_playlist:
                            self.player.load_song(self.pm.current_playlist[0])
                            # Iniciar reprodução automaticamente
                            self.player.toggle_play_pause()
                except Exception as e:
                    self.show_error(f"Erro ao abrir diretório: {str(e)}")
            elif key == ord('2'):
                self.player.toggle_play_pause()
            elif key == ord('3'):
                self.player.stop()
            elif key == ord('4'):
                if self.pm.current_playlist:
                    self.pm.current_index = (self.pm.current_index + 1) % len(self.pm.current_playlist)
                    self.player.load_song(self.pm.current_playlist[self.pm.current_index])
                    self.player.toggle_play_pause()
            elif key == ord('5'):
                if self.pm.current_playlist:
                    self.pm.current_index = (self.pm.current_index - 1) % len(self.pm.current_playlist)
                    self.player.load_song(self.pm.current_playlist[self.pm.current_index])
                    self.player.toggle_play_pause()
            # Controle de volume dinâmico com teclas + e -
            elif key == ord('+') or key == ord('='):  # = está no mesmo botão que + em muitos teclados
                new_vol = min(1.0, self.player.volume + 0.05)
                self.player.set_volume(new_vol)
            elif key == ord('-'):
                new_vol = max(0.0, self.player.volume - 0.05)
                self.player.set_volume(new_vol)
            elif key == ord('7'):
                name = self.show_input("Nome da playlist:")
                if name:
                    self.pm.create_playlist(name)
            elif key == ord('8'):
                if not self.player.current_song:
                    return True
                    
                playlist_names = list(self.pm.playlists.keys())
                if not playlist_names:
                    self.show_error("Nenhuma playlist disponível. Crie uma primeiro.")
                    return True
                    
                import tkinter as tk
                from tkinter import simpledialog
                
                root = tk.Tk()
                root.withdraw()
                
                dialog = simpledialog.askstring(
                    "Selecionar Playlist", 
                    f"Playlists disponíveis: {', '.join(playlist_names)}\nDigite o nome da playlist:",
                    parent=root
                )
                root.destroy()
                
                if dialog and dialog in self.pm.playlists:
                    self.pm.add_to_playlist(dialog, self.player.current_song)
                
                self.stdscr = curses.initscr()
                curses.start_color()
                curses.use_default_colors()
                curses.init_pair(1, curses.COLOR_GREEN, -1)
                curses.init_pair(2, curses.COLOR_CYAN, -1)
                curses.init_pair(3, curses.COLOR_YELLOW, -1)
                curses.init_pair(4, curses.COLOR_RED, -1)
                curses.init_pair(5, curses.COLOR_MAGENTA, -1)
                curses.init_pair(6, curses.COLOR_BLUE, -1)
                curses.curs_set(0)
                self.stdscr.nodelay(1)
                self.stdscr.keypad(1)
            elif key == ord('9'):
                playlist_names = list(self.pm.playlists.keys())
                if not playlist_names:
                    self.show_error("Nenhuma playlist disponível.")
                    return True
                
                playlist_name = self.show_input(f"Playlists: {', '.join(playlist_names)}\nDigite o nome:")
                if playlist_name and playlist_name in self.pm.playlists:
                    del self.pm.playlists[playlist_name]
            elif key == ord('f') or key == ord('F'):
                query = self.show_input("Pesquisar:")
                if query:
                    results = self.pm.search_songs(query)
                    if results:
                        self.pm.current_playlist = results
                        self.pm.current_index = 0
                        self.player.load_song(self.pm.current_playlist[0])
                        self.player.toggle_play_pause()
            elif key == ord('b') or key == ord('B'):
                if self.pm.library:
                    self.pm.current_playlist = self.pm.library.copy()
                    self.pm.current_index = 0
                    self.player.load_song(self.pm.current_playlist[0])
            elif key == ord('p') or key == ord('P'):
                # Melhorando o acesso às playlists
                playlist_names = list(self.pm.playlists.keys())
                if not playlist_names:
                    self.show_error("Nenhuma playlist criada!")
                    return True
                
                # Lista playlists numeradas
                pl_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(playlist_names)])
                selected = self.show_input(f"Playlists Disponíveis:\n{pl_list}\n\nDigite o número da playlist:")
                
                try:
                    if selected and selected.isdigit():
                        idx = int(selected) - 1
                        if 0 <= idx < len(playlist_names):
                            pl_name = playlist_names[idx]
                            self.pm.current_playlist = self.pm.playlists[pl_name]
                            if self.pm.current_playlist:
                                self.pm.current_index = 0
                                self.player.load_song(self.pm.current_playlist[0])
                                self.player.toggle_play_pause()
                except Exception as e:
                    self.show_error(f"Erro ao carregar playlist: {str(e)}")
                    
        except Exception as e:
            self.show_error(f"Erro: {str(e)}")
        
        return True

    def update(self):
        try:
            while True:
                try:
                    self.stdscr.erase()
                    self.stdscr.addstr(0, 0, r"""

     ____  __    ___   __   ____   __  ____    ____  ____    _  _  _  _  ____   ___   __  
    (_  _)/  \  / __) / _\ (    \ /  \(  _ \  (    \(  __)  ( \/ )/ )( \/ ___) / __) / _\ 
      )( (  O )( (__ /    \ ) D ((  O ))   /   ) D ( ) _)   / \/ \) \/ (\___ \( (_ \/    \
     (__) \__/  \___)\_/\_/(____/ \__/(__\_)  (____/(____)  \_)(_/\____/(____/ \___/\_/\_/

                    """.strip(), curses.color_pair(3))
                    self.draw_progress(5)
                    self.draw_spectrum(7)
                    self.draw_playlist(7, 45)
                    self.draw_commands()
                    # Adiciona a barra de volume visual
                    self.draw_volume_bar(14, 0)
                    self.draw_system_stats(25)  # Mantendo as estatísticas do sistema no final da tela
                    
                    # Verificar se a música acabou e iniciar a próxima automaticamente
                    if self.player.check_song_end() and self.pm.current_playlist and len(self.pm.current_playlist) > 1:
                        self.pm.current_index = (self.pm.current_index + 1) % len(self.pm.current_playlist)
                        self.player.load_song(self.pm.current_playlist[self.pm.current_index])
                        self.player.toggle_play_pause()
                    
                    if not self.handle_input():
                        break
                    
                    self.stdscr.refresh()
                    time.sleep(0.1)
                except Exception as e:
                    self.show_error(f"Erro: {str(e)}")
        finally:
            curses.endwin()
            
    def show_error(self, message):
        curses.endwin()
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro", message)
        root.destroy()
        
        self.stdscr = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_BLUE, -1)
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        self.stdscr.keypad(1)