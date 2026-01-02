#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Desktop para Avaliação Subjetiva de Vídeos
=====================================================

Esta aplicação permite realizar testes de avaliação subjetiva de qualidade de vídeo,
comparando vídeos de teste com um vídeo de referência.

Requisitos:
-----------
pip install python-vlc pandas matplotlib

Uso:
----
python app.py

Notas:
------
- A aplicação usa VLC para reprodução de vídeo, garantindo suporte a H.265/HEVC
- Os vídeos de teste são baralhados automaticamente para evitar viés
- Os nomes reais dos vídeos são ocultados durante o teste
- Os resultados são exportados em CSV e podem ser visualizados em gráficos
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import random
import os
import sys
import platform
from datetime import datetime
from typing import List, Dict, Optional

# Função para encontrar o caminho do VLC no macOS
def find_vlc_path():
    """Encontra o caminho do VLC no sistema."""
    if platform.system() == 'Darwin':  # macOS
        # Caminhos possíveis do VLC
        vlc_paths = [
            '/Applications/VLC.app/Contents/MacOS/lib',
            '/Applications/VLC.app/Contents/MacOS',
        ]
        
        for vlc_path in vlc_paths:
            if os.path.exists(vlc_path):
                # Verificar se existe libvlc.dylib ou libvlccore.dylib
                libvlc = os.path.join(vlc_path, 'libvlc.dylib')
                libvlccore = os.path.join(vlc_path, 'libvlccore.dylib')
                if os.path.exists(libvlc) or os.path.exists(libvlccore):
                    return vlc_path
        
        # Tentar Homebrew
        homebrew_paths = ['/opt/homebrew/lib', '/usr/local/lib']
        for hb_path in homebrew_paths:
            if os.path.exists(hb_path):
                libvlc = os.path.join(hb_path, 'libvlc.dylib')
                if os.path.exists(libvlc):
                    return hb_path
    
    return None

# Configurar variáveis de ambiente para VLC no macOS
vlc_path = find_vlc_path()
if vlc_path and platform.system() == 'Darwin':
    os.environ['DYLD_LIBRARY_PATH'] = vlc_path
    vlc_plugin_path = os.path.join(os.path.dirname(vlc_path), 'plugins')
    if os.path.exists(vlc_plugin_path):
        os.environ['VLC_PLUGIN_PATH'] = vlc_plugin_path

# Importar VLC com tratamento de erros
try:
    import vlc
