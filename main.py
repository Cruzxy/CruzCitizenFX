import tkinter as tk
import threading
import re
import time
import math
import sys
import ctypes

# ── ADMIN ─────────────────────────────────────────────────────────────────────
def run_as_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)
    except:
        return False

if not run_as_admin():
    print("Execute como Administrador.")
    input("ENTER para sair...")
    sys.exit(1)

# ── DEPS ──────────────────────────────────────────────────────────────────────
try:
    import pymem
    PYMEM_OK = True
except ImportError:
    PYMEM_OK = False

# ── LÓGICA ────────────────────────────────────────────────────────────────────
def extract_token(log):
    if not PYMEM_OK:
        log("pymem não instalado  —  pip install pymem", "err")
        return None
    try:
        log("Localizando processo FiveM...", "info")
        pm = None
        for name in ["FiveM.exe", "FiveM_GTAProcess.exe", "CitizenFX.exe"]:
            try:
                pm = pymem.Pymem(name)
                log(f"Conectado  ·  {name}", "ok")
                break
            except:
                continue
        if not pm:
            log("Nenhum processo FiveM encontrado.", "err")
            return None

        patterns = [
            rb"X-CitizenFX-Token[^\x00-\x7F]{0,80}?([a-f0-9-]{36})",
            rb"X-CitizenFX-Token[:=]\s*([a-f0-9-]{36})",
            rb"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})",
            rb"token[^\x00-\x7F]{0,100}?([a-f0-9-]{36})",
        ]

        log("Varrendo módulos de memória...", "info")
        for module in pm.list_modules():
            try:
                if module.SizeOfImage < 1_000_000:
                    continue
                sz = module.SizeOfImage // 1024 // 1024
                log(f"  {module.name}  ({sz} MB)", "dim")
                data = pm.read_bytes(module.lpBaseOfDll,
                                     min(module.SizeOfImage, 120_000_000))
                for pat in patterns:
                    for m in re.finditer(pat, data, re.IGNORECASE):
                        tok = m.group(1).decode("ascii", errors="ignore").strip()
                        if len(tok) == 36 and tok.count("-") == 4:
                            log(f"Token encontrado em {module.name}", "ok")
                            return tok
            except:
                continue

        log("Scan profundo...", "warn")
        for pat in patterns:
            try:
                for addr in pymem.pattern.pattern_scan_all(
                        pm.process_handle, pat, return_multiple=True)[:10]:
                    try:
                        data = pm.read_bytes(max(0, addr - 80), 200)
                        for p in patterns:
                            mm = re.search(p, data, re.IGNORECASE)
                            if mm:
                                tok = mm.group(1).decode(
                                    "ascii", errors="ignore").strip()
                                if len(tok) == 36 and tok.count("-") == 4:
                                    return tok
                    except:
                        continue
            except:
                continue

        log("Token não encontrado.", "warn")
        log("Reconecte ao servidor e tente novamente.", "dim")
        return None
    except Exception as e:
        log(f"Erro: {e}", "err")
        return None


# ── PALETA ────────────────────────────────────────────────────────────────────
BG      = "#080a12"
PANEL   = "#0b0e1c"
CARD    = "#0e1224"
BORDER  = "#161f38"
BORDER2 = "#1c2840"
HOVER   = "#131a2e"

FG      = "#e4edff"
FG2     = "#3d5278"
FG3     = "#1d2b42"
FG4     = "#0e1625"

BLUE    = "#3d7ef5"
BLUE_LO = "#0b1b3d"
BLUE_HI = "#6fa4ff"
BLUE_GL = "#142240"
BLUE_MID= "#1a3060"

GREEN   = "#1ec97c"
GREEN_LO= "#061c12"
GREEN_HI= "#45e89e"
GREEN_GL= "#0b2d1c"

RED     = "#e84545"
RED_LO  = "#260808"
RED_HI  = "#ff6868"

