import tkinter as tk
import threading
import re
import sys
import ctypes
import os
from ctypes import wintypes

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

# ── HELPERS ───────────────────────────────────────────────────────────────────
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ── DEPS ──────────────────────────────────────────────────────────────────────
try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

# ── WinAPI ────────────────────────────────────────────────────
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ           = 0x0010
MEM_COMMIT                = 0x1000
PAGE_READONLY             = 0x02
PAGE_READWRITE            = 0x04
PAGE_GUARD                = 0x100

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress",       wintypes.LPVOID),
        ("AllocationBase",    wintypes.LPVOID),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize",        ctypes.c_size_t),
        ("State",             wintypes.DWORD),
        ("Protect",           wintypes.DWORD),
        ("Type",              wintypes.DWORD),
    ]

kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype  = wintypes.HANDLE
kernel32.VirtualQueryEx.argtypes = [
    wintypes.HANDLE, wintypes.LPCVOID,
    ctypes.POINTER(MEMORY_BASIC_INFORMATION), ctypes.c_size_t
]
kernel32.VirtualQueryEx.restype = ctypes.c_size_t
kernel32.ReadProcessMemory.argtypes = [
    wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID,
    ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
]
kernel32.ReadProcessMemory.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype  = wintypes.BOOL

# ── LÓGICA DE EXTRAÇÃO ────────────────────────────────────────────────────────
def find_game_process():
    if not PSUTIL_OK:
        return None
    pattern = re.compile(r"(FiveM|RedM)(_b\d+)?_(GTA|Game)?Process", re.IGNORECASE)
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            name = proc.info["name"] or ""
            if pattern.match(name):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def extract_token():
    try:
        proc = find_game_process()
        if not proc:
            return None

        handle = kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, proc.pid
        )
        if not handle:
            return None

        try:
            token_marker = b"X-CitizenFX-Token: "
            address = 0
            mbi = MEMORY_BASIC_INFORMATION()
            chunk_size = 524288
            max_region = 67108864

            while True:
                if kernel32.VirtualQueryEx(
                    handle, ctypes.c_void_p(address),
                    ctypes.byref(mbi), ctypes.sizeof(mbi)
                ) == 0:
                    break

                base = mbi.BaseAddress or 0
                size = mbi.RegionSize or 0
                state = mbi.State
                protect = mbi.Protect

                if (state == MEM_COMMIT and
                    (protect == PAGE_READONLY or protect == PAGE_READWRITE or
                     (protect & (PAGE_READONLY | PAGE_READWRITE))) and
                    not (protect & PAGE_GUARD) and size > 0):

                    region_end = base + min(size, max_region)
                    current_addr = base

                    while current_addr < region_end:
                        to_read = min(chunk_size, region_end - current_addr)
                        buffer = (ctypes.c_char * to_read)()
                        bytes_read = ctypes.c_size_t(0)

                        ok = kernel32.ReadProcessMemory(
                            handle, ctypes.c_void_p(current_addr),
                            buffer, to_read, ctypes.byref(bytes_read)
                        )
                        if ok and bytes_read.value > 0:
                            data = bytes(buffer[:bytes_read.value])
                            idx = data.find(token_marker)
                            if idx != -1:
                                start = idx + len(token_marker)
                                end0 = data.find(b"\x00", start)
                                endr = data.find(b"\r", start)
                                endn = data.find(b"\n", start)
                                ends = [e for e in (end0, endr, endn) if e != -1]
                                end = min(ends) if ends else len(data)
                                raw = data[start:end]
                                tok = (raw.decode("ascii", errors="ignore")
                                       .replace("X-CitizenFX-Token:", "")
                                       .strip())
                                if tok and 30 <= len(tok) <= 50:
                                    return tok
                        current_addr += to_read

                next_addr = base + size if size else address + 0x1000
                if next_addr <= address:
                    break
                address = next_addr
            return None
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        return None


# ── PALETA ────────────────────────────────────────────────────────────────────
BG        = "#0b0d10"
SURFACE   = "#12151a"
CARD      = "#161a20"
TOKEN_BG  = "#0e1116"
BORDER    = "#1e232b"
BORDER_HI = "#2a3140"
FG        = "#f1f5f9"
FG2       = "#94a3b8"
FG3       = "#64748b"
BLUE      = "#3b82f6"
BLUE_DIM  = "#1e3a5f"
BLUE_BTN  = "#2563eb"
BLUE_HOV  = "#1d4ed8"
GREEN     = "#22c55e"
RED       = "#ef4444"