except Exception as e:
    error_msg = (
        f"Erro ao carregar python-vlc: {e}\n\n"
        "No macOS, certifique-se de que:\n"
        "1. O VLC Media Player está instalado em /Applications/VLC.app\n"
        "2. O python-vlc está instalado: pip install python-vlc\n\n"
        "Se o problema persistir, tente:\n"
        "export DYLD_LIBRARY_PATH=/Applications/VLC.app/Contents/MacOS/lib\n"
        "export VLC_PLUGIN_PATH=/Applications/VLC.app/Contents/MacOS/plugins"
    )
    print(error_msg)
    sys.exit(1)

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class VideoRatingApp:
    """Aplicação principal para avaliação subjetiva de vídeos."""
    
    def __init__(self, root: tk.Tk):
        """Inicializa a aplicação."""
        self.root = root
        self.root.title("Avaliação Subjetiva de Vídeos")
        self.root.geometry("1400x800")
        
        # Variáveis de estado
        self.reference_video_path: Optional[str] = None
        self.test_videos: List[Dict] = []  # Lista com caminhos originais
        self.shuffled_test_videos: List[Dict] = []  # Lista baralhada
        self.current_test_index: int = 0
        self.ratings: List[Dict] = []  # Armazena as avaliações
        self.selected_rating: Optional[int] = None
        
        # Instâncias VLC
        self.reference_player: Optional[vlc.MediaPlayer] = None
        self.test_player: Optional[vlc.MediaPlayer] = None
        
        # Criar interface inicial
        self.create_file_selection_ui()
        
    def create_file_selection_ui(self):
        """Cria a interface de seleção de ficheiros."""
        # Limpar janela
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="Avaliação Subjetiva de Vídeos",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=20)
        
        # Frame para seleção de vídeo de referência
        ref_frame = ttk.LabelFrame(main_frame, text="Vídeo de Referência", padding="15")
        ref_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.ref_path_label = ttk.Label(
            ref_frame,
            text="Nenhum vídeo selecionado",
            foreground="gray"
        )
        self.ref_path_label.pack(side=tk.LEFT, padx=10)
        
        ref_button = ttk.Button(
            ref_frame,
            text="Selecionar Vídeo de Referência",
            command=self.select_reference_video
        )
        ref_button.pack(side=tk.RIGHT)
        
        # Frame para seleção de vídeos de teste
        test_frame = ttk.LabelFrame(main_frame, text="Vídeos de Teste", padding="15")
        test_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.test_count_label = ttk.Label(
            test_frame,
            text="0 vídeos selecionados",
            foreground="gray"
        )
        self.test_count_label.pack(side=tk.LEFT, padx=10)
        
        test_button = ttk.Button(
            test_frame,
            text="Selecionar Vídeos de Teste",
            command=self.select_test_videos
        )
        test_button.pack(side=tk.RIGHT)
        
        # Botão para iniciar teste
        self.start_button = ttk.Button(
            main_frame,
            text="Iniciar Teste",
            command=self.start_test,
            state=tk.DISABLED
        )
        self.start_button.pack(pady=30)
        
    def select_reference_video(self):
        """Abre diálogo para selecionar vídeo de referência."""
        file_path = filedialog.askopenfilename(
            title="Selecionar Vídeo de Referência",
            filetypes=[
                ("Ficheiros de vídeo", "*.mp4 *.avi *.mkv *.mov *.m4v *.hevc"),
                ("Todos os ficheiros", "*.*")
            ]
        )
        
        if file_path:
            self.reference_video_path = file_path
            filename = os.path.basename(file_path)
            self.ref_path_label.config(
                text=f"Referência: {filename}",
                foreground="black"
            )
            self.check_start_button_state()
    
    def select_test_videos(self):
        """Abre diálogo para selecionar múltiplos vídeos de teste."""
        file_paths = filedialog.askopenfilenames(
            title="Selecionar Vídeos de Teste",
            filetypes=[
                ("Ficheiros de vídeo", "*.mp4 *.avi *.mkv *.mov *.m4v *.hevc"),
                ("Todos os ficheiros", "*.*")
            ]
        )
        
        if file_paths:
            self.test_videos = []
            for idx, path in enumerate(file_paths):
                self.test_videos.append({
                    'video_id': idx + 1,
                    'caminho': path,
                    'nome_original': os.path.basename(path),
                    'ordem_original': idx + 1
                })
            
            count = len(self.test_videos)
            self.test_count_label.config(
                text=f"{count} vídeo(s) selecionado(s)",
                foreground="black"
            )
            self.check_start_button_state()
    
    def check_start_button_state(self):
        """Verifica se o botão 'Iniciar Teste' deve estar ativo."""
        if self.reference_video_path and len(self.test_videos) > 0:
            self.start_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.DISABLED)
    
    def start_test(self):
        """Inicia o teste, baralhando os vídeos de teste."""
        if not self.reference_video_path or len(self.test_videos) == 0:
            messagebox.showerror("Erro", "Selecione um vídeo de referência e pelo menos um vídeo de teste.")
            return
        
        # Baralhar os vídeos de teste
        self.shuffled_test_videos = self.test_videos.copy()
        random.shuffle(self.shuffled_test_videos)
        
        # Atribuir ordem baralhada
        for idx, video in enumerate(self.shuffled_test_videos):
            video['ordem_baralhada'] = idx + 1
        
        # Resetar estado
        self.current_test_index = 0
        self.ratings = []
        self.selected_rating = None
        
        # Criar interface de avaliação
        self.create_rating_ui()
    
    def create_rating_ui(self):
        """Cria a interface de avaliação side-by-side."""
        # Limpar janela
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior com informações (sem nomes reais)
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=10)
        
        total_videos = len(self.shuffled_test_videos)
        current_video_num = self.current_test_index + 1
        self.progress_label = ttk.Label(
            info_frame,
            text=f"Vídeo {current_video_num} de {total_videos}",
            font=("Arial", 12, "bold")
        )
        self.progress_label.pack()
        
        # Frame para os vídeos (side-by-side)
        video_frame = ttk.Frame(main_frame)
        video_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Frame para vídeo de referência (esquerda)
        ref_video_frame = ttk.LabelFrame(video_frame, text="Referência", padding="5")
        ref_video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Frame para vídeo de teste (direita)
        test_video_frame = ttk.LabelFrame(video_frame, text="Vídeo de Teste", padding="5")
        test_video_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Criar players VLC
        self.setup_video_players(ref_video_frame, test_video_frame)
        
        # Frame para botões de controlo de vídeo
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        play_button = ttk.Button(
            control_frame,
            text="▶ Play/Pause",
            command=self.toggle_play_pause
        )
        play_button.pack(side=tk.LEFT, padx=10)
        
        stop_button = ttk.Button(
            control_frame,
            text="⏹ Stop",
            command=self.stop_videos
        )
        stop_button.pack(side=tk.LEFT, padx=10)
        
        # Frame para botões de nota (0-10)
        rating_frame = ttk.LabelFrame(main_frame, text="Avalie a diferença em relação à referência (0 = igual, 10 = extremamente degradado)", padding="10")
        rating_frame.pack(fill=tk.X, pady=10)
        
        self.rating_buttons = []
        button_frame = ttk.Frame(rating_frame)
        button_frame.pack()
        
        for i in range(11):
            btn = ttk.Button(
                button_frame,
                text=str(i),
                width=4,
                command=lambda n=i: self.select_rating(n)
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.rating_buttons.append(btn)
        
        # Botão Continuar
        continue_frame = ttk.Frame(main_frame)
        continue_frame.pack(fill=tk.X, pady=20)
        
        continue_button = ttk.Button(
            continue_frame,
            text="Continuar",
            command=self.continue_to_next,
            style="Accent.TButton"
        )
        continue_button.pack()
        
        # Carregar vídeos
        self.load_current_videos()
    
    def setup_video_players(self, ref_frame: ttk.Frame, test_frame: ttk.Frame):
        """Configura os players VLC para os frames."""
        # Criar instância VLC com caminho explícito no macOS se necessário
        vlc_path = find_vlc_path()
        if vlc_path and platform.system() == 'Darwin':
            # Criar instância com argumentos para especificar o caminho
            vlc_args = [
                '--intf', 'dummy',
                '--quiet',
                '--no-video-title-show',
            ]
            instance = vlc.Instance(vlc_args)
        else:
            instance = vlc.Instance()
        
        # Player de referência
        self.reference_player = instance.media_player_new()
        self._set_vlc_window(self.reference_player, ref_frame)
        
        # Player de teste
        self.test_player = instance.media_player_new()
        self._set_vlc_window(self.test_player, test_frame)
    
    def _set_vlc_window(self, player: vlc.MediaPlayer, frame: ttk.Frame):
        """Configura a janela do player VLC de acordo com o sistema operativo."""
        system = platform.system()
        
        try:
            if system == 'Windows':
                # Windows
                player.set_hwnd(frame.winfo_id())
            elif system == 'Darwin':
                # macOS
                # No macOS, pode ser necessário usar set_nsobject
                # Alternativamente, podemos usar set_xwindow se disponível
                try:
                    player.set_nsobject(frame.winfo_id())
                except AttributeError:
                    # Fallback para xwindow se nsobject não estiver disponível
                    player.set_xwindow(frame.winfo_id())
            else:
                # Linux e outros sistemas Unix
                player.set_xwindow(frame.winfo_id())
        except Exception as e:
            # Se falhar, tentar método alternativo
            print(f"Aviso: Não foi possível configurar a janela VLC: {e}")
            print("O vídeo pode abrir numa janela separada.")
    
    def load_current_videos(self):
        """Carrega os vídeos atuais (referência e teste atual)."""
        # Carregar vídeo de referência
        if self.reference_video_path:
            media = vlc.Media(self.reference_video_path)
            self.reference_player.set_media(media)
        
        # Carregar vídeo de teste atual
        if self.current_test_index < len(self.shuffled_test_videos):
            current_video = self.shuffled_test_videos[self.current_test_index]
            media = vlc.Media(current_video['caminho'])
            self.test_player.set_media(media)
        
        # Resetar seleção de nota
        self.selected_rating = None
        self.update_rating_buttons()
    
        # Atualizar UI e iniciar reprodução após um pequeno delay
        # para garantir que o VLC está pronto
        self.root.update_idletasks()
        self.root.after(100, self._start_playing_videos)
    
    def _start_playing_videos(self):
        """Inicia a reprodução dos vídeos após o delay."""
        if self.reference_player:
            self.reference_player.play()
        if self.test_player:
            self.test_player.play()
    
    def toggle_play_pause(self):
        """Alterna play/pause em ambos os vídeos."""
        if self.reference_player:
            if self.reference_player.is_playing():
                self.reference_player.pause()
            else:
                self.reference_player.play()
        
        if self.test_player:
            if self.test_player.is_playing():
                self.test_player.pause()
            else:
                self.test_player.play()
    
    def stop_videos(self):
        """Para ambos os vídeos."""
        if self.reference_player:
            self.reference_player.stop()
        if self.test_player:
            self.test_player.stop()
    
    def select_rating(self, rating: int):
        """Seleciona uma nota de 0 a 10."""
        self.selected_rating = rating
        self.update_rating_buttons()
    
    def update_rating_buttons(self):
        """Atualiza a aparência dos botões de nota."""
        for idx, btn in enumerate(self.rating_buttons):
            if idx == self.selected_rating:
                btn.config(style="Accent.TButton")
            else:
                btn.config(style="TButton")
    
    def continue_to_next(self):
        """Avança para o próximo vídeo de teste ou termina o teste."""
        if self.selected_rating is None:
            messagebox.showerror(
                "Erro",
                "Selecione uma nota entre 0 e 10 antes de continuar."
            )
            return
        
        # Pausar vídeos antes de avançar (para prevenir crashes)
        if self.reference_player:
            self.reference_player.pause()
        if self.test_player:
            self.test_player.pause()
        
        # Guardar avaliação
        current_video = self.shuffled_test_videos[self.current_test_index]
        rating_data = {
            'video_id': current_video['video_id'],
            'nome_original': current_video['nome_original'],
            'caminho': current_video['caminho'],
            'ordem_baralhada': current_video['ordem_baralhada'],
            'nota': self.selected_rating,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.ratings.append(rating_data)
        
        # Avançar para próximo vídeo
        self.current_test_index += 1
        
        if self.current_test_index < len(self.shuffled_test_videos):
            # Carregar próximo vídeo
            self.load_current_videos()
            # Atualizar label de progresso
            if hasattr(self, 'progress_label'):
                total_videos = len(self.shuffled_test_videos)
                current_video_num = self.current_test_index + 1
                self.progress_label.config(text=f"Vídeo {current_video_num} de {total_videos}")
        else:
            # Teste terminado - mostrar resumo
            self.show_summary()
    
    def show_summary(self):
        """Mostra o resumo dos resultados e opções de exportação."""
        # Parar vídeos
        self.stop_videos()
        
        # Limpar janela
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(
            main_frame,
            text="Teste Concluído",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=20)
        
        # Tabela de resultados
        results_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Criar Treeview para tabela
        columns = ('video_id', 'nome_original', 'ordem_baralhada', 'nota')
        tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=10)
        
        tree.heading('video_id', text='ID')
        tree.heading('nome_original', text='Nome do Vídeo')
        tree.heading('ordem_baralhada', text='Ordem de Apresentação')
        tree.heading('nota', text='Nota')
        
        tree.column('video_id', width=50)
        tree.column('nome_original', width=400)
        tree.column('ordem_baralhada', width=150)
        tree.column('nota', width=80)
        
        # Adicionar dados
        for rating in self.ratings:
            tree.insert('', tk.END, values=(
                rating['video_id'],
                rating['nome_original'],
                rating['ordem_baralhada'],
                rating['nota']
            ))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame para botões
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        export_csv_button = ttk.Button(
            button_frame,
            text="Exportar CSV",
            command=self.export_csv
        )
        export_csv_button.pack(side=tk.LEFT, padx=10)
        
        generate_graph_button = ttk.Button(
            button_frame,
            text="Gerar Gráficos",
            command=self.generate_graphs
        )
        generate_graph_button.pack(side=tk.LEFT, padx=10)
        
        new_test_button = ttk.Button(
            button_frame,
            text="Novo Teste",
            command=self.create_file_selection_ui
        )
        new_test_button.pack(side=tk.LEFT, padx=10)
    
    def export_csv(self):
        """Exporta os resultados para um ficheiro CSV."""
        if not self.ratings:
            messagebox.showerror("Erro", "Não há dados para exportar.")
            return
        
        # Diálogo para guardar ficheiro
        file_path = filedialog.asksaveasfilename(
            title="Guardar CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                df = pd.DataFrame(self.ratings)
                df.to_csv(file_path, index=False, encoding='utf-8')
                messagebox.showinfo("Sucesso", f"CSV exportado com sucesso para:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar CSV:\n{str(e)}")
    
    def generate_graphs(self):
        """Gera e mostra gráficos dos resultados."""
        if not self.ratings:
            messagebox.showerror("Erro", "Não há dados para gerar gráficos.")
            return
        
        # Criar janela para gráficos
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Gráficos de Resultados")
        graph_window.geometry("1000x600")
        
        # Criar figura matplotlib
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Preparar dados
        df = pd.DataFrame(self.ratings)
        nomes = df['nome_original'].tolist()
        notas = df['nota'].tolist()
        
        # Criar gráfico de barras
        bars = ax.bar(range(len(nomes)), notas, color='steelblue', alpha=0.7)
        ax.set_xlabel('Vídeos de Teste', fontsize=12)
        ax.set_ylabel('Nota (0-10)', fontsize=12)
        ax.set_title('Avaliação Subjetiva de Qualidade de Vídeo', fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(nomes)))
        ax.set_xticklabels(nomes, rotation=45, ha='right')
        ax.set_ylim(0, 10)
        ax.grid(axis='y', alpha=0.3)
        
        # Adicionar valores nas barras
        for i, (bar, nota) in enumerate(zip(bars, notas)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{nota}',
                   ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Embed no Tkinter
        canvas = FigureCanvasTkAgg(fig, graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Botão para guardar gráfico
        save_button = ttk.Button(
            graph_window,
            text="Guardar Gráfico como PNG",
            command=lambda: self.save_graph(fig)
        )
        save_button.pack(pady=10)
    
    def save_graph(self, fig):
        """Guarda o gráfico como imagem PNG."""
        file_path = filedialog.asksaveasfilename(
            title="Guardar Gráfico",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                fig.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Sucesso", f"Gráfico guardado com sucesso para:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao guardar gráfico:\n{str(e)}")
    
    def cleanup(self):
        """Limpa recursos ao fechar a aplicação."""
        if self.reference_player:
            self.reference_player.stop()
            self.reference_player.release()
        if self.test_player:
            self.test_player.stop()
            self.test_player.release()


def main():
    """Função principal."""
    # Verificar se o VLC está disponível
    try:
        instance = vlc.Instance()
        test_player = instance.media_player_new()
        test_player.release()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()  # Esconder janela principal
        
        if platform.system() == 'Darwin':
            error_msg = (
                "Erro ao carregar VLC no macOS\n\n"
                "O python-vlc não conseguiu encontrar as bibliotecas do VLC.\n\n"
                "Soluções possíveis:\n\n"
                "1. Certifique-se de que o VLC está instalado em /Applications/VLC.app\n"
                "   Descarregue de: https://www.videolan.org/vlc/\n\n"
                "2. Execute a aplicação usando o script run_macos.sh:\n"
                "   chmod +x run_macos.sh\n"
                "   ./run_macos.sh\n\n"
                "3. Ou configure manualmente as variáveis de ambiente:\n"
                "   export DYLD_LIBRARY_PATH=/Applications/VLC.app/Contents/MacOS/lib\n"
                "   export VLC_PLUGIN_PATH=/Applications/VLC.app/Contents/MacOS/plugins\n"
                "   python app.py\n\n"
                f"Erro técnico: {str(e)}"
            )
        else:
            error_msg = (
                f"O VLC Media Player não foi encontrado ou não está configurado corretamente.\n\n"
                f"Por favor, instale o VLC Media Player:\n"
                f"https://www.videolan.org/vlc/\n\n"
                f"Erro técnico: {str(e)}"
            )
        
        messagebox.showerror("Erro - VLC não encontrado", error_msg)
        root.destroy()
        return
    
    root = tk.Tk()
    app = VideoRatingApp(root)
    
    # Handler para fechar janela
    def on_closing():
        app.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

