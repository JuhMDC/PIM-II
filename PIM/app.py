# ================================================================
# app.py
# ---------------------------------------------------------------
# Aplicação em Python usando Tkinter para interface gráfica.
# Usa a biblioteca C (userdb.c compilado como .so/.dll)
# para manipular o banco de dados (arquivo users.dat)
# ================================================================

import os
import platform
import ctypes
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

# ---------------------------
# Carregar a biblioteca C
# ---------------------------
# Aqui tentamos abrir a biblioteca compilada em C que faz o
# trabalho de salvar/ler usuários. Dependendo do sistema operacional
# o nome do arquivo muda (.dll no Windows, .so no Linux, .dylib no mac).
lib = None
if platform.system() == "Windows":
    candidates = ["userdb.dll"]
elif platform.system() == "Darwin":
    # no macOS prefira .dylib; alguns .so podem ser Linux e falhar
    candidates = ["libuserdb.dylib", "libuserdb.so"]
else:
    candidates = ["libuserdb.so"]

last_exc = None
for name in candidates:
    path = os.path.abspath(name)
    # se não existe o arquivo, pula para o próximo candidato
    if not os.path.exists(path):
        continue
    try:
        # aqui tentamos carregar a biblioteca C
        lib = ctypes.CDLL(path)
        break
    except OSError as e:
        last_exc = e

if lib is None:
    # se não conseguiu carregar nada, mostramos erro e paramos a execução
    msg = (
        f"Não foi possível carregar a biblioteca nativa. Arquivos tentados: {candidates}."
    )
    if last_exc:
        msg += f" Erro ao carregar: {last_exc}"
    raise OSError(msg)

# ---------------------------------------------------------------
# Dizer para o Python como as funções C devem receber os dados
# ---------------------------------------------------------------
# Essas linhas dizem ao ctypes quais tipos cada função da biblioteca C usa.
lib.adicionar_usuario.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
lib.adicionar_usuario.restype = None

lib.listar_usuarios.argtypes = []
lib.listar_usuarios.restype = None

# ---------------------------------------------------------------
# Paleta de cores e fontes — só para organizar o visual
# ---------------------------------------------------------------
PANEL_BG = "#f3f5f7"        # fundo da janela (cinza claro)
CARD_BG = "#eaf6ff"         # cor do "card" (azul clarinho)
CARD_BORDER = "#d0eaf7"
ACCENT = "#1976D2"          # cor de destaque (azul)
ACCENT_DARK = "#155fa0"
SUCCESS = "#4caf50"         # cor verde para ações de sucesso
TEXT_COLOR = "#0b2540"      # cor do texto

# fontes usadas nos títulos/subtítulos e textos
TITLE_FONT = ("Arial", 18, "bold")
SUBTITLE_FONT = ("Arial", 14, "bold")
BUTTON_FONT = ("Arial", 11, "bold")
TEXT_FONT = ("Arial", 10)

# padrão para entradas (caixas de texto), garante que o fundo seja branco
entry_opts = {'bg': 'white', 'fg': 'black', 'insertbackground': 'black'}

# ---------------------------------------------------------------
# Funções pequenas de interface (botões e desenho)
# ---------------------------------------------------------------

def styled_button(parent, text, command=None, style="accent", width=None, height=None, **kwargs):
    """
    Cria um botão "bonitinho" com cores padronizadas.
    - parent: onde botao vai aparecer
    - text: texto do botão
    - command: função chamada quando clica
    - style: 'accent', 'success' ou 'ghost' (muda a cor)
    - width/height: tamanho aproximado
    """
    # escolhe cor de fundo conforme estilo, texto fica sempre preto (fg="black")
    if style == "accent":
        bg = ACCENT
        active = ACCENT_DARK
    elif style == "success":
        bg = SUCCESS
        active = "#388e3c"
    elif style == "ghost":
        bg = CARD_BG
        active = "#e8eef6"
    else:
        bg = CARD_BG
        active = "#e8eef6"

    btn = tk.Button(parent, text=text, command=command, bg=bg, fg="black",
                    activebackground=active, activeforeground="black",
                    relief="flat", font=BUTTON_FONT, bd=0, **kwargs)
    if width:
        btn.config(width=width)
    if height:
        btn.config(height=height)
    return btn

def _rounded_rect(canvas, x1, y1, x2, y2, r=18, **kwargs):
    """
    Função utilitária (não usada diretamente no resto): desenha um
    retângulo com cantos arredondados no canvas.
    """
    ids = []
    ids.append(canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs))
    ids.append(canvas.create_rectangle(x1, y1 + r, x2, y2 - r, **kwargs))
    ids.append(canvas.create_arc(x2 - 2*r, y1, x2, y1 + 2*r, start=0, extent=90, style='pieslice', **kwargs))
    ids.append(canvas.create_arc(x1, y1, x1 + 2*r, y1 + 2*r, start=90, extent=90, style='pieslice', **kwargs))
    ids.append(canvas.create_arc(x1, y2 - 2*r, x1 + 2*r, y2, start=180, extent=90, style='pieslice', **kwargs))
    ids.append(canvas.create_arc(x2 - 2*r, y2 - 2*r, x2, y2, start=270, extent=90, style='pieslice', **kwargs))
    return ids

