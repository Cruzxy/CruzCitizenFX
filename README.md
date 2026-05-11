<p align="center">
  <img src="./logo.png" alt="Cruz Token Extractor" width="96" height="96">
</p>

<h1 align="center">Cruz Token Extractor</h1>

<p align="center">
  Utilitario desktop para diagnostico local de sessoes CitizenFX/FiveM em ambiente Windows.
</p>

<p align="center">
  <a href="https://github.com/Cruzxy/CruzCitizenFX">
    <img alt="Repository" src="https://img.shields.io/badge/repo-CruzCitizenFX-3d7ef5">
  </a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Windows-lightgrey">
  <img alt="Interface" src="https://img.shields.io/badge/ui-Tkinter-1ec97c">
</p>

## Visao Geral

Cruz Token Extractor e uma aplicacao desktop em Python com interface grafica compacta, pensada para uso local em rotinas de desenvolvimento, teste e diagnostico. A aplicacao identifica processos FiveM/CitizenFX em execucao, executa a leitura local de memoria quando autorizada pelo sistema e apresenta o resultado em uma interface escura, responsiva e orientada a fluxo de trabalho.

O projeto prioriza uma experiencia simples: uma acao principal, logs visiveis em tempo real, status de ambiente e copia rapida do valor encontrado.

> [!IMPORTANT]
> Este projeto deve ser usado somente em ambientes proprios, autorizados e para fins legitimos de desenvolvimento, teste ou depuracao. Nao utilize a ferramenta para acessar, coletar ou compartilhar dados de terceiros sem permissao.

## Recursos

- Interface desktop nativa com Tkinter.
- Tema escuro com componentes compactos para uso tecnico.
- Console integrado com logs em tempo real.
- Execucao em background para manter a interface responsiva.
- Deteccao de dependencia `pymem` e permissao de administrador.
- Suporte a icone do aplicativo em desenvolvimento e build.
- Stack de fontes com foco SaaS/dev: `Inter`, `Aptos`, `Segoe UI`, `JetBrains Mono` e `Cascadia Code`, conforme disponibilidade no sistema.

## Requisitos

- Windows 10 ou superior.
- Python 3.10 ou superior.
- Permissao de administrador para leitura local de memoria de processos.
- Dependencias Python:
  - `pymem`
  - `Pillow` para carregar o icone na interface.
  - `pyinstaller` apenas para gerar o executavel.

## Instalacao

Clone o repositorio:

```bash
git clone https://github.com/Cruzxy/CruzCitizenFX.git
cd CruzCitizenFX
```

Instale as dependencias:

```bash
pip install pymem Pillow
```

Execute em modo desenvolvimento:

```bash
python main.py
```

A aplicacao tentara reiniciar com permissao de administrador quando necessario.

## Build Local

Para gerar o executavel Windows:

```bash
pip install pyinstaller
python -m PyInstaller --onefile --noconsole --uac-admin --add-data "logo.ico;." --name "CruzTokenExtractor" --icon="logo.ico" main.py
```

O arquivo gerado ficara em:

```text
dist/CruzTokenExtractor.exe
```

## Estrutura

```text
CruzCitizenFX/
|-- main.py
|-- logo.png
|-- logo.ico
|-- CruzTokenExtractor.spec
|-- README.md
|-- build/
`-- dist/
```

## Tecnologias

- Python
- Tkinter
- Pymem
- Pillow
- PyInstaller
- Windows API via `ctypes`

## Boas Praticas

- Use apenas em maquinas e sessoes sob sua responsabilidade.
- Nao compartilhe valores sensiveis obtidos durante diagnosticos.
- Revise o codigo antes de executar binarios gerados por terceiros.
- Gere builds localmente quando precisar validar integridade.

## Licenca

Este projeto esta licenciado sob a licenca MIT. Consulte o arquivo [LICENSE](./LICENSE) para mais detalhes.
