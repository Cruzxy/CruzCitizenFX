import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import threading
import asyncio
import re
import requests
import json
import psutil

# Tentativa de importação do pyshark
try:
    import pyshark
    PYSHARK_AVAILABLE = True
except ImportError:
    PYSHARK_AVAILABLE = False

# --- Configurações de Design (Estilo SaaS/Vercel) ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg": "#0A0A0A",        # Fundo principal ultra dark
    "card": "#171717",      # Cards e containers
    "accent": "#0070F3",    # Azul Vercel
    "accent_hover": "#0051B3",
    "border": "#262626",    # Bordas sutis
    "text_main": "#EDEDED", # Texto principal
    "text_dim": "#888888",  # Texto secundário
    "success": "#00CC88",
    "danger": "#FF4D4D"
}

TOKEN_REGEX = r"X-CitizenFX-Token:\s*([a-f0-9\-]{36})"

# --- Lógica de Suporte ---
def resolve_cfx(cfx):
    pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$'
    if re.match(pattern, cfx):
        return cfx
    
    url = cfx if "cfx.re/join/" in cfx else f"cfx.re/join/{cfx}"
    try:
        r = requests.get(f"https://{url}", timeout=10)
        if r.status_code == 200:
            return r.headers.get('x-citizenfx-url', '').strip("https://")
    except:
        return None
    return None