def create_center_card(parent, card_width=520, card_height=360, radius=18, padding=12):
    """
    Cria um 'card' central dentro do parent.
    - O card é desenhado num Canvas e tem um inner_frame onde colocamos widgets.
    - Quando a janela muda de tamanho, apenas atualizamos as posições; não
      recriamos o inner_frame para não perder os widgets.
    """
    wrapper = tk.Frame(parent, bg=PANEL_BG)
    wrapper.pack(expand=True, fill="both")

    canvas = tk.Canvas(wrapper, bg=PANEL_BG, highlightthickness=0)
    canvas.pack(expand=True, fill="both", padx=20, pady=20)

    # frame interno onde adicionamos labels, entrys, botoes, etc.
    inner_frame = tk.Frame(canvas, bg=CARD_BG)

    # guardamos os ids das formas desenhadas para atualizarmos as coords depois
    shapes = {
        "shadow": None,
        "rect_center": None,
        "rect_middle": None,
        "arc_tl": None,
        "arc_tr": None,
        "arc_bl": None,
        "arc_br": None,
        "window": None
    }

    def draw():
        # pega o tamanho atual do canvas e calcula onde desenhar o card
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w <= 0 or h <= 0:
            return

        cx = w // 2
        cy = h // 2
        x1 = cx - card_width // 2
        y1 = cy - card_height // 2
        x2 = cx + card_width // 2
        y2 = cy + card_height // 2

        shadow_offset = 6

        # cria ou atualiza sombra do card
        if shapes["shadow"] is None:
            shapes["shadow"] = canvas.create_rectangle(
                x1 + shadow_offset, y1 + shadow_offset,
                x2 + shadow_offset, y2 + shadow_offset,
                fill="#dfe7ec", outline="", tags="card"
            )
        else:
            canvas.coords(shapes["shadow"],
                          x1 + shadow_offset, y1 + shadow_offset,
                          x2 + shadow_offset, y2 + shadow_offset)

        # cria retângulos/arcos do card na primeira vez, depois só atualiza coords
        if shapes["rect_center"] is None:
            shapes["rect_center"] = canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=CARD_BG, outline=CARD_BORDER, width=1, tags="card")
            shapes["rect_middle"] = canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=CARD_BG, outline=CARD_BORDER, width=1, tags="card")
            shapes["arc_tr"] = canvas.create_arc(x2 - 2*radius, y1, x2, y1 + 2*radius, start=0, extent=90, style='pieslice', fill=CARD_BG, outline=CARD_BORDER, width=1, tags="card")
            shapes["arc_tl"] = canvas.create_arc(x1, y1, x1 + 2*radius, y1 + 2*radius, start=90, extent=90, style='pieslice', fill=CARD_BG, outline=CARD_BORDER, width=1, tags="card")
            shapes["arc_bl"] = canvas.create_arc(x1, y2 - 2*radius, x1 + 2*radius, y2, start=180, extent=90, style='pieslice', fill=CARD_BG, outline=CARD_BORDER, width=1, tags="card")
            shapes["arc_br"] = canvas.create_arc(x2 - 2*radius, y2 - 2*radius, x2, y2, start=270, extent=90, style='pieslice', fill=CARD_BG, outline=CARD_BORDER, width=1, tags="card")
        else:
            canvas.coords(shapes["rect_center"], x1 + radius, y1, x2 - radius, y2)
            canvas.coords(shapes["rect_middle"], x1, y1 + radius, x2, y2 - radius)
            canvas.coords(shapes["arc_tr"], x2 - 2*radius, y1, x2, y1 + 2*radius)
            canvas.coords(shapes["arc_tl"], x1, y1, x1 + 2*radius, y1 + 2*radius)
            canvas.coords(shapes["arc_bl"], x1, y2 - 2*radius, x1 + 2*radius, y2)
            canvas.coords(shapes["arc_br"], x2 - 2*radius, y2 - 2*radius, x2, y2)

        # calcula área interna (onde vai o inner_frame)
        inner_x1 = x1 + padding
        inner_y1 = y1 + padding
        inner_x2 = x2 - padding
        inner_y2 = y2 - padding
        win_w = inner_x2 - inner_x1
        win_h = inner_y2 - inner_y1

        # cria ou atualiza a janela que contém o inner_frame
        if shapes["window"] is None:
            shapes["window"] = canvas.create_window((cx, cy), window=inner_frame, width=win_w, height=win_h, tags="card")
        else:
            canvas.coords(shapes["window"], cx, cy)
            canvas.itemconfig(shapes["window"], width=win_w, height=win_h)

    # liga o redesenho ao redimensionamento do canvas
    canvas.bind("<Configure>", lambda e: draw())
    wrapper.after(10, draw)

    # devolve wrapper, canvas e inner_frame para que a gente adicione widgets no inner_frame
    return wrapper, canvas, inner_frame

# ---------------------------------------------------------------
# Variável global que guarda qual usuário está logado (se houver)
# ---------------------------------------------------------------
usuario_logado = None

# ---------------------------------------------------------------
# Funções de lógica (login, listar, inscrever etc.)
# ---------------------------------------------------------------

def validar_login(primeiro_nome, senha):
    """
    Lê o arquivo users.dat (binário) e compara o primeiro nome + senha.
    Retorna True se encontrou usuário, False caso contrário.
    """
    global usuario_logado
    # usuário administrador hardcoded (só para teste)
    if primeiro_nome == "ADM" and senha == "12345Abc@":
        usuario_logado = "ADM"
        return True
    if not os.path.exists('users.dat'):
        print("Arquivo users.dat não encontrado")
        return False

    # abre o arquivo binário e lê registros de tamanho fixo
    FILE = open('users.dat', 'rb')
    TAMANHO_REGISTRO = 154  # 50 bytes nome + 50 bytes senha + 50 bytes email + 4 bytes idade

    while True:
        registro = FILE.read(TAMANHO_REGISTRO)
        if not registro:
            break
        
        # lê campo nome e senha
        nome = registro[:50].decode('utf-8').rstrip('\x00')
        senha_salva = registro[50:100].decode('utf-8').rstrip('\x00')
        
        # pega somente o primeiro nome
        nome_limpo = nome.strip()
        if not nome_limpo:
            continue
        partes_nome = nome_limpo.split()
        if not partes_nome:
            continue
        primeiro = partes_nome[0]
        
        # compara ignorando caixa alta/baixa
        if primeiro.lower() == primeiro_nome.lower() and senha_salva == senha:
            usuario_logado = primeiro_nome
            FILE.close()
            return True
    
    FILE.close()
    return False

