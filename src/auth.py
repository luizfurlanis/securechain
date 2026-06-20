#!/usr/bin/env python3

import bcrypt
import json
import os
import datetime
from typing import Dict, Optional, Tuple

USERS_FILE = os.path.join(os.path.dirname(__file__), '..', 'blockchain', 'users.json')

PERFIS = ['admin', 'analista', 'visitante']

class AuthSystem:
    
    def __init__(self):
        self.usuario_atual = None
        self.perfil_atual = None
        self._inicializar_arquivo_usuarios()
    
    def _inicializar_arquivo_usuarios(self):
        if not os.path.exists(USERS_FILE):
            os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
            senha_hash = self._hash_senha("Admin@2025")
            usuarios = {
                "admin": {
                    "senha_hash": senha_hash.decode('utf-8'),
                    "perfil": "admin",
                    "criado_em": datetime.datetime.now().isoformat()
                }
            }
            with open(USERS_FILE, 'w') as f:
                json.dump(usuarios, f, indent=2)
            print("Usuario admin padrao criado: admin / Admin@2025")
    
    def _hash_senha(self, senha: str) -> bytes:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(senha.encode('utf-8'), salt)
    
    def _verificar_senha(self, senha: str, hash_senha: str) -> bool:
        try:
            return bcrypt.checkpw(senha.encode('utf-8'), hash_senha.encode('utf-8'))
        except:
            return False
    
    def _carregar_usuarios(self) -> dict:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def _salvar_usuarios(self, usuarios: dict):
        with open(USERS_FILE, 'w') as f:
            json.dump(usuarios, f, indent=2, default=str)
    
    def cadastrar_usuario(self, username: str, senha: str, perfil: str) -> Tuple[bool, str]:
        if not username or len(username) < 3:
            return False, "Username deve ter pelo menos 3 caracteres"
        
        if not senha or len(senha) < 6:
            return False, "Senha deve ter pelo menos 6 caracteres"
        
        if perfil not in PERFIS:
            return False, f"Perfil invalido. Use: {', '.join(PERFIS)}"
        
        usuarios = self._carregar_usuarios()
        
        if username in usuarios:
            return False, f"Usuario '{username}' ja existe!"
        
        senha_hash = self._hash_senha(senha)
        usuarios[username] = {
            "senha_hash": senha_hash.decode('utf-8'),
            "perfil": perfil,
            "criado_em": datetime.datetime.now().isoformat(),
            "ultimo_login": None,
            "sessoes": []
        }
        
        self._salvar_usuarios(usuarios)
        return True, f"Usuario '{username}' cadastrado com sucesso como {perfil}"
    
    def login(self, username: str, senha: str) -> Tuple[bool, str]:
        usuarios = self._carregar_usuarios()
        
        if username not in usuarios:
            return False, "Usuario ou senha invalidos"
        
        usuario = usuarios[username]
        
        if not self._verificar_senha(senha, usuario["senha_hash"]):
            return False, "Usuario ou senha invalidos"
        
        usuario["ultimo_login"] = datetime.datetime.now().isoformat()
        usuario["sessoes"].append({
            "login": datetime.datetime.now().isoformat(),
            "ip": "localhost"
        })
        
        self._salvar_usuarios(usuarios)
        
        self.usuario_atual = username
        self.perfil_atual = usuario["perfil"]
        
        return True, f"Login realizado com sucesso! Perfil: {usuario['perfil']}"
    
    def logout(self):
        if self.usuario_atual:
            print(f"Logout realizado: {self.usuario_atual}")
            self.usuario_atual = None
            self.perfil_atual = None
    
    def get_usuario_atual(self) -> Optional[str]:
        return self.usuario_atual
    
    def get_perfil_atual(self) -> Optional[str]:
        return self.perfil_atual
    
    def is_autenticado(self) -> bool:
        return self.usuario_atual is not None
    
    def is_admin(self) -> bool:
        return self.perfil_atual == "admin"
    
    def is_analista(self) -> bool:
        return self.perfil_atual == "analista"
    
    def is_visitante(self) -> bool:
        return self.perfil_atual == "visitante"
    
    def listar_usuarios(self) -> dict:
        if not self.is_admin():
            return {"erro": "Apenas administradores podem listar usuarios"}
        return self._carregar_usuarios()
    
    def remover_usuario(self, username: str) -> Tuple[bool, str]:
        if not self.is_admin():
            return False, "Apenas administradores podem remover usuarios"
        
        if username == "admin":
            return False, "Nao e possivel remover o usuario admin"
        
        usuarios = self._carregar_usuarios()
        if username not in usuarios:
            return False, f"Usuario '{username}' nao encontrado"
        
        del usuarios[username]
        self._salvar_usuarios(usuarios)
        return True, f"Usuario '{username}' removido com sucesso"


def menu_principal(auth: AuthSystem):
    while True:
        print("\n" + "="*50)
        print("  SECURECHAIN AUDIT - SISTEMA DE AUTENTICACAO")
        print("="*50)
        
        if auth.is_autenticado():
            print(f"  Usuario: {auth.get_usuario_atual()} ({auth.get_perfil_atual()})")
            print("="*50)
            print("  1. Fazer Logout")
            print("  2. Ver informacoes do usuario")
            if auth.is_admin():
                print("  3. Listar usuarios")
                print("  4. Cadastrar novo usuario")
                print("  5. Remover usuario")
            print("  0. Sair")
        else:
            print("  Nenhum usuario logado")
            print("="*50)
            print("  1. Fazer Login")
            print("  2. Cadastrar novo usuario")
            print("  0. Sair")
        
        opcao = input("\nEscolha uma opcao: ").strip()
        
        if not auth.is_autenticado():
            if opcao == "1":
                username = input("Username: ").strip()
                senha = input("Senha: ").strip()
                sucesso, msg = auth.login(username, senha)
                print(msg)
            elif opcao == "2":
                username = input("Username: ").strip()
                senha = input("Senha: ").strip()
                perfil = input("Perfil (admin/analista/visitante): ").strip().lower()
                sucesso, msg = auth.cadastrar_usuario(username, senha, perfil)
                print(msg)
            elif opcao == "0":
                print("Saindo...")
                break
            else:
                print("Opcao invalida")
        
        else:
            if opcao == "1":
                auth.logout()
            elif opcao == "2":
                print(f"  Usuario: {auth.get_usuario_atual()}")
                print(f"  Perfil: {auth.get_perfil_atual()}")
            elif opcao == "3" and auth.is_admin():
                usuarios = auth.listar_usuarios()
                print("\nLISTA DE USUARIOS:")
                for user, info in usuarios.items():
                    print(f"  - {user} ({info['perfil']}) - Ultimo login: {info.get('ultimo_login', 'Nunca')}")
            elif opcao == "4" and auth.is_admin():
                username = input("Username: ").strip()
                senha = input("Senha: ").strip()
                perfil = input("Perfil (admin/analista/visitante): ").strip().lower()
                sucesso, msg = auth.cadastrar_usuario(username, senha, perfil)
                print(msg)
            elif opcao == "5" and auth.is_admin():
                username = input("Username pra remover: ").strip()
                sucesso, msg = auth.remover_usuario(username)
                print(msg)
            elif opcao == "0":
                auth.logout()
                print("Saindo...")
                break
            else:
                print("Opcao invalida ou sem permissao")


if __name__ == "__main__":
    auth = AuthSystem()
    menu_principal(auth)