UI_FONTS  = ("Segoe UI", "Inter", "Arial")
MONO_FONTS = ("Cascadia Mono", "Consolas", "Courier New")

_UI = _MO = None

def _init_fonts():
    global _UI, _MO
    if _UI:
        return
    import tkinter.font as tkf
    fams = tkf.families()
    _UI = next((f for f in UI_FONTS if f in fams), "Segoe UI")
    _MO = next((f for f in MONO_FONTS if f in fams), "Consolas")

def F(sz, w="normal"):
    return (_UI, sz, w)

def FM(sz, w="normal"):
    return (_MO, sz, w)


# ── APP ───────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        _init_fonts()

        self.title("Cruz Token Extractor")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._busy = False
        self._token = None
        self._auto = False
        self._auto_job = None

        try:
            p = resource_path("logo.ico")
            if os.path.exists(p):
                self.iconbitmap(p)
        except:
            pass

        self._build()
        self.update_idletasks()

        W, H = 380, 290
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.minsize(W, H)

        self.after(250, self._refresh)

    def _build(self):
        pad = tk.Frame(self, bg=BG)
        pad.pack(fill="both", expand=True, padx=18, pady=14)

        # ── Header ────────────────────────────────────────────────────────────
        head = tk.Frame(pad, bg=BG)
        head.pack(fill="x")

        self._logo_img = None
        try:
            from PIL import Image, ImageTk
            p = resource_path("logo.ico")
            if os.path.exists(p):
                img = Image.open(p).resize((30, 30), Image.Resampling.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                tk.Label(head, image=self._logo_img, bg=BG).pack(side="left", padx=(0, 9))
        except Exception:
            c = tk.Canvas(head, width=30, height=30, bg=BG, highlightthickness=0)
            c.pack(side="left", padx=(0, 9))
            c.create_oval(1, 1, 29, 29, fill=BLUE_DIM, outline=BLUE, width=1)
            c.create_oval(9, 9, 21, 21, fill=BLUE, outline="")

        titles = tk.Frame(head, bg=BG)
        titles.pack(side="left", fill="y")
        tk.Label(titles, text="Cruz Token Extractor", font=F(12, "bold"),
                 bg=BG, fg=FG).pack(anchor="w")

        st = tk.Frame(titles, bg=BG)
        st.pack(anchor="w", pady=(1, 0))
        self._dot = tk.Canvas(st, width=7, height=7, bg=BG, highlightthickness=0)
        self._dot.pack(side="left", padx=(1, 5), pady=1)
        self._dot.create_oval(0, 0, 7, 7, fill=FG3, outline="")
        self._status = tk.Label(st, text="Aguardando...", font=F(8), bg=BG, fg=FG3)
        self._status.pack(side="left")

        # ── Card do token ─────────────────────────────────────────────────────
        card_wrap = tk.Frame(pad, bg=BORDER_HI)
        card_wrap.pack(fill="x", pady=(12, 0))

        card = tk.Frame(card_wrap, bg=CARD)
        card.pack(fill="x", padx=1, pady=1)

        cpad = tk.Frame(card, bg=CARD)
        cpad.pack(fill="x", padx=12, pady=10)

        tk.Label(cpad, text="TOKEN ATUAL", font=F(7, "bold"),
                 bg=CARD, fg=BLUE).pack(anchor="w")

        # Fundo diferente só atrás do texto do token
        tok_box = tk.Frame(cpad, bg=TOKEN_BG, highlightthickness=1,
                           highlightbackground=BORDER)
        tok_box.pack(fill="x", pady=(6, 10))

        self._tok_var = tk.StringVar(value="—")
        self._tok_lbl = tk.Label(tok_box, textvariable=self._tok_var,
                                 font=FM(9), bg=TOKEN_BG, fg=FG3,
                                 anchor="w", padx=10, pady=8)
        self._tok_lbl.pack(fill="x")

        # botões
        row = tk.Frame(cpad, bg=CARD)
        row.pack(fill="x")

        self._btn_ref = tk.Label(row, text="↻", font=F(13),
                                 bg=SURFACE, fg=FG2, width=3,
                                 cursor="hand2", pady=5)
        self._btn_ref.pack(side="left", padx=(0, 8))
        self._btn_ref.bind("<Button-1>", lambda e: self._refresh())
        self._btn_ref.bind("<Enter>", lambda e: self._btn_ref.config(fg=BLUE, bg=BORDER))
        self._btn_ref.bind("<Leave>", lambda e: self._btn_ref.config(fg=FG2, bg=SURFACE))

        self._btn_copy = tk.Label(row, text="Copiar Token", font=F(9, "bold"),
                                  bg=BLUE_BTN, fg="white", cursor="hand2",
                                  padx=14, pady=6)
        self._btn_copy.pack(side="left", fill="x", expand=True)
        self._btn_copy.bind("<Button-1>", lambda e: self._copy())
        self._btn_copy.bind("<Enter>", lambda e: self._btn_copy.config(bg=BLUE_HOV))
        self._btn_copy.bind("<Leave>", lambda e: self._btn_copy.config(bg=BLUE_BTN))

        # ── Auto refresh ──────────────────────────────────────────────────────
        auto = tk.Frame(pad, bg=BG)
        auto.pack(fill="x", pady=(12, 0))

        self._sw = tk.Canvas(auto, width=34, height=18, bg=BG,
                             highlightthickness=0, cursor="hand2")
        self._sw.pack(side="left")
        self._draw_sw(False)
        self._sw.bind("<Button-1>", self._toggle_auto)

        tk.Label(auto, text="Atualização automática", font=F(8),
                 bg=BG, fg=FG2).pack(side="left", padx=(8, 0))

        # ── Dica ──────────────────────────────────────────────────────────────
        tk.Label(pad, text="Conecte-se ao servidor antes de extrair",
                 font=F(7), bg=BG, fg=FG3).pack(anchor="w", pady=(8, 0))

    # ── Switch ────────────────────────────────────────────────────────────────
    def _draw_sw(self, on):
        self._sw.delete("all")
        col = BLUE if on else BORDER_HI
        self._sw.create_oval(0, 0, 18, 18, fill=col, outline="")
        self._sw.create_oval(16, 0, 34, 18, fill=col, outline="")
        self._sw.create_rectangle(9, 0, 25, 18, fill=col, outline="")
        if on:
            self._sw.create_oval(17, 2, 33, 16, fill=FG, outline="")
        else:
            self._sw.create_oval(1, 2, 17, 16, fill=FG2, outline="")

    def _toggle_auto(self, _=None):
        self._auto = not self._auto
        self._draw_sw(self._auto)
        if self._auto:
            self._auto_loop()
        elif self._auto_job:
            self.after_cancel(self._auto_job)
            self._auto_job = None

    def _auto_loop(self):
        if not self._auto:
            return
        self._refresh()
        self._auto_job = self.after(4000, self._auto_loop)

    # ── Status ────────────────────────────────────────────────────────────────
    def _set_status(self, text, fg=FG3, dot=FG3):
        self._status.config(text=text, fg=fg)
        self._dot.delete("all")
        self._dot.create_oval(0, 0, 7, 7, fill=dot, outline="")

    # ── Ações ─────────────────────────────────────────────────────────────────
    def _refresh(self):
        if self._busy:
            return
        self._busy = True
        self._set_status("Buscando...", BLUE, BLUE)
        self._btn_ref.config(fg=FG3)
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        tok = extract_token()
        self.after(0, self._done, tok)

    def _done(self, tok):
        self._busy = False
        self._btn_ref.config(fg=FG2)
        if tok:
            self._token = tok
            self._tok_var.set(tok)
            self._tok_lbl.config(fg=GREEN)
            self._set_status("Conectado", GREEN, GREEN)
        else:
            self._token = None
            self._tok_var.set("—")
            self._tok_lbl.config(fg=FG3)
            self._set_status("Jogo não encontrado", RED, RED)

    def _copy(self):
        if not self._token:
            self._btn_copy.config(text="Vazio", bg=RED)
            self.after(1100, lambda: self._btn_copy.config(text="Copiar Token", bg=BLUE_BTN))
            return
        self.clipboard_clear()
        self.clipboard_append(self._token)
        self._btn_copy.config(text="Copiado!", bg=GREEN)
        self.after(1100, lambda: self._btn_copy.config(text="Copiar Token", bg=BLUE_BTN))


if __name__ == "__main__":
    App().mainloop()