def listar_usuarios():
    """
    Chama a função C que imprime lista de usuários (printf).
    Capturamos a saída e mostramos numa janela com scrolledtext.
    """
    import io, sys
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    lib.listar_usuarios()

    sys.stdout = old_stdout
    conteudo = buffer.getvalue()

    janela_lista = tk.Toplevel(root)
    janela_lista.title("Usuários Cadastrados")
    texto = scrolledtext.ScrolledText(janela_lista, width=70, height=20, bg='white', fg='black', font=TEXT_FONT)
    texto.pack(padx=10, pady=10)
    texto.insert(tk.END, conteudo)
    texto.configure(state='disabled')

def inscrever_curso(nome_curso, usuario):
    """
    Registra inscrição no arquivo inscricoes.dat.
    Verifica se usuário já está inscrito em outro curso.
    """
    global usuario_logado
    if not usuario_logado:
        messagebox.showwarning("Inscrição", "Você precisa estar logado para se inscrever em um curso!")
        return

    try:
        # verifica se já tem inscrição para esse usuário
        if os.path.exists('inscricoes.dat'):
            with open('inscricoes.dat', 'r', encoding='utf-8') as f:
                for linha in f:
                    partes = linha.strip().split('|')
                    if len(partes) == 2 and partes[0].lower() == usuario.lower():
                        messagebox.showinfo("Inscrição", f"Você já está inscrito no curso '{partes[1]}'. Você não pode se inscrever em mais de um curso.")
                        return

        # registra a inscrição
        with open('inscricoes.dat', 'a', encoding='utf-8') as f:
            f.write(f"{usuario}|{nome_curso}\n")
        messagebox.showinfo("Inscrição", f"Você foi inscrito no curso '{nome_curso}' com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro de Inscrição", f"Não foi possível inscrever-se no curso '{nome_curso}'. Erro: {e}")

# ---------------------------------------------------------------
# Interface principal (Tkinter windows)
# ---------------------------------------------------------------
root = tk.Tk()
root.title("Sistema Acadêmico - Login/Cadastro de Usuários")
root.geometry("980x680")  # define tamanho inicial da janela
root.configure(bg=PANEL_BG)

# frame que segura a área central (a gente limpa ele sempre que troca de tela)
center_holder = tk.Frame(root, bg=PANEL_BG)
center_holder.pack(expand=True, fill="both")

def clear_center():
    """
    Remove tudo que está dentro do frame central.
    Usamos quando mudamos de tela para não acumular widgets.
    """
    for w in center_holder.winfo_children():
        w.destroy()

# ---------------------------------------------------------------
# Telas (cada func monta widgets no inner_frame retornado pelo card)
# ---------------------------------------------------------------

def mostrar_tela_login():
    """
    Tela de login: coloca campos para usuário e senha.
    Os campos são colocados dentro do inner_frame do card.
    """
    clear_center()
    wrapper, canvas, inner = create_center_card(center_holder, card_width=500, card_height=340)
    wrapper.update_idletasks()

    # Título pequeno
    tk.Label(inner, text="Login", font=SUBTITLE_FONT, bg=CARD_BG, fg=ACCENT).pack(pady=(6,4))

    # Campo usuário: colocamos dentro de um frame para alinhar com o campo senha
    tk.Label(inner, text="Usuário (primeiro nome):", bg=CARD_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=6)
    usuario_frame = tk.Frame(inner, bg=CARD_BG)
    usuario_frame.pack(fill="x", padx=6, pady=(0,6))
    entry_usuario = tk.Entry(usuario_frame, width=25, **entry_opts)   # largura igual ao campo senha
    entry_usuario.pack(side='left', pady=4)

    # Campo senha com botão olho ao lado
    tk.Label(inner, text="Senha:", bg=CARD_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=6)
    senha_frame = tk.Frame(inner, bg=CARD_BG)
    senha_frame.pack(fill="x", padx=6)
    entry_senha = tk.Entry(senha_frame, width=25, show='*', **entry_opts)
    entry_senha.pack(side='left', pady=4)
    def toggle_pw():
        # mostra/oculta senha quando clicar no botão
        if entry_senha.cget('show') == '*':
            entry_senha.config(show='')
            btn_eye.config(text='🙈')
        else:
            entry_senha.config(show='*')
            btn_eye.config(text='👁️')
    btn_eye = tk.Button(senha_frame, text='👁️', command=toggle_pw, bg=CARD_BG, fg='black', bd=0)
    btn_eye.pack(side='left', padx=6)

    # botoes de cadastrar e logar
    btns = tk.Frame(inner, bg=CARD_BG)
    btns.pack(pady=(12,6))
    styled_button(btns, "Cadastrar-se", command=mostrar_tela_cadastro, style="ghost").pack(side='left', padx=8)
    styled_button(btns, "Logar", command=lambda: (validar_login(entry_usuario.get().strip(), entry_senha.get().strip()) and (messagebox.showinfo("Bem-vindo!", "Login realizado com sucesso!"), mostrar_tela_menu_principal()) or None), style="accent", width=12).pack(side='left', padx=8)

