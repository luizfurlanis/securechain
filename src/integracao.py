#!/usr/bin/env python3
"""
Script de integração - RF02 + RF03 + RF04
Demonstra a integração completa do sistema
"""

import sys
import os

# Adicionar src ao path
sys.path.append(os.path.dirname(__file__))

from auth import AuthSystem
from monitor import MonitorIntegridade
from event_handler import EventHandler

def testar_integracao():
    """Testa a integração dos três módulos"""
    print("="*60)
    print("  🔐 SECURECHAIN - TESTE DE INTEGRAÇÃO COMPLETA")
    print("="*60)
    
    # Inicializar módulos
    auth = AuthSystem()
    monitor = MonitorIntegridade()
    eventos = EventHandler()
    
    # 1. Login admin
    print("\n1. Login do administrador:")
    sucesso, msg = auth.login("admin", "Admin@2025")
    print(f"   {msg}")
    if sucesso:
        eventos.registrar_login("admin", True)
    
    # 2. Inicializar hashes
    print("\n2. Inicializando monitor de integridade:")
    monitor.inicializar_hashes()
    
    # 3. Verificar integridade
    print("\n3. Verificando integridade dos arquivos:")
    resultado = monitor.verificar_integridade()
    
    # 4. Registrar eventos na blockchain
    print("\n4. Registrando eventos na blockchain:")
    
    # Registrar os eventos detectados
    for item in resultado['criados']:
        eventos.registrar_arquivo_criado("admin", item['arquivo'], item['hash'])
    
    for item in resultado['modificados']:
        eventos.registrar_arquivo_modificado("admin", item['arquivo'], 
                                            item['hash_anterior'], item['hash_atual'])
    
    for item in resultado['excluidos']:
        eventos.registrar_arquivo_excluido("admin", item['arquivo'], item['hash_anterior'])
    
    print("   ✅ Eventos registrados na blockchain!")
    
    # 5. Mostrar blockchain
    print("\n5. Blockchain atual:")
    ultimos = eventos.ultimos_eventos(10)
    for evento in ultimos:
        print(f"   [#{evento['_index']}] {evento['evento']} - {evento.get('descricao')}")
    
    # 6. Validar blockchain
    print("\n6. Validando integridade da blockchain:")
    integro, erros = eventos.blockchain.validar_integridade()
    if integro:
        print("   ✅ Blockchain íntegra!")
    else:
        print(f"   ❌ {len(erros)} erros encontrados!")
    
    # 7. Logout
    print("\n7. Finalizando sessão:")
    auth.logout()
    eventos.registrar_logout("admin")
    
    print("\n" + "="*60)
    print("  ✅ TESTE DE INTEGRAÇÃO CONCLUÍDO COM SUCESSO!")
    print("="*60)

if __name__ == "__main__":
    testar_integracao()