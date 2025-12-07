# party-uuid
Party-UUID é uma ferramenta gráfica multiplataforma (Linux e Windows) que detecta partições/discos, exibe UUID/UniqueId, sistema de arquivos e rótulo, e gera automaticamente linhas no formato boot=UUID=... disk=UUID=..., permitindo copiar ou salvar em .txt para uso em sistemas como AmberELEC e LibreELEC.

<img width="676" height="508" alt="Party-UUID-1" src="https://github.com/user-attachments/assets/7fdaf023-8746-438f-8668-03e519a10622" />

Party-UUID é uma ferramenta gráfica multiplataforma (Linux e Windows) para identificar partições e gerar rapidamente linhas no formato:

boot=UUID=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX disk=UUID=YYYYYYYY-YYYY-YYYY-YYYY-YYYYYYYYYYYY

text

Ela foi criada para facilitar a edição de `cmdline.txt` e parâmetros de kernel em sistemas como AmberELEC, LibreELEC e outras distribuições Linux em ARM, mas também é útil em qualquer cenário que envolva UUID de partições.

---

## ✨ Funcionalidades

- Interface gráfica moderna em **tema escuro** usando PyQt6.
- Detecta automaticamente o sistema operacional (**Linux** ou **Windows**).
- Lista partições/volumes com:
  - Dispositivo (`/dev/sda1`, `C:`, etc.).
  - UUID (Linux) ou UniqueId/Volume GUID (Windows).
  - Tipo de sistema de arquivos (ext4, vfat, NTFS, exFAT, …).
  - Rótulo (label), quando existir.
- Permite escolher qual partição será:
  - **BOOT** (partição de boot).
  - **DISK** (partição de dados / sistema).
- Gera a linha:
  - `boot=UUID=... disk=UUID=...`
- Ações rápidas:
  - **Atualizar** – relê as partições.
  - **Copiar** – copia a linha para a área de transferência.
  - **Salvar em .txt** – grava a linha em um arquivo de texto.
  - **Sair** – fecha o programa.

---

## 🧩 Como funciona

- Em **Linux**, o Party-UUID usa utilitários padrão como `lsblk`/`blkid` para obter UUID, tipo de filesystem e rótulo das partições.  
- Em **Windows**, usa comandos PowerShell (`Get-Partition` e `Get-Volume`) para ler DriveLetter, FileSystem, FileSystemLabel e UniqueId de cada volume.

> Observação: no Windows, o “UUID” exibido corresponde ao **UniqueId/Volume GUID** do volume, que não é idêntico ao UUID de filesystem do Linux, mas identifica o volume de forma única.

---

## ✅ Requisitos

### Comuns (Linux e Windows)

- **Python** 3.10 ou superior.
- **PyQt6** instalado:

pip install pyqt6

text

### Linux (Ubuntu, Linux Mint, derivados)

- Utilitários de disco:

sudo apt update
sudo apt install util-linux

text

Isso garante que `lsblk` e `blkid` estejam disponíveis para leitura dos UUIDs.

Em algumas distros, para ver todas as partições pode ser necessário rodar o programa com permissões elevadas (por exemplo, usando `sudo`).

### Windows 10 / 11

- Python instalado no Windows (não apenas no WSL).
- PowerShell disponível no PATH (padrão no sistema).

---

---

## 📜 Licença

Este projeto é distribuído sob a licença **MIT** (veja o arquivo `LICENSE`).

---

## ⚠️ Avisos

- Em Windows e Linux os identificadores exibidos têm representações diferentes; a linha `boot=UUID=... disk=UUID=...` é destinada principalmente a ambientes Linux (como cartões SD de dispositivos portáteis).  
- Sempre confirme cuidadosamente quais partições são BOOT e DISK antes de alterar arquivos de boot, para evitar que o sistema deixe de iniciar.