def mostrar_tela_menu_principal():
    """
    Tela principal mostrada depois do login.
    Contém botões para navegar para as outras telas.
    """
    clear_center()
    wrapper, canvas, inner = create_center_card(center_holder, card_width=700, card_height=420)
    wrapper.update_idletasks()

    # topo com título e info do usuário
    top = tk.Frame(inner, bg=CARD_BG)
    top.pack(fill="x")
    tk.Label(top, text="Sistema Acadêmico", font=TITLE_FONT, bg=CARD_BG, fg=ACCENT).pack(side="left", anchor="w")
    user_frame = tk.Frame(top, bg=CARD_BG)
    user_frame.pack(side="right", anchor="e")
    tk.Label(user_frame, text=f"Usuário: {usuario_logado}", bg=CARD_BG, fg=TEXT_COLOR, font=("Arial", 10, "bold")).pack(side='left', padx=(0,10))
    styled_button(user_frame, "Sair", command=lambda: (globals().update({'usuario_logado': None}), mostrar_tela_login()), style="ghost").pack(side='left')

    tk.Label(inner, text="Menu Principal", font=SUBTITLE_FONT, bg=CARD_BG, fg=TEXT_COLOR).pack(pady=(12,6))

    # botões principais
    botoes_frame = tk.Frame(inner, bg=CARD_BG)
    botoes_frame.pack(pady=14)
    styled_button(botoes_frame, "Área do Aluno", command=mostrar_area_aluno, style="accent", width=18, height=2).pack(side='left', padx=14)
    styled_button(botoes_frame, "Cursos", command=mostrar_cursos, style="accent", width=18, height=2).pack(side='left', padx=14)
    if usuario_logado == "ADM":
        styled_button(botoes_frame, "Secretaria", command=mostrar_submenu_secretaria, style="accent", width=18, height=2).pack(side='left', padx=14)

def set_logout():
    """
    Função simples que remove usuário logado.
    """
    global usuario_logado
    usuario_logado = None

def mostrar_area_aluno():
    """
    Mostra a área do aluno com notas e faltas.
    """
    clear_center()
    wrapper, canvas, inner = create_center_card(center_holder, card_width=700, card_height=460)
    wrapper.update_idletasks()

    tk.Label(inner, text="Área do Aluno", font=SUBTITLE_FONT, bg=CARD_BG, fg=TEXT_COLOR).pack(pady=(8,6))
    curso_inscrito = "Nenhum curso inscrito."
    global usuario_logado
    if usuario_logado and os.path.exists('inscricoes.dat'):
        try:
            with open('inscricoes.dat', 'r', encoding='utf-8') as f:
                for linha in f:
                    partes = linha.strip().split('|')
                    if len(partes) == 2 and partes[0].lower() == usuario_logado.lower():
                        curso_inscrito = f"Curso Inscrito: {partes[1]}"
                        break
        except Exception as e:
            curso_inscrito = f"Erro ao ler inscrições: {e}"
    tk.Label(inner, text=curso_inscrito, font=("Arial", 12, "italic"), bg=CARD_BG, fg=TEXT_COLOR).pack(pady=(4,8))

    # área de texto para notas/faltas
    notas_text = scrolledtext.ScrolledText(inner, width=70, height=12, state='normal', bg='white', fg='black', font=TEXT_FONT)
    notas_text.pack(padx=6, pady=6)
    notas_text.insert(tk.END, "Clique no botão 'Notas' para exibir suas notas.\nClique no botão 'Faltas' para exibir suas faltas.\n")

    def mostrar_notas_na_tela():
        # limpa e escreve notas do usuário (lidas de notas.dat)
        notas_text.configure(state='normal')
        notas_text.delete('1.0', tk.END)
        notas_do_usuario = {}
        if os.path.exists('notas.dat') and usuario_logado:
            try:
                with open('notas.dat', 'r', encoding='utf-8') as f:
                    for linha in f:
                        partes = linha.strip().split('|')
                        if len(partes) == 4:
                            usuario, materia, tipo, nota = partes
                            if usuario.lower() == usuario_logado.lower():
                                if materia not in notas_do_usuario:
                                    notas_do_usuario[materia] = {}
                                notas_do_usuario[materia][tipo] = nota
                if notas_do_usuario:
                    notas_text.insert(tk.END, "Notas cadastradas por matéria:\n")
                    for materia, notas in notas_do_usuario.items():
                        notas_text.insert(tk.END, f"\nMatéria: {materia}\n")
                        np1 = float(notas.get('NP1', 0)) if 'NP1' in notas else None
                        np2 = float(notas.get('NP2', 0)) if 'NP2' in notas else None
                        pim = float(notas.get('PIM', 0)) if 'PIM' in notas else None
                        for tipo in ['NP1', 'NP2', 'PIM']:
                            if tipo in notas:
                                notas_text.insert(tk.END, f"  {tipo}: {notas[tipo]}\n")
                        if np1 is not None and np2 is not None and pim is not None:
                            media = ((np1*4)+(np2*4)+(pim*2))/10
                            notas_text.insert(tk.END, f"  Média: {media:.2f}\n")
                        else:
                            notas_text.insert(tk.END, "  Média: - (faltam notas)\n")
                else:
                    notas_text.insert(tk.END, "Nenhuma nota cadastrada para você.\n")
            except Exception as e:
                notas_text.insert(tk.END, f"Erro ao ler notas: {e}\n")
        else:
            notas_text.insert(tk.END, "Nenhuma nota cadastrada para você.\n")
        notas_text.configure(state='disabled')

    def mostrar_faltas_na_tela():
        # limpa e escreve faltas do usuário (lidas de faltas.dat)
        notas_text.configure(state='normal')
        notas_text.delete('1.0', tk.END)
        faltas_do_usuario = {}
        totais_por_materia = {}
        if os.path.exists('faltas.dat') and usuario_logado:
            try:
                with open('faltas.dat', 'r', encoding='utf-8') as f:
                    for linha in f:
                        partes = linha.strip().split('|')
                        if len(partes) == 4:
                            usuario, materia, mes, faltas = partes
                            if usuario.lower() == usuario_logado.lower():
                                if materia not in faltas_do_usuario:
                                    faltas_do_usuario[materia] = {}
                                faltas_do_usuario[materia][mes] = faltas
                                try:
                                    totais_por_materia[materia] = totais_por_materia.get(materia, 0) + int(faltas)
                                except ValueError:
                                    pass
                if faltas_do_usuario:
                    notas_text.insert(tk.END, "Total de faltas por matéria:\n")
                    for materia, total in totais_por_materia.items():
                        notas_text.insert(tk.END, f"- {materia}: {total}\n")
                    notas_text.insert(tk.END, "\nFaltas cadastradas por matéria:\n")
                    for materia, meses in faltas_do_usuario.items():
                        notas_text.insert(tk.END, f"\nMatéria: {materia}\n")
                        for mes, faltas in meses.items():
                            notas_text.insert(tk.END, f"  Mês: {mes} - Faltas: {faltas}\n")
                else:
                    notas_text.insert(tk.END, "Nenhuma falta cadastrada para você.\n")
            except Exception as e:
                notas_text.insert(tk.END, f"Erro ao ler faltas: {e}\n")
        else:
            notas_text.insert(tk.END, "Nenhuma falta cadastrada para você.\n")
        notas_text.configure(state='disabled')

    # botões notas, faltas e voltar
    botoes = tk.Frame(inner, bg=CARD_BG)
    botoes.pack(pady=(8,6))
    styled_button(botoes, "Notas", command=mostrar_notas_na_tela, style="accent", width=14).pack(side='left', padx=8)
    styled_button(botoes, "Faltas", command=mostrar_faltas_na_tela, style="accent", width=14).pack(side='left', padx=8)
    styled_button(inner, "Voltar", command=mostrar_tela_menu_principal, style="ghost").pack(pady=10)

