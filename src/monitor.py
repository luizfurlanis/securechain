#!/usr/bin/env python3

import os
import json
import hashlib
import datetime
import time
from typing import Dict, List, Tuple, Optional

DOCUMENTOS_DIR = os.path.join(os.path.dirname(__file__), '..', 'documentos')
HASHES_FILE = os.path.join(os.path.dirname(__file__), '..', 'blockchain', 'hashes.json')
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
ALERTAS_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'alertas.json')

class MonitorIntegridade:
    
    def __init__(self):
        self.hashes_referencia = {}
        self.alteracoes = []
        self._inicializar_diretorios()
        self._carregar_hashes()
    
    def _inicializar_diretorios(self):
        os.makedirs(DOCUMENTOS_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(HASHES_FILE), exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
    
    def _carregar_hashes(self):
        if os.path.exists(HASHES_FILE):
            with open(HASHES_FILE, 'r') as f:
                self.hashes_referencia = json.load(f)
        else:
            self.hashes_referencia = {}
    
    def _salvar_hashes(self):
        with open(HASHES_FILE, 'w') as f:
            json.dump(self.hashes_referencia, f, indent=2, default=str)
    
    def _calcular_hash(self, caminho_arquivo: str) -> Optional[str]:
        try:
            sha256 = hashlib.sha256()
            with open(caminho_arquivo, 'rb') as f:
                for bloco in iter(lambda: f.read(4096), b''):
                    sha256.update(bloco)
            return sha256.hexdigest()
        except Exception as e:
            print(f"Erro ao calcular hash de {caminho_arquivo}: {e}")
            return None
    
    def _registrar_alteracao(self, tipo: str, arquivo: str, detalhes: str):
        alteracao = {
            'tipo': tipo,
            'arquivo': arquivo,
            'detalhes': detalhes,
            'timestamp': datetime.datetime.now().isoformat(),
            'usuario': 'sistema'
        }
        self.alteracoes.append(alteracao)
        self._salvar_alteracoes()
        
        if tipo in ['modificado', 'excluido']:
            self._gerar_alerta(tipo, arquivo, detalhes)
    
    def _salvar_alteracoes(self):
        log_file = os.path.join(LOG_DIR, f'alteracoes_{datetime.datetime.now().strftime("%Y%m%d")}.json')
        
        alteracoes_existentes = []
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                alteracoes_existentes = json.load(f)
        
        alteracoes_existentes.extend(self.alteracoes)
        
        with open(log_file, 'w') as f:
            json.dump(alteracoes_existentes, f, indent=2, default=str)
        
        self.alteracoes = []
    
    def _gerar_alerta(self, tipo: str, arquivo: str, detalhes: str):
        alerta = {
            'tipo': tipo,
            'arquivo': arquivo,
            'detalhes': detalhes,
            'timestamp': datetime.datetime.now().isoformat(),
            'nivel': 'CRITICO' if tipo == 'modificado' else 'ALTO',
            'status': 'PENDENTE'
        }
        
        alertas = []
        if os.path.exists(ALERTAS_FILE):
            with open(ALERTAS_FILE, 'r') as f:
                alertas = json.load(f)
        
        alertas.append(alerta)
        
        with open(ALERTAS_FILE, 'w') as f:
            json.dump(alertas, f, indent=2, default=str)
        
        print(f"\nALERTA [{alerta['nivel']}]: {tipo.upper()} - {arquivo}")
        print(f"   Detalhes: {detalhes}")
        print(f"   Timestamp: {alerta['timestamp']}")
    
    def inicializar_hashes(self):
        print("Inicializando hashes de referencia...")
        
        if not os.path.exists(DOCUMENTOS_DIR):
            print(f"Diretorio {DOCUMENTOS_DIR} nao existe, criando agora...")
            os.makedirs(DOCUMENTOS_DIR)
        
        arquivos = os.listdir(DOCUMENTOS_DIR)
        
        if not arquivos:
            print("Nenhum arquivo encontrado em /documentos")
            return
        
        for arquivo in arquivos:
            caminho = os.path.join(DOCUMENTOS_DIR, arquivo)
            if os.path.isfile(caminho):
                hash_arquivo = self._calcular_hash(caminho)
                if hash_arquivo:
                    self.hashes_referencia[arquivo] = {
                        'hash': hash_arquivo,
                        'tamanho': os.path.getsize(caminho),
                        'modificado': datetime.datetime.fromtimestamp(
                            os.path.getmtime(caminho)
                        ).isoformat(),
                        'criado_em': datetime.datetime.now().isoformat()
                    }
                    print(f"  {arquivo}: {hash_arquivo[:16]}...")
        
        self._salvar_hashes()
        print(f"{len(self.hashes_referencia)} hashes armazenados com sucesso")
    
    def verificar_integridade(self) -> Dict[str, List[Dict]]:
        print("Verificando integridade dos arquivos...")
        
        resultado = {
            'criados': [],
            'modificados': [],
            'excluidos': [],
            'inalterados': []
        }
        
        if os.path.exists(DOCUMENTOS_DIR):
            arquivos_atual = set(os.listdir(DOCUMENTOS_DIR))
            arquivos_referencia = set(self.hashes_referencia.keys())
            
            for arquivo in arquivos_atual - arquivos_referencia:
                caminho = os.path.join(DOCUMENTOS_DIR, arquivo)
                if os.path.isfile(caminho):
                    hash_novo = self._calcular_hash(caminho)
                    if hash_novo:
                        resultado['criados'].append({
                            'arquivo': arquivo,
                            'hash': hash_novo,
                            'tamanho': os.path.getsize(caminho)
                        })
                        self._registrar_alteracao('criado', arquivo, f'Arquivo criado: {hash_novo[:16]}...')
            
            for arquivo in arquivos_referencia - arquivos_atual:
                resultado['excluidos'].append({
                    'arquivo': arquivo,
                    'hash_anterior': self.hashes_referencia[arquivo]['hash']
                })
                self._registrar_alteracao('excluido', arquivo, 'Arquivo removido do sistema')
            
            for arquivo in arquivos_atual & arquivos_referencia:
                caminho = os.path.join(DOCUMENTOS_DIR, arquivo)
                if os.path.isfile(caminho):
                    hash_atual = self._calcular_hash(caminho)
                    hash_anterior = self.hashes_referencia[arquivo]['hash']
                    
                    if hash_atual != hash_anterior:
                        resultado['modificados'].append({
                            'arquivo': arquivo,
                            'hash_anterior': hash_anterior,
                            'hash_atual': hash_atual,
                            'tamanho': os.path.getsize(caminho)
                        })
                        self._registrar_alteracao(
                            'modificado', 
                            arquivo, 
                            f'Hash alterado: {hash_anterior[:16]}... -> {hash_atual[:16]}...'
                        )
                        self.hashes_referencia[arquivo]['hash'] = hash_atual
                        self.hashes_referencia[arquivo]['modificado'] = datetime.datetime.now().isoformat()
                    else:
                        resultado['inalterados'].append(arquivo)
        
        self._salvar_hashes()
        
        print("\nRESUMO DA VERIFICACAO:")
        print(f"  Inalterados: {len(resultado['inalterados'])}")
        print(f"  Criados: {len(resultado['criados'])}")
        print(f"  Modificados: {len(resultado['modificados'])}")
        print(f"  Excluidos: {len(resultado['excluidos'])}")
        
        if resultado['criados']:
            print("\n  ARQUIVOS CRIADOS:")
            for item in resultado['criados']:
                print(f"    - {item['arquivo']} ({item['hash'][:16]}...)")
        
        if resultado['modificados']:
            print("\n  ARQUIVOS MODIFICADOS:")
            for item in resultado['modificados']:
                print(f"    - {item['arquivo']} ({item['hash_anterior'][:16]}... -> {item['hash_atual'][:16]}...)")
        
        if resultado['excluidos']:
            print("\n  ARQUIVOS EXCLUIDOS:")
            for item in resultado['excluidos']:
                print(f"    - {item['arquivo']}")
        
        print("\n" + "="*50)
        
        return resultado
    
    def monitorar_continuo(self, intervalo: int = 30):
        print(f"Monitoramento continuo iniciado (intervalo: {intervalo}s)")
        print("="*50)
        print("Pressione Ctrl+C pra parar\n")
        
        try:
            while True:
                print(f"\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.verificar_integridade()
                time.sleep(intervalo)
        except KeyboardInterrupt:
            print("\n\nMonitoramento interrompido pelo usuario.")
    
    def listar_alertas(self, status: Optional[str] = None):
        if not os.path.exists(ALERTAS_FILE):
            print("Nenhum alerta encontrado")
            return
        
        with open(ALERTAS_FILE, 'r') as f:
            alertas = json.load(f)
        
        if status:
            alertas = [a for a in alertas if a['status'] == status]
        
        if not alertas:
            print("Nenhum alerta encontrado")
            return
        
        print("\nLISTA DE ALERTAS:")
        print("="*50)
        for i, alerta in enumerate(alertas, 1):
            print(f"{i}. {alerta['tipo'].upper()} - {alerta['arquivo']}")
            print(f"   Nivel: {alerta['nivel']}")
            print(f"   Status: {alerta['status']}")
            print(f"   Data: {alerta['timestamp']}")
            print(f"   Detalhes: {alerta['detalhes']}")
            print("-"*30)
    
    def marcar_alerta_resolvido(self, indice: int):
        if not os.path.exists(ALERTAS_FILE):
            print("Nenhum alerta encontrado")
            return
        
        with open(ALERTAS_FILE, 'r') as f:
            alertas = json.load(f)
        
        if indice < 1 or indice > len(alertas):
            print(f"Indice invalido. Use 1 a {len(alertas)}")
            return
        
        alertas[indice-1]['status'] = 'RESOLVIDO'
        alertas[indice-1]['resolvido_em'] = datetime.datetime.now().isoformat()
        
        with open(ALERTAS_FILE, 'w') as f:
            json.dump(alertas, f, indent=2, default=str)
        
        print(f"Alerta {indice} marcado como resolvido")


def menu_principal():
    monitor = MonitorIntegridade()
    
    while True:
        print("\n" + "="*50)
        print("  SECURECHAIN - MONITOR DE INTEGRIDADE")
        print("="*50)
        print("  1. Inicializar hashes de referencia")
        print("  2. Verificar integridade (uma vez)")
        print("  3. Monitoramento continuo")
        print("  4. Listar alertas pendentes")
        print("  5. Listar todos os alertas")
        print("  6. Marcar alerta como resolvido")
        print("  0. Sair")
        print("="*50)
        
        opcao = input("Escolha uma opcao: ").strip()
        
        if opcao == "1":
            monitor.inicializar_hashes()
        elif opcao == "2":
            monitor.verificar_integridade()
        elif opcao == "3":
            intervalo = input("Intervalo em segundos (padrao: 30): ").strip()
            intervalo = int(intervalo) if intervalo else 30
            monitor.monitorar_continuo(intervalo)
        elif opcao == "4":
            monitor.listar_alertas(status="PENDENTE")
        elif opcao == "5":
            monitor.listar_alertas()
        elif opcao == "6":
            monitor.listar_alertas(status="PENDENTE")
            indice = input("Numero do alerta pra resolver: ").strip()
            if indice:
                monitor.marcar_alerta_resolvido(int(indice))
        elif opcao == "0":
            break
        else:
            print("Opcao invalida")


if __name__ == "__main__":
    menu_principal()
