# projetoseparador

import os
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

try:
    import mysql.connector
except ImportError:
    mysql = None

USUARIO_CADASTRADO = "admin"
SENHA_CADASTRADA = "1234"

# Cores do Design UVR Online
COR_BG_PRINCIPAL = "#0f0f11"
COR_BG_CARD = "#16161a"
COR_BG_DROPZONE = "#121215"
COR_TEXTO = "#ffffff"
COR_TEXTO_MUTED = "#71717a"
COR_VERDE = "#4ade80"
COR_BORDA = "#27272a"

def conectar_banco():
    if mysql is None:
        raise ImportError("mysql-connector-python não está instalado.")
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="separador",
    )

def salvar_status_inicial(arquivo):
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        comando_sql = (
            "INSERT INTO processamentos (nome_musica, caminho, status) VALUES (%s, %s, %s)"
        )
        nome_arquivo = os.path.basename(arquivo)
        cursor.execute(comando_sql, (nome_arquivo, arquivo, "Processando"))
        conexao.commit()
        id_registro = cursor.lastrowid
        cursor.close()
        conexao.close()
        return id_registro
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível gravar no banco de dados: {e}")
        return None

def atualizar_status_final(id_registro, novo_status):
    if id_registro is None:
        return
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        comando_sql = "UPDATE processamentos SET status = %s WHERE id = %s"
        cursor.execute(comando_sql, (novo_status, id_registro))
        conexao.commit()
        cursor.close()
        conexao.close()
    except Exception as e:
        print(f"⚠️ Erro ao atualizar o banco de dados: {e}")

def atualizar_progresso(valor):
    progresso_var.set(valor)
    rotulo_progresso.config(text=f"Progresso: {valor}%")
    janela.update_idletasks()

def separar_audio(caminho_da_musica):
    if not os.path.exists(caminho_da_musica):
        messagebox.showerror("Erro", f"O arquivo '{caminho_da_musica}' não foi encontrado.")
        return

    id_db = salvar_status_inicial(caminho_da_musica)
    
    comando = [
        sys.executable, "-m", "demucs", "-n", "htdemucs", "-j", "4",
        "--mp3", "--two-stems=vocals", caminho_da_musica,
    ]

    try:
        processo = subprocess.Popen(
            comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )

        atualizar_progresso(0)
        percentual_atual = 0
        
        for linha in processo.stdout:
            print(linha, end="")
            if "100%" in linha:
                percentual_atual = 100
            else:
                match = re.search(r"(\d{1,3})%", linha)
                if match:
                    percentual_atual = min(int(match.group(1)), 99)
            atualizar_progresso(percentual_atual)

        retorno = processo.wait()

        if retorno == 0:
            atualizar_progresso(100)
            messagebox.showinfo("Sucesso", "Concluído com sucesso!")
            atualizar_status_final(id_db, "Concluído")
        else:
            messagebox.showerror("Erro", "Ocorreu um erro no processamento do Demucs.")
            atualizar_status_final(id_db, "Erro")

    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao processar: {e}")
        atualizar_status_final(id_db, "Erro")

def processar_arquivo():
    caminho = caminho_var.get().strip().strip('"').strip("'")
    if not caminho or caminho == "Nenhum arquivo selecionado":
        messagebox.showerror("Erro", "Selecione um arquivo primeiro clicando na área acima.")
        return
    
    btn_processar.config(state="disabled", text="⚡ Processando...")
    lbl_selecionar.config(text="Processando arquivo...")
    
    def liberar_botao():
        btn_processar.config(state="normal", text="✨ Começar Processamento")
        lbl_selecionar.config(text="Selecione um arquivo")
        caminho_var.set("Nenhum arquivo selecionado")

    threading.Thread(target=lambda: [separar_audio(caminho), liberar_botao()], daemon=True).start()

def escolher_arquivo():
    caminho = filedialog.askopenfilename(
        title="Selecione o arquivo de áudio",
        filetypes=[("Arquivos de áudio", "*.mp3 *.wav *.m4a *.flac")]
    )
    if caminho:
        caminho_var.set(caminho)
        lbl_selecionar.config(text=f"Selecionado: {os.path.basename(caminho)}")