def mostrar_submenu_secretaria():
    """
    Tela da secretaria, com botões para tarefas administrativas.
    """
    clear_center()
    wrapper, canvas, inner = create_center_card(center_holder, card_width=600, card_height=380)
    wrapper.update_idletasks()

    tk.Label(inner, text="Secretaria", font=SUBTITLE_FONT, bg=CARD_BG, fg=TEXT_COLOR).pack(pady=(6,8))
    botoes = tk.Frame(inner, bg=CARD_BG)
    botoes.pack(pady=8)
    if usuario_logado == "ADM":
        styled_button(botoes, "Cadastrar Curso", command=lambda: mostrar_tela_cadastro_curso(), style="accent", width=18).pack(pady=6)
        styled_button(botoes, "Lançar Notas", command=lambda: mostrar_tela_lancar_notas(), style="accent", width=18).pack(pady=6)
        styled_button(botoes, "Lançar Faltas", command=lambda: mostrar_tela_lancar_faltas(), style="accent", width=18).pack(pady=6)

    # bottom_frame para manter o botão sempre abaixo e centralizado
    bottom_frame = tk.Frame(inner, bg=CARD_BG)
    bottom_frame.pack(fill="x", pady=(8,12))
    # usei padding vertical grande antes (pady=85) no original; aqui colocamos um padding razoável
    btn_voltar = styled_button(bottom_frame, "Voltar ao Menu Principal", command=mostrar_tela_menu_principal, style="ghost", width=28)
    btn_voltar.pack(pady=8, anchor='center')

