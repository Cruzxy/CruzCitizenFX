import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import re
import requests
import os
import json
import time
import math
import sys
import ctypes

# ==================== FORÇAR ADMINISTRADOR ====================
def run_as_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    try:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)
    except:
        print("❌ Falha ao solicitar privilégios de administrador.")
        return False

if not run_as_admin():
    print("Este programa precisa ser executado como Administrador!")
    input("Pressione ENTER para sair...")
    sys.exit(1)

# ==================== DEPENDÊNCIAS ====================
try:
    import pymem
    PYMEM_AVAILABLE = True
except ImportError:
    PYMEM_AVAILABLE = False

try:
    import pyshark
    PYSHARK_AVAILABLE = True
except ImportError:
    PYSHARK_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ──────────────────────────────────────────────
# Core
# ──────────────────────────────────────────────

TOKEN_REGEX = r"X-CitizenFX-Token:\s*([a-f0-9\-]{36})"

def is_direct_ip(string):
    return re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$', string) is not None

def resolve_cfx(cfx):
    if is_direct_ip(cfx):
        return cfx
    if "cfx.re/join/" not in cfx:
        cfx = f"cfx.re/join/{cfx}"
    try:
        r = requests.get(f"https://{cfx}", timeout=10)
        return r.headers.get('x-citizenfx-url', '').strip("https://") or None
    except:
        return None

def remove_ansi(text):
    return re.compile(r'\x1b\[([0-9]{1,2})(;[0-9]{1,2})?m').sub('', text)

def clean_data(data):
    data = remove_ansi(data)
    data = re.sub(r'[\x00-\x1F\x7F]+', '', data)
    return re.sub(r'\r\n|\n', '\n', data).strip()

# ──────────────────────────────────────────────
# Extração via Memória
# ──────────────────────────────────────────────

def extract_token_from_process(log_callback):
    if not PYMEM_AVAILABLE:
        log_callback("pymem não instalado.", "err")
        return None

    try:
        log_callback("Procurando processos FiveM...", "info")
        
        process_names = ["FiveM.exe", "FiveM_GTAProcess.exe", "CitizenFX.exe"]
        pm = None
        process_name_used = None

        for name in process_names:
            try:
                pm = pymem.Pymem(name)
                process_name_used = name
                log_callback(f"✅ Conectado ao: {name}", "ok")
                break
            except:
                continue

        if not pm:
            log_callback("❌ Nenhum processo FiveM encontrado.", "err")
            return None

        log_callback("Escaneando memória (padrões múltiplos)...", "info")

        # === PADRÕES MELHORADOS ===
        patterns = [
            rb"X-CitizenFX-Token[^\x00-\x7F]{0,80}?([a-f0-9-]{36})",   # Padrão principal
            rb"X-CitizenFX-Token[:=]\s*([a-f0-9-]{36})",
            rb"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})",  # UUID puro
            rb"token[^\x00-\x7F]{0,100}?([a-f0-9-]{36})",
        ]

        # Scan em módulos grandes primeiro
        found_token = None
        for module in pm.list_modules():
            try:
                if module.SizeOfImage < 1000000:  # pula módulos pequenos
                    continue
                    
                log_callback(f"Verificando módulo: {module.name} ({module.SizeOfImage//1024//1024} MB)", "dim")
                
                data = pm.read_bytes(module.lpBaseOfDll, min(module.SizeOfImage, 120000000))
                
                for pattern in patterns:
                    for match in re.finditer(pattern, data, re.IGNORECASE):
                        token = match.group(1).decode('ascii', errors='ignore').strip()
                        if len(token) == 36 and token.count('-') == 4:
                            found_token = token
                            log_callback(f"✅ TOKEN ENCONTRADO em {module.name}!", "ok")
                            return found_token
            except:
                continue

        # Fallback: scan geral com pymem (mais lento)
        if not found_token:
            log_callback("Fazendo scan geral completo...", "warn")
            for pattern in patterns:
                try:
                    results = pymem.pattern.pattern_scan_all(pm.process_handle, pattern, return_multiple=True)
                    for addr in results[:10]:  # limita para não travar
                        try:
                            data = pm.read_bytes(max(0, addr-80), 200)
                            for p in patterns:
                                m = re.search(p, data, re.IGNORECASE)
                                if m:
                                    token = m.group(1).decode('ascii', errors='ignore').strip()
                                    if len(token) == 36 and token.count('-') == 4:
                                        return token
                        except:
                            continue
                except:
                    continue

        log_callback("❌ Token não encontrado após scan completo.", "warn")
        log_callback("Dica: Tente reconectar no servidor e tentar novamente.", "dim")
        return None

    except Exception as e:
        log_callback(f"Erro crítico: {e}", "err")
        return None