YELLOW  = "#e8a830"
YELLOW_LO="#1e1400"

# Fontes — Inter > Segoe UI Variable > Segoe UI (ordem de preferência)
def _best_font(sizes_map):
    """Retorna dict de fontes usando a melhor família disponível."""
    import tkinter.font as tkf
    families = tkf.families()
    for fam in ("Inter", "Segoe UI Variable Text", "Segoe UI Variable",
                 "Segoe UI", "Helvetica Neue", "Arial"):
        if fam in families:
            chosen = fam
            break
    else:
        chosen = "Segoe UI"

    # Cascadia Code para mono
    mono = "Cascadia Code" if "Cascadia Code" in families else "Consolas"
    return chosen, mono

_UI_FAM = None
_MO_FAM = None

def _init_fonts():
    global _UI_FAM, _MO_FAM
    if _UI_FAM: return
    import tkinter.font as tkf
    families = tkf.families()
    for fam in ("Inter", "Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI"):
        if fam in families:
            _UI_FAM = fam; break
    else:
        _UI_FAM = "Segoe UI"
    _MO_FAM = "Cascadia Code" if "Cascadia Code" in families else "Consolas"

def F(size, weight="normal"):
    return (_UI_FAM, size, weight)
def FM(size, weight="normal"):
    return (_MO_FAM, size, weight)


def lerp(a, b, t):
    ra,ga,ba = int(a[1:3],16), int(a[3:5],16), int(a[5:7],16)
    rb,gb,bb = int(b[1:3],16), int(b[3:5],16), int(b[5:7],16)
    return f"#{int(ra+(rb-ra)*t):02x}{int(ga+(gb-ga)*t):02x}{int(ba+(bb-ba)*t):02x}"


# ── WIDGETS ───────────────────────────────────────────────────────────────────