def mostrar_tela_cadastro():
    """
    Tela de cadastro de usuário. Aqui o usuário insere nome, senha, email, idade.
    NOTE: certifica-se de usar um único bloco de botões no final (para não duplicar).
    """
    clear_center()
    wrapper, canvas, inner = create_center_card(center_holder, card_width=520, card_height=460)
    wrapper.update_idletasks()

    tk.Label(inner, text="Cadastro de Usuário", font=SUBTITLE_FONT, bg=CARD_BG, fg=TEXT_COLOR).pack(pady=(6,8))

    # Nome
    tk.Label(inner, text="Nome:", bg=CARD_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=6)
    nome_frame = tk.Frame(inner, bg=CARD_BG)
    nome_frame.pack(fill="x", padx=6, pady=(0,6))
    entry_nome = tk.Entry(nome_frame, width=36, fg='grey', bg='white', insertbackground='black')
    entry_nome.pack(side='left', pady=4)
    entry_nome.insert(0, "Nome completo (O primeiro nome será seu Usuário)")
    def on_entry_nome_focus_in(event):
        # placeholder: quando o campo fica em foco, remove o texto sugestivo
        if entry_nome.get() == "Nome completo (O primeiro nome será seu Usuário)":
            entry_nome.delete(0, tk.END)
            entry_nome.config(fg='black')
    def on_entry_nome_focus_out(event):
        # se o usuário deixou vazio, recoloca o texto sugestivo
        if not entry_nome.get():
            entry_nome.insert(0, "Nome completo (O primeiro nome será seu Usuário)")
            entry_nome.config(fg='grey')
    entry_nome.bind('<FocusIn>', on_entry_nome_focus_in)
    entry_nome.bind('<FocusOut>', on_entry_nome_focus_out)

    # Senha
    tk.Label(inner, text="Senha:", bg=CARD_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=6)
    senha_frame = tk.Frame(inner, bg=CARD_BG)
    senha_frame.pack(fill="x", padx=6)
    entry_senha = tk.Entry(senha_frame, width=36, show='*', **entry_opts)
    entry_senha.pack(side='left', pady=4)
    btn_eye = tk.Button(senha_frame, text='👁️', command=lambda: entry_senha.config(show='' if entry_senha.cget('show') == '*' else '*'), bg=CARD_BG, fg='black', bd=0)
    btn_eye.pack(side='left', padx=6)

    # Regras (apenas um lembrete visual)
    regras_frame = tk.Frame(inner, bg=CARD_BG)
    regras_frame.pack(anchor='w', padx=6, pady=(4,4))
    label_regra_min = tk.Label(regras_frame, text="- Mínimo 8 dígitos", fg="grey", bg=CARD_BG, font=("Arial", 9))
    label_regra_mai = tk.Label(regras_frame, text="- Letra maiúscula", fg="grey", bg=CARD_BG, font=("Arial", 9))
    label_regra_minusc = tk.Label(regras_frame, text="- Letra minúscula", fg="grey", bg=CARD_BG, font=("Arial", 9))
    label_regra_esp = tk.Label(regras_frame, text="- Caractere especial", fg="grey", bg=CARD_BG, font=("Arial", 9))
    label_regra_min.pack(anchor='w')
    label_regra_mai.pack(anchor='w')
    label_regra_minusc.pack(anchor='w')
    label_regra_esp.pack(anchor='w')

    # Email
    tk.Label(inner, text="Email:", bg=CARD_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=6, pady=(6,0))
    email_frame = tk.Frame(inner, bg=CARD_BG)
    email_frame.pack(fill="x", padx=6, pady=(0,6))
    entry_email = tk.Entry(email_frame, width=36, **entry_opts)
    entry_email.pack(side='left', pady=4)

    # Idade
    tk.Label(inner, text="Idade:", bg=CARD_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=6)
    idade_frame = tk.Frame(inner, bg=CARD_BG)
    idade_frame.pack(fill="x", padx=6, pady=(0,6))
    entry_idade = tk.Entry(idade_frame, width=36, **entry_opts)
    entry_idade.pack(side='left', pady=4)

    # função que atualiza as cores das regras conforme o usuário digita a senha
    def atualizar_regras(event=None):
        senha = entry_senha.get()
        label_regra_min.config(fg='red' if len(senha) < 8 else 'green')
        label_regra_mai.config(fg='red' if not any(c.isupper() for c in senha) else 'green')
        label_regra_minusc.config(fg='red' if not any(c.islower() for c in senha) else 'green')
        label_regra_esp.config(fg='red' if not any(not c.isalnum() for c in senha) else 'green')
    entry_senha.bind('<KeyRelease>', atualizar_regras)

    # função que grava o usuário usando a biblioteca C
    def cadastrar_usuario_tela():
        nome = entry_nome.get().strip().encode('utf-8')
        senha_str = entry_senha.get()
        senha = senha_str.strip().encode('utf-8')
        email = entry_email.get().strip().encode('utf-8')
        try:
            idade = int(entry_idade.get())
        except ValueError:
            messagebox.showerror("Erro", "Idade inválida!")
            return
        erros = []
        if len(senha_str) < 8:
            erros.append("mínimo 8 dígitos")
        if not any(c.isupper() for c in senha_str):
            erros.append("letra maiúscula")
        if not any(c.islower() for c in senha_str):
            erros.append("letra minúscula")
        if not any(not c.isalnum() for c in senha_str):
            erros.append("caractere especial")
        atualizar_regras()
        if erros:
            messagebox.showwarning(
                "Senha inválida",
                "A senha deve conter: " + ", ".join(erros)
            )
            return
        if not nome or not senha or not email:
            messagebox.showwarning("Aviso", "Preencha todos os campos!")
            return
        # chama a função C para adicionar usuário
        lib.adicionar_usuario(nome, senha, email, idade)
        messagebox.showinfo("Sucesso", "Usuário cadastrado com sucesso!")
        mostrar_tela_login()

    # bottom_frame único para os botões (assim não duplica)
    bottom_frame = tk.Frame(inner, bg=CARD_BG)
    bottom_frame.pack(fill="x", pady=(8,6))
    btn_group = tk.Frame(bottom_frame, bg=CARD_BG)
    btn_group.pack()
    styled_button(btn_group, "Voltar", command=mostrar_tela_login, style="ghost", width=14).pack(side='left', padx=8)
    styled_button(btn_group, "Cadastrar-se", command=cadastrar_usuario_tela, style="accent", width=14).pack(side='left', padx=8)

def mostrar_tela_cadastro_curso():
    """
    Tela para cadastrar um curso (nome + descrição).
    """
    clear_center()
    wrapper, canvas, inner = create_center_card(center_holder, card_width=600, card_height=380)
    wrapper.update_idletasks()

    tk.Label(inner, text="Cadastro de Curso", font=SUBTITLE_FONT, bg=CARD_BG, fg=TEXT_COLOR).pack(pady=(6,8))
    tk.Label(inner, text="Nome do Curso:", bg=CARD_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=6)
    entry_nome = tk.Entry(inner, width=46, **entry_opts)
    entry_nome.pack(padx=6, pady=(0,6))
    tk.Label(inner, text="Descrição:", bg=CARD_BG, fg=TEXT_COLOR, anchor="w").pack(fill="x", padx=6, pady=(6,0))
    entry_desc = tk.Text(inner, width=46, height=4, bg='white', fg='black', insertbackground='black')
    entry_desc.pack(padx=6, pady=(0,6))

    def cadastrar_curso():
        nome = entry_nome.get().strip()
        descricao = entry_desc.get("1.0", tk.END).strip()
        if not nome or not descricao:
            messagebox.showwarning("Aviso", "Preencha todos os campos!")
            return
        try:
            with open('cursos.dat', 'a', encoding='utf-8') as f:
                f.write(f"{nome}|{descricao}\n")
            messagebox.showinfo("Sucesso", f"Curso '{nome}' cadastrado com sucesso!")
            mostrar_submenu_secretaria()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar curso: {e}")

    botoes = tk.Frame(inner, bg=CARD_BG)
    botoes.pack(pady=8)
    styled_button(botoes, "Voltar", command=mostrar_submenu_secretaria, style="ghost").pack(side='left', padx=8)
    styled_button(botoes, "Cadastrar", command=cadastrar_curso, style="accent").pack(side='left', padx=8)

