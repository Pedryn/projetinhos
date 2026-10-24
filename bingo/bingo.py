# -*- coding: utf-8 -*-
import math
import random
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


class BingoApp:
    BG = "#050b0a"
    PANEL = "#111715"
    PANEL_2 = "#09110f"
    BORDER = "#33413c"
    TEXT = "#f3f6f2"
    GREEN = "#32b933"
    DARK_BALL = "#151b19"

    def __init__(self, root):
        self.root = root
        self.root.title("Bingo")
        self.root.geometry("1040x820")
        self.root.minsize(980, 760)
        self.root.configure(bg=self.BG)

        self.limite = 100
        self.numeros = []
        self.sorteados = []
        self.ultimos_visiveis = []
        self.bolas = {}
        self.fundo_original = None
        self.fundo_renderizado = None
        self.fundo_root_photo = None
        self.fundo_grade_photo = None
        self.fundo_maquina_photo = None
        self.fundo_label = None

        self.iniciar_novo_jogo()

    def limpar_tela(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def iniciar_novo_jogo(self):
        self.numeros = list(range(1, self.limite + 1))
        random.shuffle(self.numeros)
        self.sorteados = []
        self.ultimos_visiveis = []
        self.criar_tela_jogo()

    def aplicar_limite(self):
        try:
            limite = int(self.limite_entry.get())
            if limite < 1 or limite > 200:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Digite um numero entre 1 e 200.")
            return

        self.limite = limite
        self.iniciar_novo_jogo()

    def criar_tela_jogo(self):
        self.limpar_tela()
        self.bolas = {}
        self.criar_fundo()

        for coluna in range(3):
            self.root.grid_columnconfigure(coluna, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        self.criar_painel_config(self.root).grid(row=0, column=0, sticky="nw", padx=(22, 8), pady=(14, 8))
        self.criar_maquina(self.root).grid(row=0, column=1, sticky="n", padx=8, pady=(8, 0))
        self.criar_painel_ultimos(self.root).grid(row=0, column=2, sticky="ne", padx=(8, 22), pady=(14, 8))

        self.criar_painel_contador(self.root).grid(row=1, column=0, sticky="w", padx=(22, 8), pady=(2, 10))

        tk.Button(
            self.root,
            text="SORTEAR NUMERO",
            font=("Arial", 18, "bold"),
            bg="#119f2b",
            fg=self.TEXT,
            activebackground="#20c342",
            activeforeground=self.TEXT,
            relief="raised",
            bd=4,
            padx=28,
            pady=10,
            cursor="hand2",
            command=self.sortear,
        ).grid(row=1, column=2, sticky="e", padx=(8, 22), pady=(2, 10))

        self.criar_grade(self.root).grid(row=2, column=0, columnspan=3, sticky="nsew", padx=22, pady=(0, 18))
        self.criar_botao_fundo()
        self.atualizar_interface()
        self.atualizar_fundo()

    def criar_fundo(self):
        self.fundo_label = tk.Label(self.root, bg=self.BG, bd=0)
        self.fundo_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.fundo_label.lower()
        self.root.bind("<Configure>", self.atualizar_fundo)

    def criar_botao_fundo(self):
        botao = tk.Button(
            self.root,
            text="?",
            font=("Arial", 16, "bold"),
            bg="#18211e",
            fg=self.TEXT,
            activebackground="#26312d",
            activeforeground=self.TEXT,
            relief="ridge",
            bd=3,
            cursor="hand2",
            command=self.escolher_fundo,
        )
        botao.place(relx=1.0, rely=1.0, x=-18, y=-18, anchor="se", width=44, height=44)
        botao.lift()

    def escolher_fundo(self):
        caminho = filedialog.askopenfilename(
            title="Escolher foto de fundo",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if not caminho:
            return

        try:
            if Image is not None:
                self.fundo_original = Image.open(caminho).convert("RGB")
            else:
                self.fundo_original = tk.PhotoImage(file=caminho)
        except Exception:
            messagebox.showerror(
                "Erro",
                "Nao consegui abrir esta imagem. Para JPG, instale o Pillow: pip install pillow",
            )
            return

        numero_atual = self.sorteados[-1] if self.sorteados else None
        self.atualizar_fundo()
        self.atualizar_interface(numero_atual)

    def atualizar_fundo(self, _event=None):
        if self.fundo_original is None or self.fundo_label is None:
            return

        largura = max(self.root.winfo_width(), 1)
        altura = max(self.root.winfo_height(), 1)

        if Image is not None and isinstance(self.fundo_original, Image.Image):
            imagem = self.fundo_original.copy()
            proporcao = max(largura / imagem.width, altura / imagem.height)
            novo_tamanho = (
                max(int(imagem.width * proporcao), 1),
                max(int(imagem.height * proporcao), 1),
            )
            imagem = imagem.resize(novo_tamanho, Image.LANCZOS)
            esquerda = (imagem.width - largura) // 2
            topo = (imagem.height - altura) // 2
            imagem = imagem.crop((esquerda, topo, esquerda + largura, topo + altura))
            self.fundo_renderizado = imagem
            self.fundo_root_photo = ImageTk.PhotoImage(imagem)
        else:
            self.fundo_renderizado = None
            self.fundo_root_photo = self.fundo_original

        self.fundo_label.config(image=self.fundo_root_photo)
        self.fundo_label.lower()
        self.redesenhar_areas_com_fundo()

    def redesenhar_areas_com_fundo(self):
        if hasattr(self, "grade_canvas"):
            self.desenhar_grade()
        if hasattr(self, "maquina"):
            numero_atual = self.sorteados[-1] if self.sorteados else None
            self.desenhar_maquina(numero_atual)

    def criar_card(self, parent, width, height):
        frame = tk.Frame(
            parent,
            width=width,
            height=height,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=2,
            bd=0,
        )
        frame.grid_propagate(False)
        frame.pack_propagate(False)
        return frame

    def criar_painel_config(self, parent):
        card = self.criar_card(parent, 220, 178)

        tk.Label(
            card,
            text="ATE QUAL NUMERO?",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Arial", 11, "bold"),
        ).pack(pady=(12, 6))

        self.limite_entry = tk.Entry(
            card,
            font=("Arial", 30, "bold"),
            justify="center",
            bg="#07100e",
            fg=self.GREEN,
            insertbackground=self.TEXT,
            relief="flat",
            highlightbackground="#2d3935",
            highlightthickness=2,
            width=6,
        )
        self.limite_entry.insert(0, str(self.limite))
        self.limite_entry.pack(padx=16, pady=(0, 12), ipady=2)
        self.limite_entry.bind("<Return>", lambda _event: self.aplicar_limite())

        tk.Button(
            card,
            text="Novo Jogo",
            font=("Arial", 13, "bold"),
            bg=self.PANEL,
            fg=self.TEXT,
            activebackground="#1c2622",
            activeforeground=self.TEXT,
            relief="ridge",
            bd=3,
            cursor="hand2",
            command=self.aplicar_limite,
        ).pack(fill="x", padx=16, ipady=6)

        return card

    def criar_painel_ultimos(self, parent):
        card = self.criar_card(parent, 286, 178)

        tk.Label(
            card,
            text="ULTIMOS SORTEADOS",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Arial", 11, "bold"),
        ).pack(pady=(12, 8))

        self.ultimos_canvas = tk.Canvas(
            card,
            width=252,
            height=72,
            bg=self.PANEL,
            highlightthickness=0,
        )
        self.ultimos_canvas.pack()

        tk.Button(
            card,
            text="Limpar Ultimos",
            font=("Arial", 12, "bold"),
            bg=self.PANEL,
            fg=self.TEXT,
            activebackground="#1c2622",
            activeforeground=self.TEXT,
            relief="ridge",
            bd=3,
            cursor="hand2",
            command=self.limpar_ultimos,
        ).pack(fill="x", padx=42, pady=(10, 0), ipady=5)

        return card

    def criar_maquina(self, parent):
        frame = tk.Frame(parent, bg=self.BG)
        self.maquina = tk.Canvas(
            frame,
            width=330,
            height=270,
            bg=self.BG,
            highlightthickness=0,
        )
        self.maquina.pack()
        self.desenhar_maquina(None)
        return frame

    def desenhar_maquina(self, numero):
        c = self.maquina
        c.delete("all")
        self.desenhar_recorte_fundo_canvas(c, 330, 270, "fundo_maquina_photo")
        if self.fundo_original is not None:
            c.create_rectangle(0, 0, 330, 270, fill="#000000", stipple="gray50", outline="")

        c.create_oval(70, 8, 260, 180, outline="#87908b", width=3, fill="#101614")
        for x in range(88, 250, 22):
            c.create_arc(x - 52, 8, x + 52, 180, start=80, extent=200, outline="#8e9691", width=2)
            c.create_arc(x - 52, 8, x + 52, 180, start=260, extent=200, outline="#424a47", width=1)
        for y in range(32, 172, 25):
            c.create_arc(70, y - 50, 260, y + 50, start=0, extent=180, outline="#9aa29d", width=2)

        for _ in range(20):
            x = random.randint(98, 232)
            y = random.randint(118, 168)
            c.create_oval(x - 9, y - 9, x + 9, y + 9, fill="#e5e1d9", outline="#a9a69f", width=1)
            c.create_text(
                x,
                y,
                text=str(random.randint(1, max(9, self.limite))),
                fill="#353535",
                font=("Arial", 6, "bold"),
                angle=random.randint(-25, 25),
            )

        c.create_rectangle(54, 132, 70, 250, fill="#353a38", outline="#a3aaa5", width=2)
        c.create_rectangle(260, 132, 276, 250, fill="#353a38", outline="#a3aaa5", width=2)
        c.create_rectangle(40, 245, 292, 265, fill="#2f3432", outline="#515957", width=2)
        c.create_line(260, 142, 306, 142, fill="#a8aca8", width=6)
        c.create_line(303, 142, 303, 192, fill="#a8aca8", width=6)
        c.create_oval(288, 184, 328, 210, fill="#262b2a", outline="#555c59", width=2)

        c.create_oval(118, 162, 218, 262, fill="#050706", outline="#4b504e", width=6)
        c.create_oval(132, 176, 204, 248, fill="#e7e7e2", outline="#c5c5bd", width=3)
        c.create_text(
            168,
            213,
            text=str(numero) if numero else "-",
            fill="#080908",
            font=("Arial", 36, "bold"),
        )

    def criar_painel_contador(self, parent):
        card = self.criar_card(parent, 230, 82)

        tk.Label(
            card,
            text="SORTEADOS",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Arial", 11, "bold"),
        ).pack(pady=(8, 0))

        self.contador_label = tk.Label(
            card,
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Arial", 26, "bold"),
        )
        self.contador_label.pack()
        return card

    def criar_grade(self, parent):
        moldura = tk.Frame(
            parent,
            bg=self.PANEL_2,
            highlightbackground=self.BORDER,
            highlightthickness=3,
        )
        moldura.grid_columnconfigure(0, weight=1)
        moldura.grid_rowconfigure(0, weight=1)

        self.grade_canvas = tk.Canvas(
            moldura,
            bg=self.PANEL_2,
            highlightthickness=0,
        )
        self.grade_canvas.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.grade_canvas.bind("<Configure>", lambda _event: self.desenhar_grade())

        self.desenhar_grade()
        return moldura

    def desenhar_grade(self):
        self.grade_canvas.delete("all")

        cols = 10 if self.limite <= 100 else 20
        rows = math.ceil(self.limite / cols)

        largura = max(self.grade_canvas.winfo_width(), 300)
        altura = max(self.grade_canvas.winfo_height(), 300)
        self.desenhar_fundo_grade(largura, altura)

        margem = 15

        cell = min(
            (largura - margem * 2) / cols,
            (altura - margem * 2) / rows
        )

        radius = cell * 0.38
        fonte = max(int(cell * 0.30), 8)

        offset_x = (largura - cols * cell) / 2
        offset_y = (altura - rows * cell) / 2

        self.bolas = {}

        for numero in range(1, self.limite + 1):

            row = (numero - 1) // cols
            col = (numero - 1) % cols

            x = offset_x + col * cell + cell / 2
            y = offset_y + row * cell + cell / 2

            oval = self.grade_canvas.create_oval(
                x-radius,
                y-radius,
                x+radius,
                y+radius,
                fill=self.DARK_BALL,
                outline="#6f7773",
                width=2
            )

            texto = self.grade_canvas.create_text(
                x,
                y,
                text=str(numero),
                fill=self.TEXT,
                font=("Arial", fonte, "bold")
            )

            self.bolas[numero] = (oval, texto)

    def desenhar_fundo_grade(self, largura, altura):
        self.desenhar_recorte_fundo_canvas(self.grade_canvas, largura, altura, "fundo_grade_photo")
        if self.fundo_original is None:
            return

        self.grade_canvas.create_rectangle(
            0,
            0,
            largura,
            altura,
            fill="#000000",
            stipple="gray50",
            outline="",
        )

    def desenhar_recorte_fundo_canvas(self, canvas, largura, altura, atributo_photo):
        if self.fundo_original is None:
            return

        if Image is not None and isinstance(self.fundo_original, Image.Image):
            if self.fundo_renderizado is None:
                return

            self.root.update_idletasks()
            x = canvas.winfo_rootx() - self.root.winfo_rootx()
            y = canvas.winfo_rooty() - self.root.winfo_rooty()
            x = max(int(x), 0)
            y = max(int(y), 0)

            direita = min(x + int(largura), self.fundo_renderizado.width)
            baixo = min(y + int(altura), self.fundo_renderizado.height)
            recorte = self.fundo_renderizado.crop((x, y, direita, baixo))

            if recorte.width != int(largura) or recorte.height != int(altura):
                imagem = Image.new("RGB", (int(largura), int(altura)), self.BG)
                imagem.paste(recorte, (0, 0))
                recorte = imagem

            setattr(self, atributo_photo, ImageTk.PhotoImage(recorte))
            canvas.create_image(0, 0, image=getattr(self, atributo_photo), anchor="nw")
        else:
            setattr(self, atributo_photo, self.fundo_original)
            canvas.create_image(largura // 2, altura // 2, image=getattr(self, atributo_photo))

    def limpar_ultimos(self):
        self.ultimos_visiveis = []
        self.atualizar_ultimos()

    def sortear(self):
        if not self.numeros:
            messagebox.showinfo("Fim", "Todos os numeros ja foram sorteados!")
            return

        numero = self.numeros.pop()
        self.sorteados.append(numero)
        self.ultimos_visiveis.insert(0, numero)
        self.ultimos_visiveis = self.ultimos_visiveis[:10]
        self.atualizar_interface(numero)

    def atualizar_interface(self, numero_atual=None):
        self.contador_label.config(
            text=f"{len(self.sorteados)} / {self.limite}",
            fg=self.GREEN if self.sorteados else self.TEXT,
        )
        self.desenhar_maquina(numero_atual)
        self.atualizar_ultimos()
        self.atualizar_grade()

    def atualizar_ultimos(self):
        self.ultimos_canvas.delete("all")

        for index in range(10):
            row = index // 5
            col = index % 5
            texto = str(self.ultimos_visiveis[index]) if index < len(self.ultimos_visiveis) else ""
            x = 26 + col * 50
            y = 18 + row * 36

            self.ultimos_canvas.create_oval(
                x - 16,
                y - 16,
                x + 16,
                y + 16,
                fill=self.DARK_BALL,
                outline="#6b7370",
                width=2,
            )
            self.ultimos_canvas.create_text(
                x,
                y,
                text=texto,
                fill=self.TEXT,
                font=("Arial", 12, "bold"),
            )

    def atualizar_grade(self):
        sorteados = set(self.sorteados)
        for numero, (oval, text) in self.bolas.items():
            if numero in sorteados:
                self.grade_canvas.itemconfig(oval, fill=self.GREEN, outline="#7ff06b", width=2)
            else:
                self.grade_canvas.itemconfig(oval, fill=self.DARK_BALL, outline="#6f7773", width=2)
            self.grade_canvas.itemconfig(text, fill=self.TEXT)


if __name__ == "__main__":
    root = tk.Tk()
    app = BingoApp(root)
    root.mainloop()