# --- UI Principal ---
class ModernExtractor(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("FiveM Nexus · Token Extractor")
        self.geometry("900x620")
        self.configure(fg_color=COLORS["bg"])
        
        self._stop_flag = threading.Event()

        # Layout Grid: Sidebar (200px) | Main (Resto)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_main_content()

    def setup_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["card"], border_color=COLORS["border"], border_width=1)
        sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Logo/Título
        title_label = ctk.CTkLabel(sidebar, text="NEXUS", font=ctk.CTkFont(size=22, weight="bold", letter_spacing=2), text_color=COLORS["accent"])
        title_label.pack(pady=(30, 5))
        
        subtitle = ctk.CTkLabel(sidebar, text="FiveM Data Miner", font=ctk.CTkFont(size=11), text_color=COLORS["text_dim"])
        subtitle.pack(pady=(0, 30))

        # Inputs
        self.input_label = ctk.CTkLabel(sidebar, text="SERVER ADDRESS", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS["text_dim"])
        self.input_label.pack(anchor="w", padx=25)
        
        self.entry_cfx = ctk.CTkEntry(sidebar, placeholder_text="abc123...", height=40, fg_color=COLORS["bg"], border_color=COLORS["border"])
        self.entry_cfx.pack(fill="x", padx=20, pady=(5, 20))

        self.iface_label = ctk.CTkLabel(sidebar, text="NETWORK INTERFACE", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS["text_dim"])
        self.iface_label.pack(anchor="w", padx=25)
        
        interfaces = list(psutil.net_if_addrs().keys())
        self.combo_iface = ctk.CTkComboBox(sidebar, values=interfaces, height=40, fg_color=COLORS["bg"], border_color=COLORS["border"], button_color=COLORS["border"])
        self.combo_iface.pack(fill="x", padx=20, pady=(5, 30))

        # Action Buttons
        self.btn_start = ctk.CTkButton(sidebar, text="Start Capture", font=ctk.CTkFont(weight="bold"), fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], height=45, command=self.start_capture)
        self.btn_start.pack(fill="x", padx=20, pady=10)

        self.btn_stop = ctk.CTkButton(sidebar, text="Stop", font=ctk.CTkFont(weight="bold"), fg_color="transparent", border_color=COLORS["danger"], border_width=1, text_color=COLORS["danger"], hover_color="#331111", height=45, command=self.stop_capture, state="disabled")
        self.btn_stop.pack(fill="x", padx=20, pady=5)

    def setup_main_content(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        # Header da área principal
        header_frame = ctk.CTkFrame(main, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        self.status_indicator = ctk.CTkLabel(header_frame, text="● IDLE", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS["text_dim"])
        self.status_indicator.pack(side="left")

        # Log View
        log_container = ctk.CTkFrame(main, fg_color=COLORS["card"], border_color=COLORS["border"], border_width=1)
        log_container.grid(row=1, column=0, sticky="nsew")
        log_container.grid_columnconfigure(0, weight=1)
        log_container.grid_rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_container, background=COLORS["card"], foreground=COLORS["text_main"], borderwidth=0, font=("Consolas", 11), padx=15, pady=15, highlightthickness=0)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Token Display (Footer)
        token_container = ctk.CTkFrame(main, fg_color=COLORS["card"], border_color=COLORS["accent"], border_width=1, height=80)
        token_container.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        token_container.pack_propagate(False)

        ctk.CTkLabel(token_container, text="CAPTURED TOKEN", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS["accent"]).pack(anchor="w", padx=20, pady=(10, 0))
        
        self.token_var = tk.StringVar(value="Waiting for data...")
        self.token_label = ctk.CTkLabel(token_container, textvariable=self.token_var, font=ctk.CTkFont(family="Consolas", size=15), text_color=COLORS["text_main"])
        self.token_label.pack(side="left", padx=20, pady=(0, 10))

        self.copy_btn = ctk.CTkButton(token_container, text="Copy", width=80, height=30, fg_color=COLORS["border"], hover_color="#404040", command=self.copy_token)
        self.copy_btn.pack(side="right", padx=20, pady=(0, 10))

    # --- Funções de Interface ---
    def log(self, message, type="info"):
        prefix = "»" if type == "info" else "✖" if type == "err" else "✔"
        self.log_text.insert("end", f"{prefix} {message}\n")
        self.log_text.see("end")

    def copy_token(self):
        self.clipboard_clear()
        self.clipboard_append(self.token_var.get())
        self.log("Token copied to clipboard.", "success")

    def start_capture(self):
        if not PYSHARK_AVAILABLE:
            messagebox.showerror("Error", "pyshark not found. Run: pip install pyshark")
            return
        
        cfx = self.entry_cfx.get()
        iface = self.combo_iface.get()
        
        if not cfx:
            self.log("Please enter a server address.", "err")
            return

        self._stop_flag.clear()
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.status_indicator.configure(text="● RESOLVING", text_color=COLORS["accent"])
        
        threading.Thread(target=self.capture_worker, args=(cfx, iface), daemon=True).start()

    def stop_capture(self):
        self._stop_flag.set()
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_indicator.configure(text="● IDLE", text_color=COLORS["text_dim"])
        self.log("Capture stopped by user.", "info")

    def capture_worker(self, cfx, iface):
        resolved = resolve_cfx(cfx)
        if not resolved:
            self.after(0, lambda: self.log("Failed to resolve server.", "err"))
            self.after(0, self.stop_capture)
            return

        ip, port = resolved.split(":")
        self.after(0, lambda: self.log(f"Target: {ip}:{port}", "info"))
        self.after(0, lambda: self.status_indicator.configure(text="● SNIFFING", text_color=COLORS["success"]))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            cap = pyshark.LiveCapture(interface=iface, display_filter=f'http and ip.addr == {ip}')
            for packet in cap.sniff_continuously():
                if self._stop_flag.is_set():
                    break
                
                if 'HTTP' in packet:
                    raw = str(packet.http)
                    match = re.search(TOKEN_REGEX, raw)
                    if match:
                        token = match.group(1)
                        self.after(0, self.on_token_found, token)
                        break
            cap.close()
        except Exception as e:
            self.after(0, lambda: self.log(f"Capture Error: {str(e)[:50]}...", "err"))
        
        self.after(0, self.stop_capture)

    def on_token_found(self, token):
        self.token_var.set(token)
        self.token_label.configure(text_color=COLORS["success"])
        self.log("Token successfully extracted!", "success")
        
        with open("tokens.json", "w") as f:
            json.dump({"X-CitizenFX-Token": token}, f, indent=4)

if __name__ == "__main__":
    app = ModernExtractor()
    app.mainloop()