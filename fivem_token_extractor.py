import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import asyncio
import re
import requests
import os
import json

try:
    import pyshark
    PYSHARK_AVAILABLE = True
except ImportError:
    PYSHARK_AVAILABLE = False

# ──────────────────────────────────────────────
# Core logic
# ──────────────────────────────────────────────

TOKEN_REGEX = r"X-CitizenFX-Token:\s*([a-f0-9\-]{36})"


def is_direct_ip(string):
    pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$'
    return re.match(pattern, string) is not None


def resolve_cfx(cfx):
    if is_direct_ip(cfx):
        return cfx
    if "cfx.re/join/" not in cfx:
        cfx = f"cfx.re/join/{cfx}"
    try:
        r = requests.get(f"https://{cfx}", timeout=10)
        if r.status_code != 200:
            return None
        response = r.headers.get('x-citizenfx-url', '')
        return response.strip("https://")
    except requests.RequestException:
        return None


def remove_ansi(text):
    return re.compile(r'\x1b\[([0-9]{1,2})(;[0-9]{1,2})?m').sub('', text)


def clean_data(data):
    data = remove_ansi(data)
    data = re.sub(r'[\x00-\x1F\x7F]+', '', data)
    return re.sub(r'\r\n|\n', '\n', data).strip()


# ──────────────────────────────────────────────
# GUI
# ──────────────────────────────────────────────

BG       = "#0d0f14"
PANEL    = "#13161e"
ACCENT   = "#00e5ff"
ACCENT2  = "#7c3aed"
SUCCESS  = "#22c55e"
WARNING  = "#f59e0b"
DANGER   = "#ef4444"
FG       = "#e2e8f0"
FG_DIM   = "#64748b"
BORDER   = "#1e2433"
FONT_MONO = ("Consolas", 10)
FONT_UI   = ("Segoe UI", 10)
FONT_H    = ("Segoe UI Semibold", 11)


class TokenExtractorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FiveM Token Extractor")
        self.geometry("780x560")
        self.resizable(False, False)
        self.configure(bg=BG)

        self._capture_thread = None
        self._stop_flag = threading.Event()

        # Style combobox
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=PANEL, background=PANEL,
                        foreground=FG, selectbackground=ACCENT2,
                        selectforeground=FG, bordercolor=BORDER,
                        arrowcolor=ACCENT)

        self._build_ui()

    # ── Build ──────────────────────────────────

    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=PANEL, height=54)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⬡  FiveM Token Extractor",
                 font=("Segoe UI Semibold", 13), bg=PANEL,
                 fg=ACCENT).pack(side="left", padx=20, pady=14)
        tk.Label(hdr, text="Mineração de Dados · UFABC",
                 font=("Segoe UI", 9), bg=PANEL,
                 fg=FG_DIM).pack(side="right", padx=20)

        sep = tk.Frame(self, bg=ACCENT2, height=2)
        sep.pack(fill="x")

        # ── Body ──
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=18)

        # Left column
        left = tk.Frame(body, bg=BG, width=320)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        self._section(left, "1 · Servidor FiveM")
        self._label(left, "CFX Code ou IP:Porta")
        self.entry_cfx = self._entry(left, "Ex: abc123  ou  192.168.1.1:30120")

        self._section(left, "2 · Interface de Rede")
        self._label(left, "Selecione a interface")
        self.iface_var = tk.StringVar()
        iface_names = self._get_interfaces()
        self.combo_iface = ttk.Combobox(
            left, textvariable=self.iface_var,
            values=iface_names, state="readonly",
            font=FONT_UI
        )
        self.combo_iface.pack(fill="x", ipady=5, pady=(2, 0))
        if iface_names:
            self.combo_iface.current(0)

        self._section(left, "3 · Captura")
        self.btn_start = self._button(left, "▶  Iniciar Captura",
                                      ACCENT, BG, self._start)
        tk.Frame(left, bg=BG, height=6).pack()
        self.btn_stop = self._button(left, "■  Parar",
                                     DANGER, "#fff", self._stop,
                                     state="disabled")

        # Status badge
        tk.Frame(left, bg=BG, height=14).pack()
        self.status_var = tk.StringVar(value="Aguardando…")
        self.status_lbl = tk.Label(left, textvariable=self.status_var,
                                   font=("Segoe UI", 9, "italic"),
                                   bg=BG, fg=FG_DIM)
        self.status_lbl.pack(anchor="w")

        # Divider
        tk.Frame(body, bg=BORDER, width=1).pack(side="left",
                                                fill="y", padx=18)

        # Right column – log + token
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Log de Captura",
                 font=FONT_H, bg=BG, fg=FG).pack(anchor="w")

        self.log = scrolledtext.ScrolledText(
            right, font=FONT_MONO, bg=PANEL, fg=FG,
            insertbackground=ACCENT, relief="flat",
            borderwidth=0, height=14, wrap="word",
            state="disabled"
        )
        self.log.pack(fill="both", expand=True, pady=(6, 14))
        self.log.tag_config("ok",      foreground=SUCCESS)
        self.log.tag_config("warn",    foreground=WARNING)
        self.log.tag_config("err",     foreground=DANGER)
        self.log.tag_config("info",    foreground=ACCENT)
        self.log.tag_config("dim",     foreground=FG_DIM)

        # Token box
        tk.Label(right, text="Token Capturado",
                 font=FONT_H, bg=BG, fg=FG).pack(anchor="w")

        token_frame = tk.Frame(right, bg=PANEL,
                               highlightbackground=ACCENT2,
                               highlightthickness=1)
        token_frame.pack(fill="x", pady=(4, 0))

        self.token_var = tk.StringVar(value="—")
        tk.Label(token_frame, textvariable=self.token_var,
                 font=("Consolas", 11), bg=PANEL, fg=SUCCESS,
                 padx=12, pady=10).pack(side="left", fill="x", expand=True)

        self._button(token_frame, "Copiar", ACCENT2, "#fff",
                     self._copy_token, padx=12, pady=6).pack(side="right",
                                                              padx=8, pady=6)

    # ── Helpers ───────────────────────────────

    def _get_interfaces(self):
        try:
            import psutil
            return list(psutil.net_if_addrs().keys())
        except ImportError:
            return ["psutil não instalado"]

    def _section(self, parent, text):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(14, 2))
        tk.Label(f, text=text, font=("Segoe UI Semibold", 9),
                 bg=BG, fg=ACCENT2).pack(side="left")
        tk.Frame(f, bg=BORDER, height=1).pack(side="left",
                                              fill="x", expand=True, padx=(8, 0), pady=6)

    def _label(self, parent, text):
        tk.Label(parent, text=text, font=("Segoe UI", 9),
                 bg=BG, fg=FG_DIM).pack(anchor="w", pady=(2, 0))

    def _entry(self, parent, placeholder=""):
        e = tk.Entry(parent, font=FONT_UI, bg=PANEL, fg=FG,
                     insertbackground=ACCENT, relief="flat",
                     borderwidth=0, highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=ACCENT)
        e.pack(fill="x", ipady=7, pady=(2, 0))
        if placeholder:
            e.insert(0, placeholder)
            e.config(fg=FG_DIM)
            e.bind("<FocusIn>",  lambda ev, en=e, ph=placeholder: self._ph_clear(ev, en, ph))
            e.bind("<FocusOut>", lambda ev, en=e, ph=placeholder: self._ph_restore(ev, en, ph))
        return e

    def _ph_clear(self, _, entry, ph):
        if entry.get() == ph:
            entry.delete(0, "end")
            entry.config(fg=FG)

    def _ph_restore(self, _, entry, ph):
        if not entry.get():
            entry.insert(0, ph)
            entry.config(fg=FG_DIM)

    def _button(self, parent, text, bg, fg, cmd,
                state="normal", padx=0, pady=0):
        b = tk.Button(parent, text=text, font=FONT_H,
                      bg=bg, fg=fg, activebackground=bg,
                      activeforeground=fg, relief="flat",
                      cursor="hand2", command=cmd, state=state,
                      padx=padx or 16, pady=pady or 8)
        b.pack(fill="x" if not padx else None)
        return b

    # ── Logging ───────────────────────────────

    def _log(self, msg, tag=""):
        self.log.config(state="normal")
        prefix = {"ok": "✔ ", "err": "✘ ", "warn": "⚠ ",
                  "info": "» ", "dim": "  "}.get(tag, "  ")
        self.log.insert("end", prefix + msg + "\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")

    def _set_status(self, msg, color=FG_DIM):
        self.status_var.set(msg)
        self.status_lbl.config(fg=color)

    # ── Actions ───────────────────────────────

    def _copy_token(self):
        token = self.token_var.get()
        if token and token != "—":
            self.clipboard_clear()
            self.clipboard_append(token)
            self._log("Token copiado para a área de transferência.", "dim")

    def _start(self):
        if not PYSHARK_AVAILABLE:
            self._log("pyshark não encontrado. Instale: pip install pyshark", "err")
            return

        cfx_raw   = self.entry_cfx.get().strip()
        iface_raw = self.iface_var.get().strip()

        if not cfx_raw or cfx_raw == "Ex: abc123  ou  192.168.1.1:30120":
            self._log("Preencha o CFX / IP do servidor.", "warn")
            return
        if not iface_raw or iface_raw == "psutil não instalado":
            self._log("Selecione uma interface de rede válida.", "warn")
            return

        self._stop_flag.clear()
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self._set_status("Resolvendo servidor…", WARNING)
        self._log(f"Resolvendo: {cfx_raw}", "info")

        self._capture_thread = threading.Thread(
            target=self._run_capture,
            args=(cfx_raw, iface_raw),
            daemon=True
        )
        self._capture_thread.start()

    def _stop(self):
        self._stop_flag.set()
        self._set_status("Captura interrompida.", DANGER)
        self._log("Captura interrompida pelo usuário.", "warn")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")

    def _run_capture(self, cfx_raw, iface):
        resolved = resolve_cfx(cfx_raw)
        if not resolved:
            self.after(0, self._log,
                       "Não foi possível resolver o servidor. Verifique o CFX.", "err")
            self.after(0, self._set_status, "Erro na resolução.", DANGER)
            self.after(0, self.btn_start.config, {"state": "normal"})
            self.after(0, self.btn_stop.config,  {"state": "disabled"})
            return

        if ":" not in resolved:
            self.after(0, self._log, "Formato inválido retornado pelo servidor.", "err")
            return

        ip, port = resolved.split(":", 1)
        self.after(0, self._log, f"IP resolvido: {ip}:{port}", "ok")
        self.after(0, self._set_status, "Aguardando conexão…", ACCENT)

        asyncio.set_event_loop(asyncio.new_event_loop())
        try:
            capture = pyshark.LiveCapture(
                interface=iface,
                display_filter=f'http and ip.addr == {ip} and tcp.port == {port}'
            )
            for packet in capture.sniff_continuously():
                if self._stop_flag.is_set():
                    capture.close()
                    break
                try:
                    if 'HTTP' in packet:
                        http_layer = packet['HTTP']
                        raw = clean_data(str(http_layer))
                        match = re.search(TOKEN_REGEX, raw)
                        if match:
                            token = match.group(1)
                            tokens = {"X-CitizenFX-Token": token}
                            with open("tokens.json", "w") as f:
                                json.dump(tokens, f, indent=4)
                            capture.close()
                            self.after(0, self._on_token_found, token)
                            break
                except Exception as e:
                    self.after(0, self._log, f"Erro no pacote: {e}", "err")
        except Exception as e:
            self.after(0, self._log, f"Erro na captura: {e}", "err")
            self.after(0, self._set_status, "Erro na captura.", DANGER)

        self.after(0, self.btn_start.config, {"state": "normal"})
        self.after(0, self.btn_stop.config,  {"state": "disabled"})

    def _on_token_found(self, token):
        self.token_var.set(token)
        self._log(f"Token encontrado e salvo em tokens.json!", "ok")
        self._set_status("Token capturado com sucesso.", SUCCESS)
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")


# ──────────────────────────────────────────────

if __name__ == "__main__":
    app = TokenExtractorApp()
    app.mainloop()
