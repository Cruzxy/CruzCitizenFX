# ⬡ Cruz Token Extractor

![GitHub License](https://img.shields.io/github/license/dxdjo/CruzCitizenFX)
![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey.svg)

Uma ferramenta de alto desempenho com interface gráfica (GUI) moderna, projetada para a extração instantânea do `X-CitizenFX-Token` diretamente da memória dos processos do FiveM. 

Ao contrário de extratores baseados em captura de pacotes, esta ferramenta realiza uma varredura cirúrgica nos módulos de memória, garantindo precisão e velocidade sem a necessidade de drivers de rede complexos (como Npcap).

## ✨ Funcionalidades

- **Varredura de Memória Otimizada**: Localização automática dos processos `FiveM.exe`, `FiveM_GTAProcess.exe` ou `CitizenFX.exe`.
- **Interface Premium**: Design escuro e moderno construído com Tkinter, incluindo animações de shimmer (GlowBar) e feedback visual em tempo real.
- **Terminal Integrado**: Acompanhe cada etapa do processo de extração através de um console detalhado na interface.
- **Cópia Instantânea**: Botão dedicado para copiar o token extraído para a área de transferência com um clique.
- **Detecção de Ambiente**: Verificação automática de dependências e permissões de administrador.
- **Estilo Adaptativo**: Utiliza as melhores fontes disponíveis no sistema (Inter, Segoe UI Variable) para uma experiência visual superior.

## 🚀 Como Começar

### Pré-requisitos

Para garantir o funcionamento correto, você precisará de:

1. **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
2. **Privilégios de Administrador**: A ferramenta requer permissões elevadas para ler a memória de processos protegidos.
3. **Windows**: Otimizado para sistemas Windows.

### Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/dxdjo/CruzCitizenFX.git
   cd CruzCitizenFX
   ```

2. Instale a dependência principal:
   ```bash
   pip install pymem
   ```

## 🛠️ Uso

### Executando o Script

Para iniciar a ferramenta:
```bash
python main.py
```
*A aplicação solicitará permissão de administrador automaticamente ao iniciar.*

### Gerando o Executável (.exe)

Se desejar compilar o projeto para um arquivo executável único:

1. Instale o PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Execute o comando de build:
   ```bash
    python -m PyInstaller --onefile --noconsole --uac-admin --name "CruzTokenExtractor" --icon="logo.ico" main.py
   ```
3. O arquivo final estará disponível na pasta `dist/`.

## 🧪 Tecnologias Utilizadas

- **[Pymem](https://github.com/n4ze2/pymem)**: Manipulação e varredura de memória de processos.
- **Tkinter**: Interface gráfica nativa e veloz.
- **Threading**: Processamento em background para manter a UI responsiva.
- **Ctypes**: Integração com a API do Windows para controle de privilégios.


---

> [!WARNING]
> **Aviso Ético**: Esta ferramenta deve ser utilizada exclusivamente para fins de teste, desenvolvimento e depuração de suas próprias conexões. O uso indevido para violar termos de serviço de terceiros é de total responsabilidade do usuário.

