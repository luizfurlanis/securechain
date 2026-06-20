import os
import json
from datetime import datetime
from blockchain import BlockchainAuditoria

class EventHandler:
    
    def __init__(self):
        self.blockchain = BlockchainAuditoria()
    
    def registrar_login(self, usuario: str, sucesso: bool = True):
        evento = "LOGIN" if sucesso else "LOGIN_FALHA"
        descricao = f"Login {'bem-sucedido' if sucesso else 'falhou'} para usuario {usuario}"
        return self.blockchain.registrar_evento(
            evento=evento,
            descricao=descricao,
            usuario=usuario if sucesso else "desconhecido"
        )
    
    def registrar_logout(self, usuario: str):
        return self.blockchain.registrar_evento(
            evento="LOGOUT",
            descricao=f"Logout do usuario {usuario}",
            usuario=usuario
        )
    
    def registrar_arquivo_criado(self, usuario: str, arquivo: str, hash: str):
        return self.blockchain.registrar_evento(
            evento="ARQUIVO_CRIADO",
            descricao=f"Arquivo {arquivo} criado",
            usuario=usuario,
            detalhes={"arquivo": arquivo, "hash": hash}
        )
    
    def registrar_arquivo_modificado(self, usuario: str, arquivo: str, 
                                     hash_anterior: str, hash_atual: str):
        return self.blockchain.registrar_evento(
            evento="ARQUIVO_MODIFICADO",
            descricao=f"Arquivo {arquivo} modificado",
            usuario=usuario,
            detalhes={
                "arquivo": arquivo,
                "hash_anterior": hash_anterior,
                "hash_atual": hash_atual
            }
        )
    
    def registrar_arquivo_excluido(self, usuario: str, arquivo: str, hash_anterior: str):
        return self.blockchain.registrar_evento(
            evento="ARQUIVO_EXCLUIDO",
            descricao=f"Arquivo {arquivo} excluido",
            usuario=usuario,
            detalhes={"arquivo": arquivo, "hash_anterior": hash_anterior}
        )
    
    def registrar_backup(self, usuario: str, arquivo_backup: str, tamanho: int):
        return self.blockchain.registrar_evento(
            evento="BACKUP",
            descricao=f"Backup realizado: {arquivo_backup}",
            usuario=usuario,
            detalhes={"arquivo": arquivo_backup, "tamanho": tamanho}
        )
    
    def registrar_usuario(self, usuario: str, novo_usuario: str, perfil: str):
        return self.blockchain.registrar_evento(
            evento="USUARIO_CRIADO",
            descricao=f"Usuario {novo_usuario} criado com perfil {perfil}",
            usuario=usuario
        )
    
    def registrar_alerta(self, usuario: str, tipo: str, arquivo: str, detalhes: str):
        return self.blockchain.registrar_evento(
            evento="ALERTA",
            descricao=f"Alerta {tipo} para arquivo {arquivo}",
            usuario=usuario,
            detalhes={"tipo": tipo, "arquivo": arquivo, "detalhes": detalhes}
        )
    
    def ultimos_eventos(self, n: int = 10):
        eventos = self.blockchain.listar_eventos()
        return eventos[-n:] if eventos else []


def testar_event_handler():
    print("="*50)
    print("  TESTE DO EVENT HANDLER")
    print("="*50)
    
    handler = EventHandler()
    
    print("\n1. Registrando eventos...")
    handler.registrar_login("admin", True)
    handler.registrar_login("joao", False)
    handler.registrar_arquivo_criado("admin", "doc1.txt", "abc123def456")
    handler.registrar_arquivo_modificado("joao", "doc1.txt", "abc123def456", "def456ghi789")
    handler.registrar_backup("admin", "backup_20250620.tar.gz", 1024000)
    handler.registrar_usuario("admin", "maria", "analista")
    
    print("   Eventos registrados!")
    
    print("\n2. Ultimos eventos:")
    for evento in handler.ultimos_eventos(6):
        print(f"  [{evento['_timestamp'][:19]}] {evento['evento']} - {evento.get('descricao')}")
    
    print("\n3. Validando blockchain...")
    integro, erros = handler.blockchain.validar_integridade()
    if integro:
        print("   Blockchain integra!")
    else:
        print(f"   Erros encontrados: {len(erros)}")
    
    print("\nTestes concluidos!")

if __name__ == "__main__":
    testar_event_handler()