def verificar_login():
    usuario = entry_usuario.get().strip()
    senha = entry_senha.get().strip()

    if usuario == USUARIO_CADASTRADO and senha == SENHA_CADASTRADA:
        frame_login.pack_forget()
        montar_tela_principal()
    else:
        messagebox.showerror("Login inválido", "Usuário ou senha incorretos.")

def alternar_senha():
    if entry_senha.cget("show") == "*":
        entry_senha.config(show="")
        btn_mostrar_senha.config(text="Ocultar senha")
    else:
        entry_senha.config(show="*")
        btn_mostrar_senha.config(text="Mostrar senha")

def abrir_janela_efeitos():
    caminho_original = caminho_var.get().strip().strip('"').strip("'")
    if not caminho_original or not os.path.exists(caminho_original):
        messagebox.showerror("Erro", "Selecione um arquivo de áudio válido primeiro.")
        return

    janela_efeitos = tk.Toplevel(janela)
    janela_efeitos.title("Alterar Tom ou Tempo")
    janela_efeitos.geometry("400x300")
    janela_efeitos.configure(bg=COR_BG_PRINCIPAL)
    janela_efeitos.resizable(False, False)
    janela_efeitos.transient(janela)
    janela_efeitos.grab_set()

    tk.Label(janela_efeitos, text="Modificar Áudio", font=("Arial", 14, "bold"), bg=COR_BG_PRINCIPAL, fg=COR_TEXTO).pack(pady=10)

    tk.Label(janela_efeitos, text="Velocidade (ex: 1.0 = normal):", bg=COR_BG_PRINCIPAL, fg=COR_TEXTO_MUTED).pack()
    escala_velocidade = tk.Scale(janela_efeitos, from_=0.5, to=2.0, resolution=0.1, orient="horizontal", length=300, bg=COR_BG_PRINCIPAL, fg=COR_TEXTO, highlightthickness=0)
    escala_velocidade.set(1.0)
    escala_velocidade.pack(pady=5)

    tk.Label(janela_efeitos, text="Tom (Semitons):", bg=COR_BG_PRINCIPAL, fg=COR_TEXTO_MUTED).pack()
    escala_tom = tk.Scale(janela_efeitos, from_=-6, to=6, resolution=1, orient="horizontal", length=300, bg=COR_BG_PRINCIPAL, fg=COR_TEXTO, highlightthickness=0)
    escala_tom.set(0)
    escala_tom.pack(pady=5)

    def aplicar_efeitos():
        vel = escala_velocidade.get()
        tom_semitons = escala_tom.get()

        nome_completo = os.path.basename(caminho_original)
        nome, ext = os.path.splitext(nome_completo)
        diretorio_do_codigo = os.path.dirname(os.path.abspath(__file__))
        
        contador = 1
        while True:
            nome_saida = f"{contador}_{nome}_modificado{ext}"
            arquivo_saida = os.path.join(diretorio_do_codigo, nome_saida)
            if not os.path.exists(arquivo_saida):
                break
            contador += 1

        fator_tom = 2 ** (tom_semitons / 12.0)
        sample_rate_alvo = int(44100 * fator_tom)
        velocidade_ajustada = vel / fator_tom

        comando_ffmpeg = [
            "ffmpeg", "-y", "-i", caminho_original,
            "-filter_complex", f"asetrate={sample_rate_alvo},atempo={velocidade_ajustada}",
            arquivo_saida
        ]

        def rodar_ffmpeg():
            try:
                btn_salvar.config(state="disabled", text="Processando...")
                processo = subprocess.run(comando_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if processo.returncode == 0:
                    messagebox.showinfo("Sucesso", f"Salvo como:\n{nome_saida}")
                    janela_efeitos.destroy()
                else:
                    messagebox.showerror("Erro", f"Erro no FFmpeg:\n{processo.stderr}")
                    btn_salvar.config(state="normal", text="Salvar Novo Áudio")
            except FileNotFoundError:
                messagebox.showerror("Erro", "FFmpeg não foi encontrado no sistema.")
                btn_salvar.config(state="normal", text="Salvar Novo Áudio")

        threading.Thread(target=rodar_ffmpeg, daemon=True).start()

    btn_salvar = tk.Button(janela_efeitos, text="Salvar Novo Áudio", width=22, bg=COR_VERDE, fg="#000000", font=("Arial", 10, "bold"), command=aplicar_efeitos, relief="flat")
    btn_salvar.pack(pady=20)

# =====================================================================
# TELA PRINCIPAL REESTILIZADA CONFORME A IMAGEM
# =====================================================================
def montar_tela_principal():
    global lbl_selecionar, progresso_var, rotulo_progresso, btn_processar
    
    janela.geometry("1000x500")
    janela.configure(bg=COR_BG_PRINCIPAL)
    
    container_corpo = tk.Frame(janela, bg=COR_BG_PRINCIPAL)
    container_corpo.pack(fill="both", expand=True, padx=40, pady=40)

    # --- CARD DA ESQUERDA (Área de Upload) ---
    card_esquerdo = tk.Frame(container_corpo, bg=COR_BG_CARD, bd=0, highlightbackground=COR_BORDA, highlightthickness=1)
    card_esquerdo.pack(side="left", fill="both", expand=True, padx=(0, 20))
    
    tk.Label(card_esquerdo, text="Remova os vocais de qualquer música", font=("Arial", 15, "bold"), bg=COR_BG_CARD, fg=COR_TEXTO).pack(anchor="w", padx=25, pady=(25, 2))
    tk.Label(card_esquerdo, text="Ajudaremos você a fazer uma versão HQ karaoke!", font=("Arial", 10), bg=COR_BG_CARD, fg=COR_TEXTO_MUTED).pack(anchor="w", padx=25, pady=(0, 25))
    
    # Dropzone / Área de Clique Central (Prevenção de bugs visuais de fundo nativo)
    btn_dropzone = tk.Button(
        card_esquerdo, bg=COR_BG_DROPZONE, activebackground=COR_BG_DROPZONE, bd=0,
        highlightbackground=COR_BORDA, highlightthickness=1, command=escolher_arquivo, relief="flat"
    )
    btn_dropzone.pack(fill="both", expand=True, padx=25, pady=(0, 15))

    frame_interno_drop = tk.Frame(btn_dropzone, bg=COR_BG_DROPZONE)
    frame_interno_drop.pack(expand=True)
    
    lbl_icone = tk.Label(frame_interno_drop, text="📁↑", font=("Arial", 28), bg=COR_BG_DROPZONE, fg=COR_VERDE)
    lbl_icone.pack(side="left", padx=10)
    
    lbl_selecionar = tk.Label(frame_interno_drop, text="Selecione um arquivo", font=("Arial", 13), bg=COR_BG_DROPZONE, fg=COR_TEXTO)
    lbl_selecionar.pack(side="left", padx=10)

    lbl_icone.bind("<Button-1>", lambda e: escolher_arquivo())
    lbl_selecionar.bind("<Button-1>", lambda e: escolher_arquivo())

    # Efeito Hover premium e fixo para todos os componentes do Dropzone
    COR_HOVER = "#1c1c21"

    def ao_entrar(event):
        btn_dropzone.config(bg=COR_HOVER)
        frame_interno_drop.config(bg=COR_HOVER)
        lbl_icone.config(bg=COR_HOVER)
        lbl_selecionar.config(bg=COR_HOVER)

    def ao_sair(event):
        btn_dropzone.config(bg=COR_BG_DROPZONE)
        frame_interno_drop.config(bg=COR_BG_DROPZONE)
        lbl_icone.config(bg=COR_BG_DROPZONE)
        lbl_selecionar.config(bg=COR_BG_DROPZONE)

    for componente in (btn_dropzone, frame_interno_drop, lbl_icone, lbl_selecionar):
        componente.bind("<Enter>", ao_entrar)
        componente.bind("<Leave>", ao_sair)

    # Botão manual para disparar processamento
    btn_processar = tk.Button(
        card_esquerdo, text="✨ Começar Processamento", bg=COR_VERDE, fg="#000000",
        font=("Arial", 11, "bold"), activebackground="#3cd073", activeforeground="#000000",
        bd=0, relief="flat", command=processar_arquivo, cursor="hand2"
    )
    btn_processar.pack(fill="x", padx=25, pady=(0, 15), ipady=8)

    # Barra de Progresso
    progresso_var = tk.IntVar(value=0)
    style = ttk.Style()
    style.theme_use('default')
    style.configure("Custom.Horizontal.TProgressbar", thickness=4, troughcolor=COR_BG_PRINCIPAL, background=COR_VERDE, bordercolor=COR_BG_PRINCIPAL)
    
    bar_progresso = ttk.Progressbar(card_esquerdo, orient="horizontal", mode="determinate", variable=progresso_var, style="Custom.Horizontal.TProgressbar")
    bar_progresso.pack(fill="x", padx=25, pady=(0, 5))
    
    rotulo_progresso = tk.Label(card_esquerdo, text="", font=("Arial", 8), bg=COR_BG_CARD, fg=COR_TEXTO_MUTED)
    rotulo_progresso.pack(anchor="e", padx=25, pady=(0, 10))

    # --- CARD DA DIREITA (Outros Serviços) ---
    card_direito = tk.Frame(container_corpo, bg=COR_BG_CARD, width=280, bd=0, highlightbackground=COR_BORDA, highlightthickness=1)
    card_direito.pack(side="right", fill="y")
    card_direito.pack_propagate(False)
    
    tk.Label(card_direito, text="Outros Serviços", font=("Arial", 13, "bold"), bg=COR_BG_CARD, fg=COR_TEXTO).pack(anchor="w", padx=20, pady=(25, 15))
    
    btn_servico1 = tk.Button(
        card_direito, text="🎤  Remova Vocais de Uma Música", bg=COR_BG_CARD, fg=COR_TEXTO, 
        activebackground="#1f1f23", activeforeground=COR_TEXTO, bd=0, anchor="w", font=("Arial", 10), cursor="hand2"
    )
    btn_servico1.pack(fill="x", padx=10, pady=4, ipady=6)
    
    btn_servico2 = tk.Button(
        card_direito, text="🎛️  Alterar tom or Tempo", bg=COR_BG_CARD, fg=COR_TEXTO_MUTED, 
        activebackground="#1f1f23", activeforeground=COR_TEXTO, bd=0, anchor="w", font=("Arial", 10), 
        command=abrir_janela_efeitos, cursor="hand2"
    )
    btn_servico2.pack(fill="x", padx=10, pady=4, ipady=6)

# =====================================================================
# TELA DE LOGIN ESTILIZADA
# =====================================================================
janela = tk.Tk()
janela.title("UVR Online - Login")
janela.geometry("400x320")
janela.configure(bg=COR_BG_PRINCIPAL)
janela.resizable(False, False)

caminho_var = tk.StringVar(value="Nenhum arquivo selecionado")

frame_login = tk.Frame(janela, bg=COR_BG_CARD, bd=0, highlightbackground=COR_BORDA, highlightthickness=1)
frame_login.pack(fill="both", expand=True, padx=40, pady=40)

tk.Label(frame_login, text="ENTRAR NA PLATAFORMA", font=("Arial", 12, "bold"), bg=COR_BG_CARD, fg=COR_TEXTO).pack(pady=(20, 15))

tk.Label(frame_login, text="Usuário:", bg=COR_BG_CARD, fg=COR_TEXTO_MUTED).pack(anchor="w", padx=30)
entry_usuario = tk.Entry(frame_login, width=30, bg="#27272a", fg=COR_TEXTO, insertbackground=COR_TEXTO, bd=1, relief="solid")
entry_usuario.pack(pady=(0, 10))

tk.Label(frame_login, text="Senha:", bg=COR_BG_CARD, fg=COR_TEXTO_MUTED).pack(anchor="w", padx=30)
entry_senha = tk.Entry(frame_login, width=30, show="*", bg="#27272a", fg=COR_TEXTO, insertbackground=COR_TEXTO, bd=1, relief="solid")
entry_senha.pack(pady=(0, 5))

btn_mostrar_senha = tk.Button(frame_login, text="Mostrar senha", font=("Arial", 8), bg=COR_BG_CARD, fg=COR_TEXTO_MUTED, bd=0, command=alternar_senha, activebackground=COR_BG_CARD, activeforeground=COR_TEXTO)
btn_mostrar_senha.pack(pady=(0, 15))

tk.Button(frame_login, text="Entrar", width=25, bg=COR_VERDE, fg="#000000", font=("Arial", 10, "bold"), command=verificar_login, relief="flat").pack(pady=5)

janela.mainloop()



    Banco de dados:

    create database separador;
use separador;

create table processamentos (
	id INT AUTO_INCREMENT PRIMARY KEY,
    caminho VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    mensagem TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

alter table  processamentos add nome_musica VARCHAR(255) NOT NULL;

ALTER TABLE processamentos MODIFY COLUMN caminho VARCHAR(500) NULL;

SELECT * FROM processamentos;
