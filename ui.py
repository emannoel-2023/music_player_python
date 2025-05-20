#===================
# Módulo: ui.py (atualizado com navegação de playlist corrigida)
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
        
        # Variáveis de estado para navegação da playlist
        self.playlist_page = 0
        self.playlist_items_per_page = 8
        self.selecting_song = False
        self.selected_index = 0
        self.last_navigation_key_time = 0  # Para evitar navegação muito rápida
        self.navigation_cooldown = 0.15  # Cooldown em segundos entre navegações
        
        # Configurar curses
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_BLUE, -1)
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Destacar item selecionado
        curses.curs_set(0)
        self.stdscr.nodelay(1)  # Sempre não-bloqueante
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
        
        # Converter segundos para formato minutos:segundos
        progress_min = int(progress // 60)
        progress_sec = int(progress % 60)
        total_min = int(total // 60)
        total_sec = int(total % 60)
        
        # Formato de tempo em minutos:segundos
        time_format = f"{progress_min}:{progress_sec:02d}/{total_min}:{total_sec:02d}"
        
        bar_width = 40
        filled = int(bar_width * (progress / total)) if total > 0 else 0
        
        # Mostrar o nome da música
        self.stdscr.addstr(24, 0, f"▶ Tocando: {song_name}", curses.color_pair(3))
        # Mostrar a duração abaixo do nome da música
        self.stdscr.addstr(25, 0, f"[{'█'*filled}{' '*(bar_width-filled)}] {time_format}")

    def draw_spectrum(self, y):
        """Desenha o espectro de áudio horizontalmente de baixo para cima"""
        spectrum = self.player.get_spectrum()
        max_height = 5  # Altura máxima das barras do espectro
        
        # Desenha a linha base onde ficará o espectro
        self.stdscr.addstr(y, 0, "Espectro: ", curses.color_pair(2))
        
        # Para cada valor no espectro, desenha uma barra vertical
        for i in range(min(10, len(spectrum))):
            # Normaliza a altura da barra para no máximo max_height
            height = min(int(spectrum[i]), max_height)
            
            # Coordenadas base para desenhar a partir do chão
            base_y = y + max_height - 1  # Posição y do "chão"
            
            # Desenha a barra de baixo para cima (invertendo a ordem)
            for h in range(height):
                # Determina a posição y atual para o bloco
                current_y = base_y - h
                
                # Escolhe a cor baseada na altura relativa
                if h == 0:  # Blocos mais baixos (piso)
                    color = curses.color_pair(1)  # Verde para baixas frequências
                elif h <= 2:
                    color = curses.color_pair(3)  # Amarelo para médias frequências
                elif h <= 3:
                    color = curses.color_pair(5)  # Magenta para altas-médias frequências
                else:
                    color = curses.color_pair(4)  # Vermelho para altas frequências
                
                # Desenha o bloco na posição atual
                self.stdscr.addstr(current_y, 10+i*2, "█", color)

    def draw_volume_bar(self, y, x):
        """Desenha uma barra de volume horizontal com indicador dinâmico"""
        vol_percent = int(self.player.volume * 100)
        bar_width = 20
        filled = int(bar_width * self.player.volume)
        
        # Desenha a barra com um marcador diferente para o nível atual
        bar = ""
        for i in range(bar_width):
            if i < filled - 1:
                bar += "▰"  # Barra preenchida antes do indicador
            elif i == filled - 1:
                bar += "▲"  # Indicador da posição atual
            else:
                bar += "▱"  # Barra vazia após o indicador
        
        self.stdscr.addstr(y, x, f"Volume: [{bar}] {vol_percent}%")
        self.stdscr.addstr(y, x + 35, "[+/-] Ajustar", curses.color_pair(2))

    def draw_system_stats(self, y):
        # Usa o psutil mais corretamente para obter métricas apenas deste processo
        mem = self.process.memory_percent()
        cpu = self.update_cpu_usage()
        
        self.stdscr.addstr(y, 0, f"RAM: {mem:.1f}%", curses.color_pair(1))
        self.stdscr.addstr(y, 20, f"CPU: {cpu:.1f}%", curses.color_pair(1))

    def draw_playlist(self, start_y, start_x):
        """Desenha a playlist atual com paginação e indica o item selecionado"""
        # Calcular o número total de páginas
        total_songs = len(self.pm.current_playlist)
        total_pages = (total_songs + self.playlist_items_per_page - 1) // self.playlist_items_per_page
        
        # Ajustar a página atual se necessário
        if total_pages > 0:
            self.playlist_page = max(0, min(self.playlist_page, total_pages - 1))
        else:
            self.playlist_page = 0
        
        # Calcular o intervalo de músicas a mostrar
        start_idx = self.playlist_page * self.playlist_items_per_page
        end_idx = min(start_idx + self.playlist_items_per_page, total_songs)
        
        # Título da lista com indicação de paginação
        page_info = f" (Página {self.playlist_page + 1}/{total_pages})" if total_pages > 0 else ""
        self.stdscr.addstr(start_y, start_x, f"Playlist Atual{page_info}:", curses.color_pair(3))
        self.stdscr.addstr(start_y, start_x + 40, f"Total: {total_songs} músicas", curses.color_pair(1))
        
        # Desenhar as músicas da página atual
        for i in range(start_idx, end_idx):
            song_name = os.path.basename(self.pm.current_playlist[i])[:30]
            status = "▶" if i == self.pm.current_index else " "
            row = start_y + 1 + (i - start_idx)
            
            # Usar cores diferentes para destacar o item selecionado no modo de seleção
            if self.selecting_song and i == self.selected_index:
                self.stdscr.addstr(row, start_x, f"{status} {i+1}. {song_name}".ljust(40), curses.color_pair(7))
            else:
                self.stdscr.addstr(row, start_x, f"{status} {i+1}. {song_name}")
        
        # Instruções de navegação da playlist
        if total_pages > 1:
            self.stdscr.addstr(start_y + self.playlist_items_per_page + 1, start_x, 
                         "Navegação: [↑/↓] Mover cursor [PgUp/PgDn] Mudar página [Enter] Selecionar", 
                         curses.color_pair(2))
        
        # Barra de status para o modo de seleção
        if self.selecting_song:
            self.stdscr.addstr(start_y + self.playlist_items_per_page + 2, start_x,
                         "MODO DE SELEÇÃO: Use setas para navegar e Enter para tocar", 
                         curses.color_pair(5))

    def draw_commands(self):
        commands = [
            ("[1] Abrir diretório", "[2] Play/Pause"),
            ("[3] Parar", "[4] Próxima"),
            ("[5] Anterior", "[+/-] Volume"),
            ("[7] Criar playlist", "[8] Add"),
            ("[P] Playlists", "[9] Remover"),
            ("[F] Pesquisar", "[B] Biblioteca"),
            ("[N] Navegar playlist", "[S] Saltar p/ música"),
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
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Destacar item selecionado
        curses.curs_set(0)
        self.stdscr.nodelay(1)  # Sempre não-bloqueante
        self.stdscr.keypad(1)
        
        return input_str if input_str else ""

    def play_selected_song(self):
        """Reproduz a música selecionada"""
        if not self.pm.current_playlist or self.selected_index >= len(self.pm.current_playlist):
            return
            
        self.pm.current_index = self.selected_index
        self.player.load_song(self.pm.current_playlist[self.selected_index])
        self.player.toggle_play_pause()
        # Desativa o modo de seleção após tocar
        self.selecting_song = False

    def handle_navigation_mode(self, key):
        """Gerencia as teclas quando está no modo de navegação da playlist"""
        current_time = time.time()
        
        # Aplica cooldown para evitar navegação muito rápida
        if current_time - self.last_navigation_key_time < self.navigation_cooldown:
            return
            
        total_songs = len(self.pm.current_playlist)
        if total_songs == 0:
            self.selecting_song = False
            return
            
        navigation_occurred = False
            
        if key == curses.KEY_UP:
            # Move a seleção para cima
            self.selected_index = (self.selected_index - 1) % total_songs
            # Ajusta a página se necessário
            page_of_selected = self.selected_index // self.playlist_items_per_page
            if page_of_selected != self.playlist_page:
                self.playlist_page = page_of_selected
            navigation_occurred = True
                
        elif key == curses.KEY_DOWN:
            # Move a seleção para baixo
            self.selected_index = (self.selected_index + 1) % total_songs
            # Ajusta a página se necessário
            page_of_selected = self.selected_index // self.playlist_items_per_page
            if page_of_selected != self.playlist_page:
                self.playlist_page = page_of_selected
            navigation_occurred = True
                
        elif key == curses.KEY_NPAGE:  # Page Down
            # Próxima página
            total_pages = (total_songs + self.playlist_items_per_page - 1) // self.playlist_items_per_page
            if total_pages > 0:
                self.playlist_page = (self.playlist_page + 1) % total_pages
                # Ajusta o índice de seleção para a nova página
                self.selected_index = self.playlist_page * self.playlist_items_per_page
                if self.selected_index >= total_songs:
                    self.selected_index = total_songs - 1
            navigation_occurred = True
                    
        elif key == curses.KEY_PPAGE:  # Page Up
            # Página anterior
            total_pages = (total_songs + self.playlist_items_per_page - 1) // self.playlist_items_per_page
            if total_pages > 0:
                self.playlist_page = (self.playlist_page - 1) % total_pages
                # Ajusta o índice de seleção para a nova página
                self.selected_index = self.playlist_page * self.playlist_items_per_page
            navigation_occurred = True
                
        elif key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter
            # Reproduz a música selecionada
            self.play_selected_song()
            navigation_occurred = True
            
        elif key == 27:  # ESC
            # Sai do modo de seleção
            self.selecting_song = False
            navigation_occurred = True
            
        # Atualiza o tempo do último comando de navegação apenas se houve navegação
        if navigation_occurred:
            self.last_navigation_key_time = current_time

    def jump_to_song(self):
        """Pede ao usuário um número e salta para essa música na playlist"""
        if not self.pm.current_playlist:
            self.show_error("A playlist está vazia!")
            return
            
        try:
            song_number = self.show_input(f"Número da música (1-{len(self.pm.current_playlist)}):")
            if song_number and song_number.isdigit():
                idx = int(song_number) - 1  # Converte para índice base-0
                if 0 <= idx < len(self.pm.current_playlist):
                    # Define o índice atual e reproduz a música
                    self.pm.current_index = idx
                    self.player.load_song(self.pm.current_playlist[idx])
                    self.player.toggle_play_pause()
                    
                    # Calcula a página correta
                    self.playlist_page = idx // self.playlist_items_per_page
                else:
                    self.show_error("Número de música inválido!")
        except Exception as e:
            self.show_error(f"Erro ao saltar para música: {str(e)}")

    def handle_input(self):
        try:
            key = self.stdscr.getch()
            
            # Se estiver no modo de navegação, trata as teclas de navegação
            if self.selecting_song and key != -1:
                self.handle_navigation_mode(key)
                # Não retorna aqui! Deixa o código continuar para processar outras teclas
                # return True  # REMOVIDO - esta linha causava o problema
                
            if key == ord('q') or key == ord('Q'):
                self.pm.save_state()
                return False
            elif key == ord('n') or key == ord('N'):
                # Ativa/desativa o modo de navegação da playlist
                if self.pm.current_playlist:
                    self.selecting_song = not self.selecting_song
                    if self.selecting_song:
                        # Inicia seleção na música atual
                        self.selected_index = self.pm.current_index
                        # Ajusta a página para mostrar a música selecionada
                        self.playlist_page = self.selected_index // self.playlist_items_per_page
                        # NÃO MUDA O MODO NODELAY - mantém sempre não-bloqueante
                    # Não precisa mais ajustar nodelay pois sempre será 1
                else:
                    self.show_error("Não há músicas na playlist!")
            elif key == ord('s') or key == ord('S'):
                # Salta diretamente para uma música pelo número
                self.jump_to_song()
            elif key == ord('0'):
                if self.player.current_song:
                    self.pm.favorites.append(self.player.current_song)
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
                curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Destacar item selecionado
                curses.curs_set(0)
                self.stdscr.nodelay(1)  # Sempre não-bloqueante
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
                    self.draw_commands()
                    # Desenha a playlist ao lado dos comandos
                    self.draw_playlist(5, 55)  
                    # Adiciona a barra de volume visual
                    self.draw_volume_bar(14, 0)
                    self.draw_system_stats(26)  # Ajustado para ficar abaixo do tempo/duração
                    
                    # Verificar se a música acabou e iniciar a próxima automaticamente
                    if self.player.check_song_end() and self.pm.current_playlist and len(self.pm.current_playlist) > 1:
                        self.pm.current_index = (self.pm.current_index + 1) % len(self.pm.current_playlist)
                        self.player.load_song(self.pm.current_playlist[self.pm.current_index])
                        self.player.toggle_play_pause()
                    
                    if not self.handle_input():
                        break
                    
                    self.stdscr.refresh()
                    time.sleep(0.1)  # Mantém o loop ativo com intervalos pequenos
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
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Destacar item selecionado
        curses.curs_set(0)
        self.stdscr.nodelay(1)  # Sempre não-bloqueante
        self.stdscr.keypad(1)