# ──────────────────────────────────────────────
# Cores e Fontes
# ──────────────────────────────────────────────
BG_BASE = "#0a0c10"
BG_SURFACE = "#0f1117"
BG_RAISED = "#151820"
BG_HOVER = "#1c2030"
BORDER = "#1e2433"
ACCENT = "#00d4ff"
SUCCESS = "#10b981"
DANGER = "#f43f5e"
FG = "#e8eaf2"
FG_MED = "#8892a4"
FG_DIM = "#4a5568"

FONT_MONO = ("Consolas", 9)
FONT_UI = ("Segoe UI", 10)
FONT_SML = ("Segoe UI", 9)
FONT_H3 = ("Segoe UI Semibold", 10)

# ──────────────────────────────────────────────
# Widgets (resumidos)
# ──────────────────────────────────────────────

class PulsingDot(tk.Canvas):
    def __init__(self, parent, color=ACCENT, size=8, **kw):
        super().__init__(parent, width=size+4, height=size+4, bg=BG_BASE, highlightthickness=0, **kw)
        self._color = color
        self._size = size
        self._step = 0
        self._running = False
        self._draw(1.0)

    def _draw(self, alpha):
        self.delete("all")
        s = self._size; pad=2; r=s//2; cx=pad+r; cy=pad+r
        self.create_oval(cx-r, cy-r, cx+r, cy+r, fill=self._color, outline="")

    def pulse(self, color=None):
        if color: self._color = color
        self._running = True
        self._animate()

    def _animate(self):
        if not self._running: return
        self._step = (self._step + 0.15) % (2 * math.pi)
        self._draw((math.sin(self._step) + 1) / 2)
        self.after(50, self._animate)

    def solid(self, color=None):
        self._running = False
        if color: self._color = color
        self._draw(1.0)


class GlowButton(tk.Frame):
    def __init__(self, parent, text, command, style="primary", **kw):
        super().__init__(parent, bg=BG_BASE, **kw)
        self._cmd = command
        colors = {
            "primary": ("#0a1f2e", "#0d2a3d", ACCENT, ACCENT),
            "danger": ("#1a0812", "#240d18", DANGER, DANGER)
        }
        self._bg, self._bg_h, self._fg, self._border = colors.get(style, (BG_RAISED, BG_HOVER, FG, BORDER))

        outer = tk.Frame(self, bg=self._border, padx=1, pady=1)
        outer.pack(fill="x")
        inner = tk.Frame(outer, bg=self._bg)
        inner.pack(fill="x")
        self._btn = tk.Button(inner, text=text, font=FONT_H3, bg=self._bg, fg=self._fg,
                              activebackground=self._bg_h, relief="flat", cursor="hand2", pady=8, command=self._click)
        self._btn.pack(fill="x")

    def _click(self):
        if str(self._btn.cget("state")) != "disabled":
            self._cmd()

    def set_state(self, state):
        self._btn.config(state=state)


class ModernEntry(tk.Frame):
    def __init__(self, parent, placeholder="", **kw):
        super().__init__(parent, bg=BG_BASE, **kw)
        self._ph = placeholder
        self._border = tk.Frame(self, bg=BORDER, padx=1, pady=1)
        self._border.pack(fill="x")
        inner = tk.Frame(self._border, bg=BG_RAISED)
        inner.pack(fill="x")
        self.entry = tk.Entry(inner, font=FONT_UI, bg=BG_RAISED, fg=FG_DIM, relief="flat")
        self.entry.pack(fill="x", padx=10, pady=8)
        if placeholder:
            self.entry.insert(0, placeholder)
        self.entry.bind("<FocusIn>", self._on_focus)
        self.entry.bind("<FocusOut>", self._on_blur)

    def _on_focus(self, _=None):
        self._border.config(bg=ACCENT)
        if self.entry.get() == self._ph:
            self.entry.delete(0, "end")
            self.entry.config(fg=FG)

    def _on_blur(self, _=None):
        self._border.config(bg=BORDER)
        if not self.entry.get():
            self.entry.insert(0, self._ph)
            self.entry.config(fg=FG_DIM)

    def get(self):
        val = self.entry.get()
        return "" if val == self._ph else val


class StatusBar(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG_SURFACE, height=34, **kw)
        self.pack_propagate(False)
        left = tk.Frame(self, bg=BG_SURFACE)
        left.pack(side="left", fill="y", padx=16)
        self._dot = PulsingDot(left)
        self._dot.pack(side="left", pady=10)
        self._msg = tk.StringVar(value="Pronto")
        tk.Label(left, textvariable=self._msg, bg=BG_SURFACE, fg=FG_MED).pack(side="left", padx=8)

    def set(self, msg, state="idle"):
        self._msg.set(msg)
        if state == "running": self._dot.pulse(ACCENT)
        elif state == "ok": self._dot.solid(SUCCESS)
        elif state == "error": self._dot.solid(DANGER)