def mostrar_cursos():
    """
    Tela que mostra todos os cursos cadastrados.
    Cada curso vira um "mini-card" com descrição que se ajusta ao tamanho
    do canvas (wraplength recalculado no resize).
    O botão 'Voltar ao Menu Principal' fica no rodapé do card.
    """
    clear_center()
    card_w = 760
    wrapper, canvas, inner = create_center_card(center_holder, card_width=card_w, card_height=520)
    wrapper.update_idletasks()

    tk.Label(inner, text="Cursos Disponíveis", font=SUBTITLE_FONT, bg=CARD_BG, fg=TEXT_COLOR).pack(pady=(6,8))

    # Container principal (conteudo rolável) — separa do bottom_frame
    content_frame = tk.Frame(inner, bg=CARD_BG)
    content_frame.pack(fill="both", expand=True, padx=6, pady=6)

    # canvas interno e scrollbar
    list_canvas = tk.Canvas(content_frame, bg=CARD_BG, highlightthickness=0)
    list_canvas.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=list_canvas.yview)
    scrollbar.pack(side="right", fill="y")
    list_canvas.configure(yscrollcommand=scrollbar.set)

    inner_list = tk.Frame(list_canvas, bg=CARD_BG)
    list_window = list_canvas.create_window((0,0), window=inner_list, anchor="nw")

    # garante que o scrollregion acompanhe a lista interna
    inner_list.bind("<Configure>", lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all")))

    # guardamos as labels de descrição para atualizar o wrap quando redimensionar
    desc_labels = []

    def on_canvas_config(e):
        # ajusta a largura da janela interna e o wrap das descrições
        list_canvas.itemconfig(list_window, width=e.width)
        wrap_base = max(180, e.width - 220)
        for lbl in desc_labels:
            lbl.config(wraplength=wrap_base)
    list_canvas.bind("<Configure>", on_canvas_config)

    try:
        if not os.path.exists('cursos.dat'):
            tk.Label(inner_list, text="Nenhum curso cadastrado ainda.", bg=CARD_BG, fg=TEXT_COLOR, font=TEXT_FONT).pack(pady=20)
        else:
            with open('cursos.dat', 'r', encoding='utf-8') as f:
                linhas = f.readlines()
                if not linhas:
                    tk.Label(inner_list, text="Nenhum curso cadastrado ainda.", bg=CARD_BG, fg=TEXT_COLOR, font=TEXT_FONT).pack(pady=20)
                else:
                    for idx, linha in enumerate(linhas, 1):
                        partes = linha.strip().split('|')
                        if len(partes) == 2:
                            nome_curso, desc = partes
                            # "mini-card"
                            curso_fr = tk.Frame(inner_list, bg="#dff8ff", bd=1, relief="solid", padx=14, pady=10)
                            curso_fr.pack(fill="x", pady=8, padx=6)
                            tk.Label(curso_fr, text=f"{idx}. {nome_curso}", font=("Arial", 12, "bold"), bg="#dff8ff", fg=ACCENT).pack(fill="x", pady=(0,6))
                            desc_label = tk.Label(curso_fr, text=f"{desc}", bg="#dff8ff", fg=TEXT_COLOR,
                                                  wraplength=400, justify="left", anchor="w", font=TEXT_FONT)
                            desc_label.pack(fill="x", pady=(0,8))
                            desc_labels.append(desc_label)
                            btn_container = tk.Frame(curso_fr, bg="#dff8ff")
                            btn_container.pack(fill="x")
                            styled_button(btn_container, "Inscrever-se", command=lambda nc=nome_curso: inscrever_curso(nc, usuario_logado), style="success").pack(side="right")
                        else:
                            tk.Label(inner_list, text=f"{idx}. {linha.strip()}", bg=CARD_BG, fg=TEXT_COLOR).pack(fill="x", pady=2)
    except Exception as e:
        tk.Label(inner, text=f"Erro ao ler cursos: {e}", bg=CARD_BG, fg='red').pack(pady=10)

    # Bottom frame: botão voltar centralizado e único
    bottom_frame = tk.Frame(inner, bg=CARD_BG)
    bottom_frame.pack(fill="x", pady=(8,12))
    styled_button(bottom_frame, "Voltar ao Menu Principal", command=mostrar_tela_menu_principal, style="ghost", width=28).pack(pady=6)

def mostrar_tela_lancar_notas():
    """
    Tela para escolher tipo de nota (NP1, NP2, PIM) e abrir formulários.
    """
    clear_center()
    wrapper, canvas, inner = create_center_card(center_holder, card_width=620, card_height=420)
    wrapper.update_idletasks()

    tk.Label(inner, text="Lançar Nota", font=SUBTITLE_FONT, bg=CARD_BG, fg=TEXT_COLOR).pack(pady=(6,8))
    botoes_frame = tk.Frame(inner, bg=CARD_BG)
    botoes_frame.pack(pady=10)

    def abrir_formulario(tipo):
        # abre uma nova tela dentro do mesmo fluxo, para lançar nota
        clear_center()
        wrapper2, canvas2, inner2 = create_center_card(center_holder, card_width=520, card_height=380)
        wrapper2.update_idletasks()

        tk.Label(inner2, text=f"Lançar Nota - {tipo}", font=SUBTITLE_FONT, bg=CARD_BG, fg=TEXT_COLOR).pack(pady=(6,8))
        tk.Label(inner2, text="Usuário (primeiro nome):", bg=CARD_BG, fg=TEXT_COLOR).pack(fill="x", padx=6)
        entry_usuario = tk.Entry(inner2, width=36, **entry_opts)
        entry_usuario.pack(padx=6, pady=(0,6))
        if tipo != 'PIM':
            tk.Label(inner2, text="Matéria:", bg=CARD_BG, fg=TEXT_COLOR).pack(fill="x", padx=6)
            entry_materia = tk.Entry(inner2, width=36, **entry_opts)
            entry_materia.pack(padx=6, pady=(0,6))
        tk.Label(inner2, text="Nota:", bg=CARD_BG, fg=TEXT_COLOR).pack(fill="x", padx=6)
        entry_nota = tk.Entry(inner2, width=12, **entry_opts)
        entry_nota.pack(padx=6, pady=(0,6))

        def salvar_nota():
            usuario = entry_usuario.get().strip()
            nota = entry_nota.get().strip()
            if tipo != 'PIM':
                materia = entry_materia.get().strip()
                if not usuario or not materia or not nota:
                    messagebox.showwarning("Aviso", "Preencha todos os campos!")
                    return
            else:
                if not usuario or not nota:
                    messagebox.showwarning("Aviso", "Preencha todos os campos!")
                    return
            try:
                float(nota)
            except ValueError:
                messagebox.showerror("Erro", "Nota inválida!")
                return
            try:
                if tipo == 'PIM':
                    materias_usuario = set()
                    if os.path.exists('notas.dat'):
                        with open('notas.dat', 'r', encoding='utf-8') as f:
                            for linha in f:
                                partes = linha.strip().split('|')
                                if len(partes) == 4:
                                    user, materia_arq, tipo_arq, _ = partes
                                    if user.lower() == usuario.lower() and tipo_arq in ['NP1', 'NP2']:
                                        materias_usuario.add(materia_arq)
                    if not materias_usuario:
                        messagebox.showwarning("Aviso", "O usuário não possui matérias cadastradas para NP1/NP2!")
                        return
                    with open('notas.dat', 'a', encoding='utf-8') as f:
                        for materia in materias_usuario:
                            f.write(f"{usuario}|{materia}|PIM|{nota}\n")
                    messagebox.showinfo("Sucesso", f"Nota do PIM lançada para todas as matérias de {usuario}!")
                else:
                    with open('notas.dat', 'a', encoding='utf-8') as f:
                        f.write(f"{usuario}|{materia}|{tipo}|{nota}\n")
                    messagebox.showinfo("Sucesso", f"Nota lançada para {usuario}!")
                mostrar_tela_lancar_notas()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar nota: {e}")

        botoes_form = tk.Frame(inner2, bg=CARD_BG)
        botoes_form.pack(pady=8)
        styled_button(botoes_form, "Voltar", command=mostrar_tela_lancar_notas, style="ghost").pack(side='left', padx=8)
        styled_button(botoes_form, "Salvar", command=salvar_nota, style="accent").pack(side='left', padx=8)

    styled_button(botoes_frame, "NP1", command=lambda: abrir_formulario('NP1'), style="accent", width=14).pack(side='left', padx=8)
    styled_button(botoes_frame, "NP2", command=lambda: abrir_formulario('NP2'), style="accent", width=14).pack(side='left', padx=8)
    styled_button(botoes_frame, "PIM", command=lambda: abrir_formulario('PIM'), style="accent", width=14).pack(side='left', padx=8)
    styled_button(inner, "Voltar", command=mostrar_submenu_secretaria, style="ghost").pack(pady=8)

def mostrar_tela_lancar_faltas():
    """
    Tela para lançar faltas.
    """
    clear_center()
    wrapper, canvas, inner = create_center_card(center_holder, card_width=520, card_height=420)
    wrapper.update_idletasks()

    tk.Label(inner, text="Lançar Faltas", font=SUBTITLE_FONT, bg=CARD_BG, fg=TEXT_COLOR).pack(pady=(6,8))
    tk.Label(inner, text="Usuário (primeiro nome):", bg=CARD_BG, fg=TEXT_COLOR).pack(fill="x", padx=6)
    entry_usuario = tk.Entry(inner, width=36, **entry_opts)
    entry_usuario.pack(padx=6, pady=(0,6))
    tk.Label(inner, text="Matéria:", bg=CARD_BG, fg=TEXT_COLOR).pack(fill="x", padx=6)
    entry_materia = tk.Entry(inner, width=36, **entry_opts)
    entry_materia.pack(padx=6, pady=(0,6))
    tk.Label(inner, text="Mês:", bg=CARD_BG, fg=TEXT_COLOR).pack(fill="x", padx=6)
    entry_mes = tk.Entry(inner, width=20, **entry_opts)
    entry_mes.pack(padx=6, pady=(0,6))
    tk.Label(inner, text="Faltas:", bg=CARD_BG, fg=TEXT_COLOR).pack(fill="x", padx=6)
    entry_faltas = tk.Entry(inner, width=12, **entry_opts)
    entry_faltas.pack(padx=6, pady=(0,6))

    def salvar_faltas():
        usuario = entry_usuario.get().strip()
        materia = entry_materia.get().strip()
        mes = entry_mes.get().strip()
        faltas = entry_faltas.get().strip()
        if not usuario or not materia or not mes or not faltas:
            messagebox.showwarning("Aviso", "Preencha todos os campos!")
            return
        try:
            int(faltas)
        except ValueError:
            messagebox.showerror("Erro", "Quantidade de faltas inválida!")
            return
        try:
            with open('faltas.dat', 'a', encoding='utf-8') as f:
                f.write(f"{usuario}|{materia}|{mes}|{faltas}\n")
            messagebox.showinfo("Sucesso", f"Faltas lançadas para {usuario}!")
            mostrar_submenu_secretaria()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar faltas: {e}")

    botoes = tk.Frame(inner, bg=CARD_BG)
    botoes.pack(pady=8)
    styled_button(botoes, "Voltar", command=mostrar_submenu_secretaria, style="ghost").pack(side='left', padx=8)
    styled_button(botoes, "Salvar", command=salvar_faltas, style="accent").pack(side='left', padx=8)

# ---------------------------------------------------------------
# Inicializa a aplicação mostrando a tela de login
# ---------------------------------------------------------------
mostrar_tela_login()

root.mainloop()