#!/usr/bin/env python3
"""
Aplicação para testes subjetivos de qualidade de vídeo
Permite comparar vídeos distorcidos com um vídeo de referência
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import random
import csv
import os
import platform
import threading
import time
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageTk
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Usar backend não-interativo
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit
from skimage.metrics import structural_similarity as ssim
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai


class VideoQualityTestApp:
    """Aplicação principal para testes de qualidade de vídeo"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Teste Subjetivo de Qualidade de Vídeo")
        self.root.geometry("1200x800")
        
        # Variáveis de estado
        self.reference_video_path = None
        self.distorted_videos = []
        self.current_trial_index = 0
        self.trial_order = []
        self.results = []
        self.nome_do_teste = None
        
        # Caputadores de vídeo OpenCV
        self.reference_cap = None
        self.distorted_cap = None
        
        # Estado de reprodução
        self.is_playing = False
        self.video_thread = None
        self.stop_video = False
        
        # FPS e timing para sincronização
        self.fps = 30.0
        self.frame_time = 1.0 / self.fps
        
        # Criar interface inicial
        self.create_welcome_screen()
    
    def create_welcome_screen(self):
        """Cria o ecrã inicial para configuração do teste"""
        # Limpar widgets existentes
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="Teste Subjetivo de Qualidade de Vídeo", 
                               font=("Arial", 18, "bold"))
        title_label.pack(pady=20)
        
        # Nome do teste
        subject_frame = ttk.Frame(main_frame)
        subject_frame.pack(pady=10)
        
        ttk.Label(subject_frame, text="Nome do Teste:").pack(side=tk.LEFT, padx=5)
        self.nome_teste_entry = ttk.Entry(subject_frame, width=30)
        self.nome_teste_entry.pack(side=tk.LEFT, padx=5)
        
        # Botão para selecionar vídeo de referência
        ref_frame = ttk.Frame(main_frame)
        ref_frame.pack(pady=20)
        
        ttk.Label(ref_frame, text="Vídeo de Referência:", font=("Arial", 12)).pack(pady=5)
        self.ref_path_label = ttk.Label(ref_frame, text="Nenhum ficheiro selecionado", 
                                        foreground="gray")
        self.ref_path_label.pack(pady=5)
        
        ttk.Button(ref_frame, text="Selecionar Vídeo de Referência", 
                  command=self.select_reference_video).pack(pady=5)
        
        # Botão para selecionar vídeos distorcidos
        dist_frame = ttk.Frame(main_frame)
        dist_frame.pack(pady=20)
        
        ttk.Label(dist_frame, text="Vídeos Distorcidos:", font=("Arial", 12)).pack(pady=5)
        self.dist_path_label = ttk.Label(dist_frame, text="Nenhum ficheiro selecionado", 
                                         foreground="gray")
        self.dist_path_label.pack(pady=5)
        
        ttk.Button(dist_frame, text="Selecionar Vídeos Distorcidos", 
                  command=self.select_distorted_videos).pack(pady=5)
        
        # Botão para iniciar teste
        self.start_button = ttk.Button(main_frame, text="Iniciar Teste", 
                                       command=self.start_test, state=tk.DISABLED)
        self.start_button.pack(pady=30)
    
    def select_reference_video(self):
        """Abre diálogo para selecionar vídeo de referência"""
        file_path = filedialog.askopenfilename(
            title="Selecionar Vídeo de Referência",
            filetypes=[("Vídeo files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"), 
                      ("All files", "*.*")]
        )
        if file_path:
            self.reference_video_path = file_path
            filename = os.path.basename(file_path)
            self.ref_path_label.config(text=filename, foreground="black")
            self.check_ready_to_start()
    
    def select_distorted_videos(self):
        """Abre diálogo para selecionar múltiplos vídeos distorcidos"""
        file_paths = filedialog.askopenfilenames(
            title="Selecionar Vídeos Distorcidos",
            filetypes=[("Vídeo files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"), 
                      ("All files", "*.*")]
        )
        if file_paths:
            self.distorted_videos = list(file_paths)
            count = len(self.distorted_videos)
            self.dist_path_label.config(
                text=f"{count} ficheiro(s) selecionado(s)", 
                foreground="black"
            )
            self.check_ready_to_start()
    
    def check_ready_to_start(self):
        """Verifica se está tudo pronto para iniciar o teste"""
        if self.reference_video_path and self.distorted_videos:
            self.start_button.config(state=tk.NORMAL)
    
    def start_test(self):
        """Inicia o teste após verificar dados do teste"""
        nome_teste = self.nome_teste_entry.get().strip()
        if not nome_teste:
            messagebox.showwarning("Aviso", "Por favor, introduza o nome do teste.")
            return
        
        self.nome_do_teste = nome_teste
        
        # Criar ordem aleatória dos vídeos distorcidos
        self.trial_order = list(range(len(self.distorted_videos)))
        random.shuffle(self.trial_order)
        self.current_trial_index = 0
        
        # Criar interface de teste
        self.create_test_screen()
    
    def create_test_screen(self):
        """Cria a interface de teste com os dois players de vídeo"""
        # Limpar widgets existentes
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Frame principal (container para tudo)
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Informação do teste (no topo)
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        trial_num = self.current_trial_index + 1
        total_trials = len(self.distorted_videos)
        info_text = f"Ensaio {trial_num}/{total_trials} | Teste: {self.nome_do_teste}"
        ttk.Label(info_frame, text=info_text, font=("Arial", 12, "bold")).pack()
        
        # Frame de controlos fixo no bottom (empacotar primeiro com side=BOTTOM para ficar sempre no fundo)
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
        
        # Frame para os vídeos (side by side) - ocupa espaço disponível acima dos controlos
        video_frame = ttk.Frame(main_frame)
        video_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Frame para vídeo de referência (esquerda)
        ref_video_frame = ttk.LabelFrame(video_frame, text="Referência", padding="5")
        ref_video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Label para exibir o vídeo de referência (com tamanho fixo)
        self.reference_video_label = tk.Label(ref_video_frame, bg="black", text="Carregando...")
        self.reference_video_label.pack(fill=tk.BOTH, expand=True)
        
        # Frame para vídeo distorcido (direita)
        dist_video_frame = ttk.LabelFrame(video_frame, text="Distorcido", padding="5")
        dist_video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.distorted_video_label = tk.Label(dist_video_frame, bg="black", text="Carregando...")
        self.distorted_video_label.pack(fill=tk.BOTH, expand=True)
        
        # Guardar tamanhos fixos dos labels após serem criados
        self.root.update_idletasks()
        self.update_label_sizes()
        
        # Bind para atualizar tamanhos quando a janela for redimensionada
        self.root.bind('<Configure>', self.on_window_configure)
        
        # Botões de controlo
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(pady=5)
        
        self.play_pause_button = ttk.Button(button_frame, text="▶ Play", 
                                           command=self.toggle_play_pause)
        self.play_pause_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="↻ Repetir", 
                  command=self.restart_videos).pack(side=tk.LEFT, padx=5)
        
        # Escala de avaliação
        rating_frame = ttk.LabelFrame(controls_frame, text="Avaliação da Qualidade (0-10)", 
                                      padding="10")
        rating_frame.pack(pady=10)
        
        self.rating_var = tk.IntVar(value=5)
        
        # Escala visual com slider
        scale_frame = ttk.Frame(rating_frame)
        scale_frame.pack()
        
        ttk.Label(scale_frame, text="0").pack(side=tk.LEFT, padx=5)
        self.rating_scale = ttk.Scale(scale_frame, from_=0, to=10, 
                                      variable=self.rating_var, 
                                      orient=tk.HORIZONTAL, length=400,
                                      command=self.on_scale_change)
        self.rating_scale.pack(side=tk.LEFT, padx=5)
        ttk.Label(scale_frame, text="10").pack(side=tk.LEFT, padx=5)
        
        # Valor numérico da avaliação
        self.rating_label = ttk.Label(rating_frame, text="5", 
                                      font=("Arial", 16, "bold"))
        self.rating_label.pack(pady=5)
        
        # Botão Next
        next_frame = ttk.Frame(controls_frame)
        next_frame.pack(pady=10)
        
        self.next_button = ttk.Button(next_frame, text="Next →", 
                                      command=self.next_trial, 
                                      style="Accent.TButton")
        self.next_button.pack()
        
        # Inicializar players de vídeo
        self.setup_video_players()
    
    def update_label_sizes(self):
        """Atualiza os tamanhos dos labels (chamado apenas quando necessário)"""
        try:
            ref_width = self.reference_video_label.winfo_width()
            ref_height = self.reference_video_label.winfo_height()
            dist_width = self.distorted_video_label.winfo_width()
            dist_height = self.distorted_video_label.winfo_height()
            
            # Só atualizar se os tamanhos são válidos e diferentes
            if ref_width > 1 and ref_height > 1:
                self.ref_label_width = ref_width
                self.ref_label_height = ref_height
            elif not hasattr(self, 'ref_label_width'):
                self.ref_label_width = 500
                self.ref_label_height = 400
            
            if dist_width > 1 and dist_height > 1:
                self.dist_label_width = dist_width
                self.dist_label_height = dist_height
            elif not hasattr(self, 'dist_label_width'):
                self.dist_label_width = 500
                self.dist_label_height = 400
        except:
            # Se houver erro, usar valores padrão
            if not hasattr(self, 'ref_label_width'):
                self.ref_label_width = 500
                self.ref_label_height = 400
            if not hasattr(self, 'dist_label_width'):
                self.dist_label_width = 500
                self.dist_label_height = 400
    
    def on_window_configure(self, event=None):
        """Callback quando a janela é redimensionada"""
        # Atualizar tamanhos apenas se for o evento da janela principal
        if event and event.widget == self.root:
            self.root.after_idle(self.update_label_sizes)
    
    def setup_video_players(self):
        """Configura os captadores OpenCV para os dois vídeos"""
        # Abrir vídeos com OpenCV
        self.reference_cap = cv2.VideoCapture(self.reference_video_path)
        
        current_distorted_index = self.trial_order[self.current_trial_index]
        self.distorted_cap = cv2.VideoCapture(self.distorted_videos[current_distorted_index])
        
        # Obter FPS dos vídeos (usar o menor para sincronização)
        ref_fps = self.reference_cap.get(cv2.CAP_PROP_FPS) or 30.0
        dist_fps = self.distorted_cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.fps = min(ref_fps, dist_fps)
        self.frame_time = 1.0 / self.fps
        
        # Estado inicial: pausado
        self.is_playing = False
        self.stop_video = False
        
        # Iniciar thread de reprodução
        self.start_video_thread()
    
    def start_video_thread(self):
        """Inicia a thread de reprodução de vídeo"""
        if self.video_thread is not None and self.video_thread.is_alive():
            self.stop_video = True
            self.video_thread.join(timeout=1.0)
        
        self.stop_video = False
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()
    
    def video_loop(self):
        """Loop principal de reprodução de vídeo (executa em thread separada)"""
        while not self.stop_video:
            if self.is_playing:
                # Ler frames de ambos os vídeos
                ret_ref, frame_ref = self.reference_cap.read()
                ret_dist, frame_dist = self.distorted_cap.read()
                
                if not ret_ref or not ret_dist:
                    # Fim do vídeo - parar reprodução
                    self.is_playing = False
                    self.root.after(0, lambda: self.play_pause_button.config(text="▶ Play"))
                    # Reiniciar para o início para próxima reprodução
                    self.reference_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.distorted_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # Redimensionar frames para caber nos labels
                frame_ref = self.resize_frame(frame_ref, self.reference_video_label)
                frame_dist = self.resize_frame(frame_dist, self.distorted_video_label)
                
                # Converter para formato compatível com Tkinter
                img_ref = Image.fromarray(cv2.cvtColor(frame_ref, cv2.COLOR_BGR2RGB))
                img_dist = Image.fromarray(cv2.cvtColor(frame_dist, cv2.COLOR_BGR2RGB))
                
                # Atualizar labels na thread principal (usar método auxiliar para evitar problemas de closure)
                self.root.after(0, self._update_frames, img_ref, img_dist)
                
                # Controlar FPS
                time.sleep(self.frame_time)
            else:
                # Quando pausado, apenas esperar
                time.sleep(0.1)
    
    def resize_frame(self, frame, label):
        """Redimensiona o frame para caber no label mantendo aspect ratio"""
        if frame is None:
            return None
        
        # Usar tamanhos fixos guardados (evita crescimento infinito)
        if label == self.reference_video_label:
            label_width = getattr(self, 'ref_label_width', 500)
            label_height = getattr(self, 'ref_label_height', 400)
        else:
            label_width = getattr(self, 'dist_label_width', 500)
            label_height = getattr(self, 'dist_label_height', 400)
        
        # Se os tamanhos ainda não estão definidos, usar valores padrão
        if label_width <= 1 or label_height <= 1:
            label_width = 500
            label_height = 400
        
        # Calcular novo tamanho mantendo aspect ratio
        frame_height, frame_width = frame.shape[:2]
        if frame_height == 0 or frame_width == 0:
            return frame
        
        aspect_ratio = frame_width / frame_height
        
        if label_width / label_height > aspect_ratio:
            new_height = label_height
            new_width = int(new_height * aspect_ratio)
        else:
            new_width = label_width
            new_height = int(new_width / aspect_ratio)
        
        # Garantir que os tamanhos são válidos
        new_width = max(1, min(new_width, label_width))
        new_height = max(1, min(new_height, label_height))
        
        # Redimensionar
        resized = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        # Criar frame preto do tamanho fixo do label e centralizar o vídeo
        result = np.zeros((label_height, label_width, 3), dtype=np.uint8)
        y_offset = (label_height - new_height) // 2
        x_offset = (label_width - new_width) // 2
        result[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized
        
        return result
    
    def _update_frames(self, img_ref, img_dist):
        """Método auxiliar para atualizar frames (evita problemas de closure)"""
        self.update_video_frames(img_ref, img_dist)
    
    def update_video_frames(self, img_ref, img_dist):
        """Atualiza os frames dos vídeos nos labels (executa na thread principal)"""
        try:
            # As imagens já vêm redimensionadas do resize_frame com tamanho fixo
            photo_ref = ImageTk.PhotoImage(image=img_ref)
            photo_dist = ImageTk.PhotoImage(image=img_dist)
            
            # Atualizar apenas a imagem, sem alterar tamanho do label
            self.reference_video_label.config(image=photo_ref)
            self.reference_video_label.image = photo_ref  # Manter referência
            
            self.distorted_video_label.config(image=photo_dist)
            self.distorted_video_label.image = photo_dist  # Manter referência
        except Exception as e:
            # Ignorar erros de atualização (pode acontecer ao fechar)
            pass
    
    def toggle_play_pause(self):
        """Alterna entre play e pause para ambos os vídeos"""
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.play_pause_button.config(text="⏸ Pause")
        else:
            self.play_pause_button.config(text="▶ Play")
    
    def restart_videos(self):
        """Reinicia ambos os vídeos do início"""
        was_playing = self.is_playing
        self.is_playing = False
        
        # Reiniciar vídeos
        if self.reference_cap:
            self.reference_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        if self.distorted_cap:
            self.distorted_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        self.is_playing = was_playing
        if not self.is_playing:
            self.play_pause_button.config(text="▶ Play")
    
    def on_scale_change(self, value=None):
        """Atualiza o label quando o slider muda"""
        rating = int(self.rating_var.get())
        self.rating_label.config(text=str(rating))
    
    def next_trial(self):
        """Grava a resposta atual e avança para o próximo ensaio"""
        # Obter dados do ensaio atual
        current_distorted_index = self.trial_order[self.current_trial_index]
        distorted_filename = os.path.basename(self.distorted_videos[current_distorted_index])
        reference_filename = os.path.basename(self.reference_video_path)
        rating = int(self.rating_var.get())
        timestamp = datetime.now().isoformat()
        
        # Guardar resultado
        result = {
            'nome_do_teste': self.nome_do_teste,
            'reference_filename': reference_filename,
            'distorted_filename': distorted_filename,
            'trial_index': self.current_trial_index + 1,
            'rating_0_10': rating,
            'timestamp': timestamp
        }
        self.results.append(result)
        
        # Parar reprodução atual
        self.stop_video = True
        self.is_playing = False
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=1.0)
        
        if self.reference_cap:
            self.reference_cap.release()
        if self.distorted_cap:
            self.distorted_cap.release()
        
        # Avançar para próximo ensaio
        self.current_trial_index += 1
        
        if self.current_trial_index < len(self.distorted_videos):
            # Criar novo ecrã de teste
            self.create_test_screen()
        else:
            # Todos os ensaios concluídos
            self.save_results()
            self.show_completion_screen()
    
    def save_results(self):
        """Guarda os resultados num ficheiro CSV e gera análise"""
        if not self.results:
            return
        
        # Criar pasta com o nome do teste (sanitizar nome para evitar problemas com caminhos)
        safe_nome_teste = "".join(c for c in self.nome_do_teste if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_nome_teste = safe_nome_teste.replace(' ', '_')
        
        # Criar diretório para os resultados
        results_dir = os.path.join('.', safe_nome_teste)
        os.makedirs(results_dir, exist_ok=True)
        
        # Nome do ficheiro com timestamp
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = os.path.join(results_dir, f"results_{timestamp_str}.csv")
        
        # Escrever CSV
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['nome_do_teste', 'reference_filename', 'distorted_filename', 
                         'trial_index', 'rating_0_10', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in self.results:
                writer.writerow(result)
        
        # Gerar análise automática (tudo dentro da pasta do teste)
        try:
            pdf_file = self.generate_analysis(csv_filename, timestamp_str, results_dir)
            if pdf_file:
                messagebox.showinfo("Sucesso", 
                                   f"✓ Todos os ficheiros guardados em:\n{os.path.abspath(results_dir)}\n\n"
                                   f"✓ CSV: {os.path.basename(csv_filename)}\n"
                                   f"✓ PDF de dados gerado\n"
                                   f"✓ Análise com Gemini gerada (MD e PDF)")
            else:
                messagebox.showinfo("Sucesso", 
                                   f"✓ Todos os ficheiros guardados em:\n{os.path.abspath(results_dir)}\n\n"
                                   f"✓ CSV: {os.path.basename(csv_filename)}\n"
                                   f"✓ Análise Markdown gerada\n"
                                   f"⚠ PDF não foi gerado (verifique dependências)")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showwarning("Aviso", 
                                  f"Resultados guardados em:\n{os.path.abspath(results_dir)}\n\n"
                                  f"Erro ao gerar análise:\n{str(e)}\n\n"
                                  f"Verifique o console para mais detalhes.")
            print(f"Erro completo:\n{error_details}")
    
    def calculate_psnr(self, ref_path, dist_path):
        """Calcula PSNR médio entre dois vídeos"""
        ref_cap = cv2.VideoCapture(ref_path)
        dist_cap = cv2.VideoCapture(dist_path)
        
        psnr_values = []
        frame_count = 0
        
        while True:
            ret_ref, frame_ref = ref_cap.read()
            ret_dist, frame_dist = dist_cap.read()
            
            if not ret_ref or not ret_dist:
                break
            
            # Converter para grayscale se necessário
            if len(frame_ref.shape) == 3:
                frame_ref = cv2.cvtColor(frame_ref, cv2.COLOR_BGR2GRAY)
            if len(frame_dist.shape) == 3:
                frame_dist = cv2.cvtColor(frame_dist, cv2.COLOR_BGR2GRAY)
            
            # Calcular MSE
            mse = np.mean((frame_ref.astype(float) - frame_dist.astype(float)) ** 2)
            
            if mse == 0:
                psnr = 100  # Imagens idênticas
            else:
                psnr = 20 * np.log10(255.0 / np.sqrt(mse))
            
            psnr_values.append(psnr)
            frame_count += 1
            
            # Limitar a 100 frames para não demorar muito
            if frame_count >= 100:
                break
        
        ref_cap.release()
        dist_cap.release()
        
        return np.mean(psnr_values) if psnr_values else 0.0
    
    def calculate_ssim(self, ref_path, dist_path):
        """Calcula SSIM médio entre dois vídeos"""
        ref_cap = cv2.VideoCapture(ref_path)
        dist_cap = cv2.VideoCapture(dist_path)
        
        ssim_values = []
        frame_count = 0
        
        while True:
            ret_ref, frame_ref = ref_cap.read()
            ret_dist, frame_dist = dist_cap.read()
            
            if not ret_ref or not ret_dist:
                break
            
            # Converter para grayscale
            if len(frame_ref.shape) == 3:
                frame_ref = cv2.cvtColor(frame_ref, cv2.COLOR_BGR2GRAY)
            if len(frame_dist.shape) == 3:
                frame_dist = cv2.cvtColor(frame_dist, cv2.COLOR_BGR2GRAY)
            
            # Redimensionar se necessário (SSIM requer mesmo tamanho)
            if frame_ref.shape != frame_dist.shape:
                h, w = min(frame_ref.shape[0], frame_dist.shape[0]), min(frame_ref.shape[1], frame_dist.shape[1])
                frame_ref = cv2.resize(frame_ref, (w, h))
                frame_dist = cv2.resize(frame_dist, (w, h))
            
            # Calcular SSIM
            ssim_val = ssim(frame_ref, frame_dist, data_range=255)
            ssim_values.append(ssim_val)
            frame_count += 1
            
            # Limitar a 100 frames para não demorar muito
            if frame_count >= 100:
                break
        
        ref_cap.release()
        dist_cap.release()
        
        return np.mean(ssim_values) if ssim_values else 0.0
    
    def generate_analysis(self, csv_filename, timestamp_str, results_dir):
        """Gera análise completa: PSNR, SSIM, correlações e regressões"""
        # Ler CSV
        df = pd.read_csv(csv_filename)
        
        # Usar o diretório de resultados fornecido
        base_dir = results_dir
        base_name = f"analysis_{timestamp_str}"
        
        # Calcular métricas objetivas
        print("Calculando métricas objetivas...")
        psnr_values = []
        ssim_values = []
        mos_values = []
        distorted_files = []
        
        ref_path = self.reference_video_path
        
        for idx, row in df.iterrows():
            dist_filename = row['distorted_filename']
            # Encontrar caminho completo do vídeo distorcido
            dist_path = None
            for video_path in self.distorted_videos:
                if os.path.basename(video_path) == dist_filename:
                    dist_path = video_path
                    break
            
            if dist_path and os.path.exists(dist_path):
                print(f"Processando {dist_filename}...")
                psnr = self.calculate_psnr(ref_path, dist_path)
                ssim_val = self.calculate_ssim(ref_path, dist_path)
                
                psnr_values.append(psnr)
                ssim_values.append(ssim_val)
                mos_values.append(row['rating_0_10'])
                distorted_files.append(dist_filename)
        
        # Criar DataFrame com métricas
        metrics_df = pd.DataFrame({
            'distorted_filename': distorted_files,
            'MOS': mos_values,
            'PSNR': psnr_values,
            'SSIM': ssim_values
        })
        
        # Calcular correlações (com tratamento de arrays constantes)
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=stats.ConstantInputWarning)
            
            # Verificar se arrays têm variância antes de calcular correlação
            def safe_correlation(x, y, corr_func):
                if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
                    return 0.0
                try:
                    return corr_func(x, y)[0]
                except (ValueError, TypeError):
                    return 0.0
            
            pearson_psnr = safe_correlation(mos_values, psnr_values, stats.pearsonr)
            pearson_ssim = safe_correlation(mos_values, ssim_values, stats.pearsonr)
            spearman_psnr = safe_correlation(mos_values, psnr_values, stats.spearmanr)
            spearman_ssim = safe_correlation(mos_values, ssim_values, stats.spearmanr)
        
        # Regressão linear PSNR -> MOS
        try:
            slope_psnr, intercept_psnr, r_psnr, p_psnr, _ = stats.linregress(psnr_values, mos_values)
        except ValueError:
            slope_psnr, intercept_psnr, r_psnr, p_psnr = 0.0, 0.0, 0.0, 1.0
        
        # Regressão linear SSIM -> MOS
        try:
            slope_ssim, intercept_ssim, r_ssim, p_ssim, _ = stats.linregress(ssim_values, mos_values)
        except ValueError:
            slope_ssim, intercept_ssim, r_ssim, p_ssim = 0.0, 0.0, 0.0, 1.0
        
        # Regressão polinomial (grau 2) PSNR -> MOS
        try:
            poly_psnr = np.polyfit(psnr_values, mos_values, 2)
            poly_psnr_func = np.poly1d(poly_psnr)
        except (np.linalg.LinAlgError, ValueError):
            # Se falhar, usar regressão linear como fallback
            poly_psnr = [0.0, slope_psnr, intercept_psnr]
            poly_psnr_func = np.poly1d(poly_psnr)
        
        # Regressão polinomial (grau 2) SSIM -> MOS
        try:
            poly_ssim = np.polyfit(ssim_values, mos_values, 2)
            poly_ssim_func = np.poly1d(poly_ssim)
        except (np.linalg.LinAlgError, ValueError):
            # Se falhar, usar regressão linear como fallback
            poly_ssim = [0.0, slope_ssim, intercept_ssim]
            poly_ssim_func = np.poly1d(poly_ssim)
        
        # Gerar gráficos (dentro da pasta do teste)
        fig_dir = os.path.join(base_dir, "figures")
        os.makedirs(fig_dir, exist_ok=True)
        
        # Gráfico 1: Scatter PSNR vs MOS com regressão
        plt.figure(figsize=(10, 6))
        plt.scatter(psnr_values, mos_values, alpha=0.6, s=100)
        psnr_sorted = np.sort(psnr_values)
        plt.plot(psnr_sorted, slope_psnr * psnr_sorted + intercept_psnr, 
                'r--', label=f'Linear (R²={r_psnr**2:.3f})', linewidth=2)
        plt.plot(psnr_sorted, poly_psnr_func(psnr_sorted), 
                'g--', label='Polinomial (grau 2)', linewidth=2)
        plt.xlabel('PSNR (dB)', fontsize=12)
        plt.ylabel('MOS (Mean Opinion Score)', fontsize=12)
        plt.title(f'PSNR vs MOS - Correlação Pearson: {pearson_psnr:.3f}', fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, 'psnr_vs_mos.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Gráfico 2: Scatter SSIM vs MOS com regressão
        plt.figure(figsize=(10, 6))
        plt.scatter(ssim_values, mos_values, alpha=0.6, s=100)
        ssim_sorted = np.sort(ssim_values)
        plt.plot(ssim_sorted, slope_ssim * ssim_sorted + intercept_ssim, 
                'r--', label=f'Linear (R²={r_ssim**2:.3f})', linewidth=2)
        plt.plot(ssim_sorted, poly_ssim_func(ssim_sorted), 
                'g--', label='Polinomial (grau 2)', linewidth=2)
        plt.xlabel('SSIM', fontsize=12)
        plt.ylabel('MOS (Mean Opinion Score)', fontsize=12)
        plt.title(f'SSIM vs MOS - Correlação Pearson: {pearson_ssim:.3f}', fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, 'ssim_vs_mos.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Gráfico 3: Comparação de métricas
        plt.figure(figsize=(12, 6))
        x = np.arange(len(distorted_files))
        width = 0.35
        
        # Normalizar PSNR e SSIM para escala 0-10
        psnr_norm = (np.array(psnr_values) - np.min(psnr_values)) / (np.max(psnr_values) - np.min(psnr_values)) * 10
        ssim_norm = np.array(ssim_values) * 10
        
        plt.bar(x - width/2, mos_values, width, label='MOS (Subjetivo)', alpha=0.8)
        plt.bar(x + width/2, psnr_norm, width, label='PSNR (Normalizado)', alpha=0.8)
        plt.xlabel('Vídeo Distorcido', fontsize=12)
        plt.ylabel('Score (0-10)', fontsize=12)
        plt.title('Comparação: MOS vs PSNR Normalizado', fontsize=14)
        plt.xticks(x, [f"V{i+1}" for i in range(len(distorted_files))], rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, 'mos_vs_psnr_comparison.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        # Gerar documento Markdown
        md_filename = os.path.join(base_dir, f"{base_name}_analysis.md")
        
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(f"# Análise de Qualidade de Vídeo\n\n")
            f.write(f"**Nome do Teste:** {self.nome_do_teste}\n\n")
            f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Tabela de métricas
            f.write("## Métricas Objetivas e Subjetivas\n\n")
            f.write("| Vídeo | MOS | PSNR (dB) | SSIM |\n")
            f.write("|-------|-----|-----------|------|\n")
            for i, row in metrics_df.iterrows():
                f.write(f"| {row['distorted_filename']} | {row['MOS']:.1f} | {row['PSNR']:.2f} | {row['SSIM']:.3f} |\n")
            f.write("\n")
            
            # Correlações
            f.write("## Correlações\n\n")
            f.write("| Métrica | Pearson | Spearman |\n")
            f.write("|---------|---------|----------|\n")
            f.write(f"| PSNR | {pearson_psnr:.3f} | {spearman_psnr:.3f} |\n")
            f.write(f"| SSIM | {pearson_ssim:.3f} | {spearman_ssim:.3f} |\n")
            f.write("\n")
            
            # Regressões
            f.write("## Modelos de Regressão\n\n")
            f.write("### PSNR → MOS\n\n")
            f.write(f"- **Linear:** MOS = {slope_psnr:.3f} × PSNR + {intercept_psnr:.3f}\n")
            f.write(f"- **R² Linear:** {r_psnr**2:.3f}\n")
            f.write(f"- **Polinomial (grau 2):** MOS = {poly_psnr[0]:.3f} × PSNR² + {poly_psnr[1]:.3f} × PSNR + {poly_psnr[2]:.3f}\n")
            f.write("\n")
            
            f.write("### SSIM → MOS\n\n")
            f.write(f"- **Linear:** MOS = {slope_ssim:.3f} × SSIM + {intercept_ssim:.3f}\n")
            f.write(f"- **R² Linear:** {r_ssim**2:.3f}\n")
            f.write(f"- **Polinomial (grau 2):** MOS = {poly_ssim[0]:.3f} × SSIM² + {poly_ssim[1]:.3f} × SSIM + {poly_ssim[2]:.3f}\n")
            f.write("\n")
            
            # Gráficos (usar caminhos relativos - tudo na mesma pasta)
            f.write("## Gráficos\n\n")
            f.write(f"![PSNR vs MOS](figures/psnr_vs_mos.png)\n\n")
            f.write(f"![SSIM vs MOS](figures/ssim_vs_mos.png)\n\n")
            f.write(f"![Comparação MOS vs PSNR](figures/mos_vs_psnr_comparison.png)\n\n")
        
        # Converter MD para PDF e renomear para 'dados_...'
        pdf_file = self.md_to_pdf(md_filename, fig_dir)
        
        if pdf_file:
            # Renomear PDF para 'dados_...'
            dados_pdf = os.path.join(base_dir, f"dados_{timestamp_str}.pdf")
            if os.path.exists(pdf_file):
                os.rename(pdf_file, dados_pdf)
                pdf_file = dados_pdf
            
            # Gerar análise com Gemini
            try:
                self.generate_gemini_analysis(dados_pdf, md_filename, timestamp_str, base_dir, fig_dir)
            except Exception as e:
                print(f"⚠ Erro ao gerar análise com Gemini: {e}")
                print("Os dados foram gerados com sucesso, mas a análise automática falhou.")
        
        return pdf_file
    
    def generate_gemini_analysis(self, dados_pdf, md_filename, timestamp_str, base_dir, fig_dir):
        """Gera análise com Gemini AI baseada nos dados"""
        # Carregar variáveis de ambiente
        load_dotenv()
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        if not gemini_key:
            print("⚠ GEMINI_API_KEY não encontrada no .env")
            return None
        
        try:
            # Configurar Gemini
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            print("Enviando dados ao Gemini para análise...")
            
            # Ler conteúdo do Markdown para contexto
            with open(md_filename, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Preparar prompt com dados do Markdown
            prompt = f"""
Analisa os seguintes dados de um teste subjetivo de qualidade de vídeo e fornece uma análise detalhada com conclusões.

Dados do teste:
{md_content}

Por favor, fornece:
1. Uma análise geral dos resultados
2. Interpretação das correlações entre métricas objetivas (PSNR, SSIM) e subjetivas (MOS)
3. Avaliação da qualidade dos modelos de regressão
4. Conclusões sobre que métricas objetivas melhor prevêem a qualidade percebida

Formata a resposta em Markdown com títulos, parágrafos e listas quando apropriado.
"""
            
            # Enviar prompt ao Gemini (usando apenas texto)
            response = model.generate_content(prompt)
            
            # Obter texto da resposta
            analysis_text = response.text
            
            # Gerar ficheiro Markdown com análise
            analysis_md = os.path.join(base_dir, f"analise_{timestamp_str}.md")
            with open(analysis_md, 'w', encoding='utf-8') as f:
                f.write(f"# Análise de Qualidade de Vídeo - Conclusões\n\n")
                f.write(f"**Nome do Teste:** {self.nome_do_teste}\n\n")
                f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                f.write(analysis_text)
            
            print(f"✓ Análise gerada: {analysis_md}")
            
            # Converter para PDF
            analysis_pdf = self.md_to_pdf(analysis_md, fig_dir)
            if analysis_pdf:
                # Renomear para analise_...
                final_analysis_pdf = os.path.join(base_dir, f"analise_{timestamp_str}.pdf")
                if os.path.exists(analysis_pdf):
                    os.rename(analysis_pdf, final_analysis_pdf)
                print(f"✓ PDF de análise gerado: {final_analysis_pdf}")
            
        except Exception as e:
            print(f"Erro ao gerar análise com Gemini: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def md_to_pdf(self, md_file, fig_dir):
        """Converte Markdown para PDF usando reportlab"""
        pdf_file = md_file.replace('.md', '.pdf')
        
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            import re
            
            # Ler conteúdo do Markdown
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Criar documento PDF
            doc = SimpleDocTemplate(
                pdf_file,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2.5*cm,
                bottomMargin=2.5*cm
            )
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=20,
                alignment=TA_LEFT
            )
            heading2_style = ParagraphStyle(
                'CustomHeading2',
                parent=styles['Heading2'],
                fontSize=18,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=15,
                spaceBefore=25
            )
            heading3_style = ParagraphStyle(
                'CustomHeading3',
                parent=styles['Heading3'],
                fontSize=14,
                textColor=colors.HexColor('#555'),
                spaceAfter=10,
                spaceBefore=20
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                leading=16,
                alignment=TA_JUSTIFY
            )
            
            # Elementos do PDF
            story = []
            
            # Parsear Markdown linha por linha
            lines = md_content.split('\n')
            i = 0
            current_table_rows = []
            in_table = False
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Título H1
                if line.startswith('# ') and not line.startswith('##'):
                    text = line[2:].strip()
                    story.append(Paragraph(text, title_style))
                    story.append(Spacer(1, 12))
                
                # Título H2
                elif line.startswith('## ') and not line.startswith('###'):
                    text = line[3:].strip()
                    story.append(Spacer(1, 12))
                    story.append(Paragraph(text, heading2_style))
                    story.append(Spacer(1, 12))
                
                # Título H3
                elif line.startswith('### '):
                    text = line[4:].strip()
                    story.append(Spacer(1, 10))
                    story.append(Paragraph(text, heading3_style))
                    story.append(Spacer(1, 10))
                
                # Tabela
                elif line.startswith('|'):
                    if not in_table:
                        in_table = True
                        current_table_rows = []
                    # Parsear linha da tabela
                    cells = [cell.strip() for cell in line.split('|')[1:-1]]
                    current_table_rows.append(cells)
                
                # Linha separadora de tabela
                elif line.startswith('|---') and in_table:
                    i += 1
                    continue
                
                # Fim da tabela ou processar tabela
                elif in_table and line == '':
                    if current_table_rows:
                        # Criar tabela
                        table_data = current_table_rows
                        table = Table(table_data)
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                            ('FONTSIZE', (0, 1), (-1, -1), 9),
                            ('TOPPADDING', (0, 1), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                        ]))
                        story.append(table)
                        story.append(Spacer(1, 12))
                        current_table_rows = []
                        in_table = False
                
                # Imagem
                elif '![' in line and '](' in line:
                    # Extrair caminho da imagem
                    match = re.search(r'!\[.*?\]\((.*?)\)', line)
                    if match:
                        img_path = match.group(1)
                        # Se for caminho relativo, tornar absoluto
                        if not os.path.isabs(img_path):
                            img_path = os.path.join(os.path.dirname(md_file), img_path)
                        
                        if os.path.exists(img_path):
                            try:
                                img = Image(img_path, width=16*cm, height=12*cm, kind='proportional')
                                story.append(Spacer(1, 12))
                                story.append(img)
                                story.append(Spacer(1, 12))
                            except:
                                story.append(Paragraph(f"[Imagem: {os.path.basename(img_path)}]", normal_style))
                
                # Lista
                elif line.startswith('- ') or line.startswith('* '):
                    text = line[2:].strip()
                    # Remover formatação markdown básica
                    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                    story.append(Paragraph(f"• {text}", normal_style))
                
                # Parágrafo normal
                elif line and not line.startswith('---'):
                    # Remover formatação markdown básica
                    text = line
                    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                    text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
                    story.append(Paragraph(text, normal_style))
                    story.append(Spacer(1, 6))
                
                # Separador
                elif line.startswith('---'):
                    story.append(Spacer(1, 20))
                
                i += 1
            
            # Construir PDF
            doc.build(story)
            print(f"✓ PDF gerado com sucesso usando reportlab: {pdf_file}")
            return pdf_file
            
        except ImportError:
            print("\n⚠ reportlab não está instalado.")
            print("Instale com: pip install reportlab")
            print(f"\nO ficheiro Markdown foi gerado: {os.path.abspath(md_file)}")
            return None
        except Exception as e:
            print(f"\n⚠ Erro ao gerar PDF: {str(e)}")
            print(f"O ficheiro Markdown foi gerado: {os.path.abspath(md_file)}")
            import traceback
            traceback.print_exc()
            return None
    
    def show_completion_screen(self):
        """Mostra ecrã de conclusão do teste"""
        # Limpar widgets existentes
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="40")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Mensagem de conclusão
        ttk.Label(main_frame, text="Teste Concluído!", 
                 font=("Arial", 24, "bold")).pack(pady=20)
        
        ttk.Label(main_frame, 
                 text=f"Obrigado pela sua participação!\n\n"
                      f"Total de ensaios: {len(self.results)}\n"
                      f"Resultados guardados em CSV.",
                 font=("Arial", 12)).pack(pady=20)
        
        # Botão para novo teste
        ttk.Button(main_frame, text="Novo Teste", 
                  command=self.create_welcome_screen).pack(pady=20)
        
        # Botão para sair
        ttk.Button(main_frame, text="Sair", 
                  command=self.root.quit).pack(pady=10)


def main():
    """Função principal"""
    root = tk.Tk()
    app = VideoQualityTestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

