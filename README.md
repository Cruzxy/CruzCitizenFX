# ⬡ FiveM Token Extractor

![GitHub License](https://img.shields.io/github/license/dxdjo/CruzCitizenFX)
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)

Uma ferramenta gráfica (GUI) moderna e eficiente para captura e extração do `X-CitizenFX-Token` de conexões de servidores FiveM. Desenvolvido para facilitar a mineração de dados e depuração de conexões.

## ✨ Funcionalidades

- **Resolução Automática**: Suporte para CFX Code (ex: `abc123`) e IP:Porta.
- **Interface Intuitiva**: Interface gráfica construída com Tkinter, com design escuro e moderno.
- **Captura em Tempo Real**: Monitoramento de pacotes HTTP para identificar o token de autenticação.
- **Cópia Rápida**: Botão dedicado para copiar o token capturado para a área de transferência.
- **Logs Detalhados**: Acompanhamento do processo de captura e resolução diretamente na interface.
- **Persistência**: Salva o último token capturado em um arquivo `tokens.json`.

## 🚀 Como Começar

### Pré-requisitos

Para rodar ou compilar este projeto, você precisará de:

1. **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
2. **Npcap (ou Wireshark)**: Necessário para que o `pyshark` possa realizar a captura de pacotes.
   - [Baixar Npcap](https://nmap.org/npcap/) (Certifique-se de instalar com o suporte "WinPcap API-compatible mode" ativado).

### Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/dxdjo/CruzCitizenFX.git
   cd CruzCitizenFX
   ```

2. Instale as dependências necessárias:
   ```bash
   pip install pyshark requests colorama pyinstaller psutil
   ```

## 🛠️ Uso

### Executando via Script

Para iniciar a ferramenta diretamente pelo Python:
```bash
python fivem_token_extractor.py
```

### Gerando o Executável (.exe)

O projeto inclui um script automatizado para gerar uma versão standalone da aplicação:

1. Execute o arquivo `build_exe.bat`.
2. O script instalará as dependências e utilizará o `PyInstaller` para compilar o código.
3. O executável final estará disponível na pasta `dist/FivemTokenExtractor.exe`.

## 🧪 Tecnologias Utilizadas

- [Python](https://www.python.org/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - Interface Gráfica
- [PyShark](https://kiminewt.github.io/pyshark/) - Wrapper Python para TShark (Wireshark)
- [Requests](https://requests.readthedocs.io/) - Resolução de URLs CFX
- [Psutil](https://psutil.readthedocs.io/) - Identificação de interfaces de rede

## 🎓 Créditos

Este projeto foi desenvolvido como parte de estudos em **Mineração de Dados · UFABC**.

---
*Aviso: Use esta ferramenta de forma ética e apenas para fins de teste e desenvolvimento.*
