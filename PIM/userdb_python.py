"""
userdb_python.py
Implementação em Python puro das funções da biblioteca C
para gerenciamento de usuários.
"""

import struct
import os

DBFILE = "users.dat"

class Usuario:
    """Estrutura equivalente ao struct Usuario em C"""
    def __init__(self, nome="", senha="", email="", idade=0):
        self.nome = nome[:50]  # máximo 50 chars
        self.senha = senha[:50]
        self.email = email[:50]
        self.idade = idade
    
    def to_bytes(self):
        """Converte para bytes (formato binário compatível com C)"""
        # 50 bytes para nome, 50 para senha, 50 para email, 4 para idade (int)
        nome_bytes = self.nome.encode('utf-8')[:50].ljust(50, b'\x00')
        senha_bytes = self.senha.encode('utf-8')[:50].ljust(50, b'\x00')
        email_bytes = self.email.encode('utf-8')[:50].ljust(50, b'\x00')
        idade_bytes = struct.pack('i', self.idade)  # int de 4 bytes
        return nome_bytes + senha_bytes + email_bytes + idade_bytes
    
    @staticmethod
    def from_bytes(data):
        """Lê um usuário dos bytes"""
        if len(data) < 154:
            return None
        nome = data[0:50].decode('utf-8').rstrip('\x00')
        senha = data[50:100].decode('utf-8').rstrip('\x00')
        email = data[100:150].decode('utf-8').rstrip('\x00')
        idade = struct.unpack('i', data[150:154])[0]
        return Usuario(nome, senha, email, idade)


def adicionar_usuario(nome, senha, email, idade):
    """
    Adiciona um usuário no arquivo binário.
    Equivalente à função C: void adicionar_usuario(...)
    """
    try:
        # Converte bytes para string se necessário
        if isinstance(nome, bytes):
            nome = nome.decode('utf-8')
        if isinstance(senha, bytes):
            senha = senha.decode('utf-8')
        if isinstance(email, bytes):
            email = email.decode('utf-8')
        
        usuario = Usuario(nome, senha, email, idade)
        
        with open(DBFILE, 'ab') as f:
            f.write(usuario.to_bytes())
        
        print(f"Usuário '{nome}' adicionado com sucesso!")
    except Exception as e:
        print(f"Erro ao adicionar usuário: {e}")


def listar_usuarios():
    """
    Lista todos os usuários cadastrados.
    Equivalente à função C: void listar_usuarios()
    """
    if not os.path.exists(DBFILE):
        print("Nenhum usuário encontrado (arquivo ausente).")
        return
    
    try:
        with open(DBFILE, 'rb') as f:
            print("=== Lista de Usuários ===")
            count = 0
            while True:
                data = f.read(154)  # tamanho do registro
                if not data or len(data) < 154:
                    break
                
                usuario = Usuario.from_bytes(data)
                if usuario and usuario.nome.strip():
                    print(f"Nome : {usuario.nome}")
                    print(f"Senha: {usuario.senha}")
                    print(f"Email: {usuario.email}")
                    print(f"Idade: {usuario.idade}\n")
                    count += 1
            
            if count == 0:
                print("Nenhum usuário cadastrado.")
    except Exception as e:
        print(f"Erro ao listar usuários: {e}")