class LogView(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG_SURFACE, **kw)
        self.text = scrolledtext.ScrolledText(self, font=FONT_MONO, bg=BG_BASE, fg=FG, state="disabled")
        self.text.pack(fill="both", expand=True)

    def log(self, msg, tag="dim"):
        self.text.config(state="normal")
        self.text.insert("end", f"{time.strftime('%H:%M:%S')} | {msg}\n")
        self.text.see("end")
        self.text.config(state="disabled")

    def clear(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")


class TokenDisplay(tk.Frame):
    def __init__(self, parent, on_copy, **kw):
        super().__init__(parent, bg=BG_SURFACE, **kw)
        self._on_copy = on_copy
        tk.Label(self, text="TOKEN CAPTURADO", bg=BG_SURFACE, fg=FG_DIM).pack(anchor="w", padx=14, pady=8)
        self._token_var = tk.StringVar(value="aguardando...")
        self._lbl = tk.Label(self, textvariable=self._token_var, font=("Consolas", 11), bg=BG_RAISED, fg=FG_DIM, anchor="w")
        self._lbl.pack(fill="x", padx=14, pady=8)
        tk.Button(self, text="Copiar", command=on_copy, bg=ACCENT, fg="black").pack(pady=5)

    def set_token(self, token):
        self._token_var.set(token)
        self._lbl.config(fg=SUCCESS)

    def get_token(self):
        return self._token_var.get()


# ──────────────────────────────────────────────
# Aplicação Principal
# ──────────────────────────────────────────────

class TokenExtractorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FiveM Token Extractor - v2.1")
        self.geometry("880x660")
        self.configure(bg=BG_BASE)

        self._stop_flag = threading.Event()
        self._build_ui()

        self._log("Sistema iniciado.", "dim")
        if not PYMEM_AVAILABLE:
            self._log("Instale pymem: pip install pymem", "warn")

    def _build_ui(self):
        # Sidebar
        side = tk.Frame(self, bg=BG_SURFACE, width=280)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        pad = tk.Frame(side, bg=BG_SURFACE)
        pad.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(pad, text="SERVIDOR", font=("Consolas", 9, "bold"), bg=BG_SURFACE, fg=ACCENT).pack(anchor="w")
        self._cfx_entry = ModernEntry(pad, placeholder="abc123 ou IP:Porta")
        self._cfx_entry.pack(fill="x", pady=8)

        tk.Label(pad, text="CAPTURA", font=("Consolas", 9, "bold"), bg=BG_SURFACE, fg=ACCENT).pack(anchor="w", pady=(15,5))

        GlowButton(pad, "▶ Captura via Rede", self._start, "primary").pack(fill="x", pady=4)
        GlowButton(pad, "🔍 Extrair da Memória", self._extract_from_memory, "primary").pack(fill="x", pady=4)
        GlowButton(pad, "■ Parar", self._stop, "danger").pack(fill="x", pady=4)

        # Área principal
        main = tk.Frame(self, bg=BG_BASE)
        main.pack(side="right", fill="both", expand=True)

        self._logview = LogView(main)
        self._logview.pack(fill="both", expand=True, padx=10, pady=10)

        self._token_display = TokenDisplay(main, on_copy=self._copy_token)
        self._token_display.pack(fill="x", padx=10, pady=10)

        self._statusbar = StatusBar(self)
        self._statusbar.pack(fill="x", side="bottom")

    def _log(self, msg, tag="dim"):
        self._logview.log(msg)

    def _set_status(self, msg, state="idle"):
        self._statusbar.set(msg, state)

    def _copy_token(self):
        token = self._token_display.get_token()
        if token and token != "aguardando...":
            self.clipboard_clear()
            self.clipboard_append(token)
            self._log("✅ Token copiado!")

    # ==================== MEMÓRIA ====================
    def _extract_from_memory(self):
        self._set_status("Escaneando memória...", "running")
        def worker():
            token = extract_token_from_process(self._log)
            self.after(0, self._finish_memory, token)
        threading.Thread(target=worker, daemon=True).start()

    def _finish_memory(self, token):
        if token:
            self._token_display.set_token(token)
            self._set_status("Token extraído com sucesso!", "ok")
            with open("tokens.json", "w") as f:
                json.dump({"X-CitizenFX-Token": token}, f, indent=4)
        else:
            self._set_status("Token não encontrado.", "error")

    def _start(self): 
        self._log("Funcionalidade de rede ainda em desenvolvimento...")
    def _stop(self):
        self._log("Parado pelo usuário.")

# ==================== EXECUÇÃO ====================
if __name__ == "__main__":
    app = TokenExtractorApp()
    app.mainloop()