class GlowBar(tk.Canvas):
    """Linha de progresso shimmer."""
    def __init__(self, parent, **kw):
        super().__init__(parent, height=2, highlightthickness=0, bg=BG, **kw)
        self._on = False; self._t = 0.0

    def start(self):
        self._on = True; self._t = 0.0; self._tick()

    def stop(self, ok=True):
        self._on = False
        self.delete("all")
        w = self.winfo_width() or 560
        self.create_rectangle(0, 0, w, 2,
                              fill=GREEN if ok else RED, outline="")
        self.after(800, self.delete, "all")

    def _tick(self):
        if not self._on: return
        self.delete("all")
        w = self.winfo_width() or 560
        self._t = (self._t + 0.022) % 1.0
        bw = int(w * .35)
        x  = int((w + bw) * self._t) - bw
        for ox, ow, col in [
            (x - bw//2, bw,      BLUE_GL),
            (x,         bw,      BLUE_LO),
            (x+bw//3,   bw//2,   BLUE),
            (x+bw*2//3, bw//5,   BLUE_HI),
        ]:
            if ox+ow > 0 and ox < w:
                self.create_rectangle(max(0,ox), 0, min(w,ox+ow), 2,
                                      fill=col, outline="")
        self.after(11, self._tick)


class StatusDot(tk.Canvas):
    def __init__(self, parent, r=4, bg=PANEL, **kw):
        super().__init__(parent, width=r*2+2, height=r*2+2,
                         bg=bg, highlightthickness=0, **kw)
        self._r = r; self._state = "idle"; self._ph = 0.0
        self._paint(FG3); self._tick()

    def _paint(self, c):
        self.delete("all"); r = self._r
        self.create_oval(1,1,r*2+1,r*2+1, fill=c, outline="")

    def _tick(self):
        if self._state == "run":
            self._ph = (self._ph + 0.16) % (2*math.pi)
            self._paint(lerp(BLUE_MID, BLUE_HI, (math.sin(self._ph)+1)/2))
        self.after(45, self._tick)

    def set(self, s):
        self._state = s
        if s != "run":
            self._paint({"idle":FG3,"ok":GREEN,"err":RED}.get(s, FG3))


class InfoPopover(tk.Toplevel):
    """Janelinha flutuante com infos de ambiente."""
    def __init__(self, parent, anchor_widget):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(bg=BORDER2)
        self.attributes("-topmost", True)

        # Posição: abaixo do botão âncora
        anchor_widget.update_idletasks()
        x = anchor_widget.winfo_rootx()
        y = anchor_widget.winfo_rooty() + anchor_widget.winfo_height() + 4
        self.geometry(f"+{x}+{y}")

        inner = tk.Frame(self, bg=CARD, padx=16, pady=12)
        inner.pack(padx=1, pady=1)

        title = tk.Label(inner, text="Ambiente", font=F(9, "bold"),
                         bg=CARD, fg=FG)
        title.pack(anchor="w", pady=(0, 8))

        def row(key, val, vc=FG2):
            f = tk.Frame(inner, bg=CARD)
            f.pack(fill="x", pady=2)
            tk.Label(f, text=key, font=F(8), bg=CARD,
                     fg=FG2, width=8, anchor="w").pack(side="left")
            tk.Label(f, text="·", font=F(8), bg=CARD,
                     fg=FG3).pack(side="left", padx=4)
            tk.Label(f, text=val, font=FM(8), bg=CARD,
                     fg=vc).pack(side="left")

        row("pymem",   "instalado" if PYMEM_OK else "ausente",
            GREEN_HI if PYMEM_OK else RED_HI)
        py_v = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        row("python",  py_v, FG2)
        row("modo",    "administrador", GREEN_HI)
        row("output",  "memória", BLUE_HI)

        if not PYMEM_OK:
            tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(8,6))
            warn = tk.Frame(inner, bg=YELLOW_LO)
            warn.pack(fill="x")
            tk.Label(warn, text="pip install pymem", font=FM(8),
                     bg=YELLOW_LO, fg=YELLOW,
                     padx=8, pady=5).pack()

        # Fecha ao clicar fora
        self.bind("<FocusOut>", lambda _: self.destroy())
        self.bind("<Escape>",   lambda _: self.destroy())
        self.focus_set()


class ExtractBtn(tk.Frame):
    """Botão grande de extração com ícone e hover suave."""
    def __init__(self, parent, cmd, **kw):
        super().__init__(parent, bg=BLUE_LO, **kw)
        self.config(highlightthickness=1, highlightbackground=BLUE_MID)
        self._cmd = cmd
        self._busy = False

        self._icon = tk.Label(self, text="⬡", font=F(18),
                              bg=BLUE_LO, fg=BLUE_HI,
                              cursor="hand2")
        self._icon.pack(pady=(18, 4))

        self._lbl = tk.Label(self, text="Extrair Token",
                             font=F(11, "bold"),
                             bg=BLUE_LO, fg=BLUE_HI,
                             cursor="hand2")
        self._lbl.pack(pady=(0, 6))

        self._sub = tk.Label(self, text="varredura de memória",
                             font=F(8),
                             bg=BLUE_LO, fg=FG2,
                             cursor="hand2")
        self._sub.pack(pady=(0, 18))

        for w in (self, self._icon, self._lbl, self._sub):
            w.bind("<Enter>",    self._on)
            w.bind("<Leave>",    self._off)
            w.bind("<Button-1>", self._click)

    def _on(self,  _=None):
        if not self._busy:
            for w in (self, self._icon, self._lbl, self._sub):
                w.config(bg=BLUE_GL)
            self.config(highlightbackground=BLUE_HI)
    def _off(self, _=None):
        for w in (self, self._icon, self._lbl, self._sub):
            w.config(bg=BLUE_LO)
        self.config(highlightbackground=BLUE_MID)

    def _click(self, _=None):
        if not self._busy: self._cmd()

    def set_busy(self, v):
        self._busy = v
        self._lbl.config(text="Extraindo..." if v else "Extrair Token")
        self._sub.config(text="aguarde..." if v else "varredura de memória")
        col = FG3 if v else BLUE_HI
        self._icon.config(fg=col)
        self._lbl.config(fg=col)


class Console(tk.Frame):
    TAGS = {
        "dim":  FG3,
        "ok":   GREEN_HI,
        "err":  RED_HI,
        "warn": YELLOW,
        "info": BLUE_HI,
        "ts":   FG3,
        "pipe": "#1a2d48",
        "bar":  FG3,
    }

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=CARD, **kw)
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=CARD)
        hdr.pack(fill="x", padx=12, pady=(7, 0))

        tf = tk.Frame(hdr, bg=CARD)
        tf.pack(side="left")
        for col in (RED, YELLOW, GREEN):
            c = tk.Canvas(tf, width=8, height=8, bg=CARD, highlightthickness=0)
            c.pack(side="left", padx=(0, 4))
            c.create_oval(0, 0, 8, 8, fill=col, outline="")

        tk.Label(hdr, text="  terminal", font=FM(8),
                 bg=CARD, fg=FG3).pack(side="left")

        clr = tk.Label(hdr, text="limpar", font=F(8),
                       bg=CARD, fg=FG2, cursor="hand2")
        clr.pack(side="right")
        clr.bind("<Button-1>", lambda _: self.clear())
        clr.bind("<Enter>",    lambda _: clr.config(fg=BLUE_HI))
        clr.bind("<Leave>",    lambda _: clr.config(fg=FG2))

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", pady=(5, 0))

        self._txt = tk.Text(
            self,
            font=FM(8),
            bg=BG, fg=FG2,
            state="disabled", relief="flat",
            padx=12, pady=8,
            selectbackground=BLUE_LO,
            selectforeground=FG,
            wrap="none",
            spacing1=0, spacing3=2,
            cursor="arrow",
            highlightthickness=0,
            height=10,   # altura mínima: garante que o TokenField fique visível
        )
        self._txt.pack(fill="both", expand=True)

        sb = tk.Scrollbar(self._txt, orient="vertical",
                          command=self._txt.yview,
                          bg=CARD, troughcolor=BG,
                          relief="flat", width=3, highlightthickness=0)
        self._txt.config(yscrollcommand=sb.set)

        for tag, col in self.TAGS.items():
            self._txt.tag_config(tag, foreground=col)

    def log(self, msg, tag="dim"):
        self._txt.config(state="normal")
        ts = time.strftime("%H:%M:%S")
        self._txt.insert("end", ts, "ts")
        self._txt.insert("end", "  │  ", "pipe")
        self._txt.insert("end", f"{msg}\n", tag)
        self._txt.see("end")
        self._txt.config(state="disabled")

    def log_sep(self):
        self._txt.config(state="normal")
        self._txt.insert("end", "─" * 50 + "\n", "bar")
        self._txt.see("end")
        self._txt.config(state="disabled")

    def clear(self):
        self._txt.config(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.config(state="disabled")


class TokenField(tk.Frame):
    def __init__(self, parent, on_copy, **kw):
        super().__init__(parent, bg=PANEL, **kw)
        self._on_copy = on_copy
        self._token   = None
        self._build()

    def _build(self):
        # Rótulo
        top = tk.Frame(self, bg=PANEL)
        top.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(top, text="TOKEN EXTRAÍDO", font=F(8),
                 bg=PANEL, fg=FG2).pack(side="left")
        self._status_lbl = tk.Label(top, text="aguardando",
                                    font=FM(8), bg=PANEL, fg=FG3)
        self._status_lbl.pack(side="right")

        # Campo
        wrap = tk.Frame(self, bg=BORDER2)
        wrap.pack(fill="x", padx=14, pady=(0, 6))
        inner = tk.Frame(wrap, bg=CARD)
        inner.pack(fill="x", padx=1, pady=1)

        # Prompt
        tk.Label(inner, text="$", font=FM(10),
                 bg=CARD, fg=FG2, padx=12).pack(side="left")

        self._var = tk.StringVar(value="—")
        self._lbl = tk.Label(inner, textvariable=self._var,
                             font=FM(10), bg=CARD, fg=FG2,
                             anchor="w", pady=10)
        self._lbl.pack(side="left", fill="x", expand=True)

        # Botão copiar
        cp = tk.Label(inner, text="copiar ⎘", font=F(8),
                      bg=CARD, fg=FG2, cursor="hand2", padx=12)
        cp.pack(side="right")
        cp.bind("<Button-1>", lambda _: self._do_copy())
        cp.bind("<Enter>",    lambda _: cp.config(fg=BLUE_HI))
        cp.bind("<Leave>",    lambda _: cp.config(fg=FG2))

        self._fb = tk.Label(self, text="", font=F(8),
                            bg=PANEL, fg=GREEN_HI)
        self._fb.pack(anchor="w", padx=14, pady=(0, 8))

    def set(self, token):
        self._token = token
        self._var.set(token)
        self._lbl.config(fg=GREEN_HI)
        self._status_lbl.config(text="✓  capturado", fg=GREEN_HI)

    def get(self):
        return self._token or ""

    def _do_copy(self):
        if self._token:
            self._on_copy()
            self._fb.config(text="  ✓  copiado para a área de transferência")
            self.after(2000, lambda: self._fb.config(text=""))


class Footer(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=PANEL, height=22, **kw)
        self.pack_propagate(False)
        tk.Frame(self, bg=BORDER, height=1).pack(side="top", fill="x")
        row = tk.Frame(self, bg=PANEL)
        row.pack(fill="both", expand=True, padx=10)

        self._dot = StatusDot(row, r=3, bg=PANEL)
        self._dot.pack(side="left", pady=4)
        self._msg = tk.StringVar(value="pronto")
        self._lbl = tk.Label(row, textvariable=self._msg,
                             font=F(8), bg=PANEL, fg=FG2)
        self._lbl.pack(side="left", padx=5)
        self._clk = tk.StringVar()
        tk.Label(row, textvariable=self._clk,
                 font=FM(8), bg=PANEL, fg=FG3).pack(side="right")
        self._tick()

    def _tick(self):
        self._clk.set(time.strftime("%H:%M:%S"))
        self.after(1000, self._tick)

    def set(self, msg, state="idle"):
        self._msg.set(msg)
        self._dot.set(state)
        self._lbl.config(fg={"idle":FG2,"run":BLUE_HI,
                              "ok":GREEN_HI,"err":RED_HI}.get(state, FG2))


# ── APP ───────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        _init_fonts()                       # detecta melhor fonte disponível

        self.title("Cruz Token Extractor")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._busy = False

        # Layout em duas colunas: esquerda = botão grande, direita = console+token
        # Calcula altura necessária antes de mostrar
        self._build()

        # Força render para medir tamanhos reais
        self.update_idletasks()

        # Tamanho fixo inicial: 700 × 520 — cabe tudo sem cortar o TokenField
        W, H = 700, 520
        self.minsize(600, 480)
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - W) // 2
        y  = (sh - H) // 2
        self.geometry(f"{W}x{H}+{x}+{y}")

        self._welcome()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Top bar
        self._topbar()

        # GlowBar (2px)
        self._gbar = GlowBar(self)
        self._gbar.pack(fill="x")

        # ── Corpo: 2 colunas
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # Coluna esquerda — botão grande
        left = tk.Frame(body, bg=PANEL, width=200)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")
        self._left_col(left)

        # Coluna direita — console + token
        right = tk.Frame(body, bg=BG)
        right.pack(side="right", fill="both", expand=True)
        self._right_col(right)

        # Footer
        self._footer = Footer(self)
        self._footer.pack(fill="x", side="bottom")

    def _topbar(self):
        bar = tk.Frame(self, bg=PANEL, height=42)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=BORDER, height=1).pack(side="bottom", fill="x")

        row = tk.Frame(bar, bg=PANEL)
        row.pack(fill="both", expand=True, padx=16)

        # Logo
        logo = tk.Frame(row, bg=PANEL)
        logo.pack(side="left", pady=10)

        ic = tk.Canvas(logo, width=20, height=20,
                       bg=PANEL, highlightthickness=0)
        ic.pack(side="left", padx=(0, 10))
        ic.create_oval(1, 1, 19, 19, fill=BLUE_LO, outline=BLUE, width=1)
        ic.create_oval(7, 7, 13, 13, fill=BLUE, outline="")

        tk.Label(logo, text="Cruz Token Extractor", font=F(11, "bold"),
                 bg=PANEL, fg=FG).pack(side="left")

        # Botão info (⊙) — direita
        right = tk.Frame(row, bg=PANEL)
        right.pack(side="right", pady=11)

        self._info_btn = tk.Label(
            right, text="ⓘ", font=F(12),
            bg=PANEL, fg=FG2, cursor="hand2", padx=4)
        self._info_btn.pack(side="right")
        self._info_btn.bind("<Button-1>", self._toggle_info)
        self._info_btn.bind("<Enter>",    lambda _: self._info_btn.config(fg=BLUE_HI))
        self._info_btn.bind("<Leave>",    lambda _: self._info_btn.config(fg=FG2))
        self._popover = None

    def _left_col(self, parent):
        """Coluna esquerda com botão grande centralizado."""
        wrap = tk.Frame(parent, bg=PANEL)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)

        self._extract_btn = ExtractBtn(wrap, self._extract)
        self._extract_btn.pack(fill="x")

        # Dica abaixo do botão
        tk.Label(wrap,
                 text="Conecte-se a um\nservidor FiveM antes\nde extrair.",
                 font=F(8),
                 bg=PANEL, fg=FG3,
                 justify="center").pack(pady=(14, 0))

    def _right_col(self, parent):
        """Console de logs + campo de token."""
        self._console = Console(parent)
        self._console.pack(fill="both", expand=True)

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

        self._tok = TokenField(parent, on_copy=self._copy)
        self._tok.pack(fill="x")

    # ── Info popover ──────────────────────────────────────────────────────────

    def _toggle_info(self, _=None):
        if self._popover and self._popover.winfo_exists():
            self._popover.destroy()
            self._popover = None
        else:
            self._popover = InfoPopover(self, self._info_btn)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _welcome(self):
        self._console.log("Cruz Token Extractor inicializado.", "ok")
        if PYMEM_OK:
            self._console.log("pymem detectado e pronto.", "info")
        else:
            self._console.log("pymem ausente  —  pip install pymem", "warn")
        self._console.log("Aguardando ação.", "dim")

    def _copy(self):
        t = self._tok.get()
        if t:
            self.clipboard_clear()
            self.clipboard_append(t)
            self._console.log("Token copiado para a área de transferência.", "ok")

    # ── Extração ──────────────────────────────────────────────────────────────

    def _extract(self):
        if self._busy: return
        self._busy = True
        self._extract_btn.set_busy(True)
        self._footer.set("varrendo memória...", "run")
        self._gbar.start()
        self._console.log_sep()
        self._console.log("Extração iniciada.", "info")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        tok = extract_token(self._console.log)
        self.after(0, self._done, tok)

    def _done(self, tok):
        self._busy = False
        self._extract_btn.set_busy(False)
        if tok:
            self._tok.set(tok)
            self._footer.set("token extraído com sucesso", "ok")
            self._gbar.stop(ok=True)
            self._console.log(f"Token  →  {tok}", "ok")
        else:
            self._footer.set("token não encontrado", "err")
            self._gbar.stop(ok=False)
            self._console.log("Falha. Reconecte ao servidor FiveM.", "err")
        self._console.log_sep()


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()