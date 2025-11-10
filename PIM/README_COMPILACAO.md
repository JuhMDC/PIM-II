# 🛠️ Guia de Compilação - Sistema Acadêmico

Este sistema pode funcionar de **duas formas**:

1. **Com biblioteca C nativa** (melhor performance) ✅
2. **Com módulo Python puro** (fallback automático) ⚙️

---

## 📋 Requisitos

- Python 3.6 ou superior
- Tkinter (geralmente já vem com Python)

---

## 🪟 Windows

### Opção 1: Usar módulo Python (Recomendado - Sem compilação)
```powershell
python app.py
```
O sistema detectará automaticamente que não há biblioteca C e usará o módulo Python puro.

### Opção 2: Compilar biblioteca C nativa

**Instalar MinGW-w64:**

1. Baixe em: https://winlibs.com/ (versão standalone)
2. Extraia para `C:\mingw64`
3. Adicione ao PATH: `C:\mingw64\bin`

**Compilar:**
```powershell
gcc -shared -o libuserdb.dll userdb.c
python app.py
```

---

## 🐧 Linux

### Opção 1: Usar módulo Python
```bash
python3 app.py
```

### Opção 2: Compilar biblioteca C nativa

**Instalar GCC (se necessário):**
```bash
# Debian/Ubuntu
sudo apt-get install build-essential

# Fedora/RHEL
sudo dnf install gcc

# Arch
sudo pacman -S gcc
```

**Compilar:**
```bash
gcc -shared -fPIC -o libuserdb.so userdb.c
python3 app.py
```

---

## 🍎 macOS

### Opção 1: Usar módulo Python
```bash
python3 app.py
```

### Opção 2: Compilar biblioteca C nativa

**Instalar Xcode Command Line Tools (se necessário):**
```bash
xcode-select --install
```

**Compilar:**
```bash
# Tenta .dylib primeiro (nativo do macOS)
gcc -shared -fPIC -o libuserdb.dylib userdb.c

# Se der erro, tenta .so
gcc -shared -fPIC -o libuserdb.so userdb.c

python3 app.py
```

---

## 🔍 Verificação

Ao executar `python app.py`, você verá uma das mensagens:

- ✅ `✓ Biblioteca C carregada: libuserdb.dll` (Windows)
- ✅ `✓ Biblioteca C carregada: libuserdb.so` (Linux)
- ✅ `✓ Biblioteca C carregada: libuserdb.dylib` (macOS)
- ⚠️ `⚠ Biblioteca C não encontrada. Usando implementação Python pura.`

**Ambas as opções funcionam perfeitamente!**

---

## 🎯 Login Padrão

- **Usuário:** `ADM`
- **Senha:** `12345Abc@`

---

## 📁 Estrutura de Arquivos

```
PIM/
├── app.py                  # Aplicação principal
├── userdb.c                # Código C (biblioteca nativa)
├── userdb_python.py        # Implementação Python pura
├── libuserdb.dll           # Biblioteca compilada (Windows)
├── libuserdb.so            # Biblioteca compilada (Linux)
├── libuserdb.dylib         # Biblioteca compilada (macOS)
├── users.dat               # Banco de dados de usuários (binário)
├── cursos.dat              # Cadastro de cursos
├── notas.dat               # Notas dos alunos
├── faltas.dat              # Faltas dos alunos
└── inscricoes.dat          # Inscrições em cursos
```

---

## ❓ Problemas Comuns

### Windows: "gcc: command not found"
- Instale MinGW-w64 conforme instruções acima
- OU simplesmente use o módulo Python (funciona sem compilação)

### Linux/Mac: Erro de permissão
```bash
chmod +x libuserdb.so  # ou .dylib no macOS
```

### Biblioteca não encontrada
- Verifique se o arquivo compilado está na mesma pasta que `app.py`
- O sistema automaticamente usará o módulo Python se não encontrar a biblioteca C

---

## 🚀 Início Rápido (Sem Compilação)

```bash
# Clone ou navegue até a pasta
cd c:\PIM_-main\PIM

# Execute diretamente (usará Python puro)
python app.py
```

**Pronto! O sistema funcionará automaticamente! 🎉**
