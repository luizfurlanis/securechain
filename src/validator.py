#!/usr/bin/env python3

import os
import sys
import json
import datetime
from typing import Dict, List, Tuple, Optional

sys.path.append(os.path.dirname(__file__))

from blockchain import BlockchainAuditoria
from event_handler import EventHandler

class BlockchainValidator:
    
    def __init__(self):
        self.blockchain = BlockchainAuditoria()
        self.event_handler = EventHandler()
        self.alertas = []
    
    def validar_completo(self) -> Dict:
        print("Iniciando validacao completa da blockchain...")
        print("=" * 50)
        
        resultado = self.blockchain.validar_integridade_avancada()
        
        self._gerar_alertas(resultado)
        self._exibir_resumo(resultado)
        
        if resultado['status'] == 'CORROMPIDA':
            self._registrar_corrupcao(resultado)
        
        return resultado
    
    def _gerar_alertas(self, resultado: Dict):
        self.alertas = []
        
        for erro in resultado.get('erros', []):
            alerta = {
                'tipo': erro.get('tipo', 'ERRO_DESCONHECIDO'),
                'nivel': 'CRITICO',
                'bloco': erro.get('bloco', 'N/A'),
                'mensagem': erro.get('mensagem', ''),
                'timestamp': datetime.datetime.now().isoformat(),
                'detalhes': erro
            }
            self.alertas.append(alerta)
            
            self.event_handler.registrar_alerta(
                usuario='sistema',
                tipo=alerta['tipo'],
                arquivo=f'bloco_{alerta["bloco"]}',
                detalhes=alerta['mensagem']
            )
        
        for alerta in resultado.get('alertas', []):
            alerta_info = {
                'tipo': alerta.get('tipo', 'INCONSISTENCIA'),
                'nivel': 'ALTO',
                'bloco': alerta.get('bloco', 'N/A'),
                'mensagem': alerta.get('mensagem', ''),
                'timestamp': datetime.datetime.now().isoformat(),
                'detalhes': alerta
            }
            self.alertas.append(alerta_info)
    
    def _exibir_resumo(self, resultado: Dict):
        print("\nRESUMO DA VALIDACAO:")
        print("=" * 50)
        print(f"  Status: {resultado['status']}")
        print(f"  Total de blocos: {resultado['total_blocos']}")
        print(f"  Blocos validos: {resultado['estatisticas']['blocos_validos']}")
        print(f"  Blocos invalidos: {resultado['estatisticas']['blocos_invalidos']}")
        print(f"  Erros: {len(resultado['erros'])}")
        print(f"  Alertas: {len(resultado['alertas'])}")
        
        if resultado['erros']:
            print("\nERROS ENCONTRADOS:")
            for erro in resultado['erros']:
                print(f"  Bloco #{erro.get('bloco', '?')}: {erro.get('tipo')}")
                print(f"    {erro.get('mensagem')}")
        
        if resultado['alertas']:
            print("\nALERTAS:")
            for alerta in resultado['alertas']:
                print(f"  Bloco #{alerta.get('bloco', '?')}: {alerta.get('tipo')}")
                print(f"    {alerta.get('mensagem')}")
        
        if resultado['status'] == 'INTEGRO':
            print("\nBlockchain completamente integra!")
        elif resultado['status'] == 'INCONSISTENTE':
            print("\nBlockchain com inconsistencias (nao criticas)")
        else:
            print("\nBlockchain CORROMPIDA! Acoes necessarias.")
        
        print("=" * 50)
    
    def _registrar_corrupcao(self, resultado: Dict):
        erros = resultado.get('erros', [])
        
        for erro in erros:
            self.event_handler.registrar_evento(
                evento='CORRUPCAO_DETECTADA',
                descricao=f"Corrupcao detectada na blockchain: {erro.get('mensagem', '')}",
                usuario='sistema',
                detalhes={
                    'bloco': erro.get('bloco', 'N/A'),
                    'tipo': erro.get('tipo', 'DESCONHECIDO'),
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
        
        print("Corrupcao registrada na blockchain")
    
    def verificar_bloco_especifico(self, index: int) -> Dict:
        bloco = self.blockchain.obter_bloco(index)
        
        if not bloco:
            return {
                'sucesso': False,
                'mensagem': f'Bloco #{index} nao encontrado'
            }
        
        hash_recalculado = bloco.calcular_hash()
        valido = hash_recalculado == bloco.hash
        
        encadeamento_ok = True
        if index > 0:
            bloco_anterior = self.blockchain.obter_bloco(index - 1)
            if bloco_anterior:
                encadeamento_ok = bloco.hash_anterior == bloco_anterior.hash
        
        return {
            'sucesso': True,
            'bloco': {
                'index': bloco.index,
                'timestamp': bloco.timestamp,
                'evento': bloco.dados.get('evento', 'N/A'),
                'hash': bloco.hash,
                'hash_anterior': bloco.hash_anterior,
                'hash_recalculado': hash_recalculado,
                'valido': valido,
                'encadeamento_ok': encadeamento_ok
            }
        }
    
    def simular_corrupcao(self, index: int) -> Tuple[bool, str]:
        if index < 0 or index >= len(self.blockchain.cadeia):
            return False, f"Bloco #{index} nao encontrado"
        
        bloco = self.blockchain.cadeia[index]
        
        bloco.hash = '0' * 64
        self.blockchain._salvar()
        
        return True, f"Bloco #{index} corrompido (hash alterado para zeros)"
    
    def listar_blocos_invalidos(self) -> List[Dict]:
        invalidos = []
        
        for i, bloco in enumerate(self.blockchain.cadeia):
            hash_recalculado = bloco.calcular_hash()
            if hash_recalculado != bloco.hash:
                invalidos.append({
                    'index': i,
                    'hash_atual': bloco.hash,
                    'hash_esperado': hash_recalculado,
                    'evento': bloco.dados.get('evento', 'N/A'),
                    'timestamp': bloco.timestamp
                })
        
        return invalidos


def menu_principal():
    validator = BlockchainValidator()
    
    while True:
        print("\n" + "="*50)
        print("  SECURECHAIN - VALIDADOR DA BLOCKCHAIN")
        print("="*50)
        
        try:
            total = validator.blockchain.total_blocos()
            print(f"  Total de blocos: {total}")
        except:
            print("  Total de blocos: N/A")
        
        print("="*50)
        print("  1. Validar blockchain completa")
        print("  2. Verificar bloco especifico")
        print("  3. Listar blocos invalidos")
        print("  4. Exportar relatorio de validacao")
        print("  5. Visualizar ultimo bloco")
        print("  6. Reparar bloco (recalcular hash)")
        print("  7. SIMULAR corrupcao (TESTE)")
        print("  0. Sair")
        print("="*50)
        
        opcao = input("Escolha uma opcao: ").strip()
        
        if opcao == "1":
            print("\n" + "="*50)
            validator.validar_completo()
            print("="*50)
            
        elif opcao == "2":
            try:
                index = int(input("Indice do bloco: ").strip())
                resultado = validator.verificar_bloco_especifico(index)
                print("\nDETALHES DO BLOCO:")
                print("="*40)
                if resultado['sucesso']:
                    bloco = resultado['bloco']
                    print(f"  Index: {bloco['index']}")
                    print(f"  Timestamp: {bloco['timestamp']}")
                    print(f"  Evento: {bloco['evento']}")
                    print(f"  Hash: {bloco['hash'][:16]}...")
                    print(f"  Hash Anterior: {bloco['hash_anterior'][:16]}...")
                    print(f"  Hash Recalculado: {bloco['hash_recalculado'][:16]}...")
                    print(f"  Hash valido: {bloco['valido']}")
                    print(f"  Encadeamento: {bloco['encadeamento_ok']}")
                else:
                    print(f"  {resultado['mensagem']}")
            except ValueError:
                print("Indice invalido")
                
        elif opcao == "3":
            invalidos = validator.listar_blocos_invalidos()
            if invalidos:
                print("\nBLOCOS INVALIDOS:")
                print("="*40)
                for b in invalidos:
                    print(f"  Bloco #{b['index']} - {b['evento']}")
                    print(f"    Hash atual: {b['hash_atual'][:16]}...")
                    print(f"    Hash esperado: {b['hash_esperado'][:16]}...")
            else:
                print("\nNenhum bloco invalido encontrado")
                
        elif opcao == "4":
            arquivo = input("Caminho pra salvar (padrao: blockchain/validacao.json): ").strip()
            if not arquivo:
                arquivo = os.path.join(os.path.dirname(__file__), '..', 'blockchain', 'validacao.json')
            validator.blockchain.exportar_relatorio_validacao(arquivo)
            print(f"Relatorio salvo em: {arquivo}")
            
        elif opcao == "5":
            ultimo = validator.blockchain.ultimo_bloco()
            if ultimo:
                print("\nULTIMO BLOCO:")
                print("="*40)
                print(f"  Index: {ultimo.index}")
                print(f"  Timestamp: {ultimo.timestamp}")
                print(f"  Evento: {ultimo.dados.get('evento', 'N/A')}")
                print(f"  Descricao: {ultimo.dados.get('descricao', 'N/A')[:50]}")
                print(f"  Usuario: {ultimo.dados.get('usuario', 'N/A')}")
                print(f"  Hash: {ultimo.hash}")
                print(f"  Hash Anterior: {ultimo.hash_anterior}")
            else:
                print("Blockchain vazia")
                
        elif opcao == "6":
            try:
                index = int(input("Indice do bloco pra reparar: ").strip())
                sucesso, msg = validator.blockchain.reparar_bloco(index)
                print(msg)
                if sucesso:
                    validator.blockchain._salvar()
            except ValueError:
                print("Indice invalido")
                
        elif opcao == "7":
            print("\nATENCAO: Isso vai corromper a blockchain pra teste!")
            confirm = input("Tem certeza? (s/N): ").strip().lower()
            if confirm == 's':
                try:
                    index = int(input("Indice do bloco pra corromper: ").strip())
                    sucesso, msg = validator.simular_corrupcao(index)
                    print(msg)
                except ValueError:
                    print("Indice invalido")
            else:
                print("Operacao cancelada")
                
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opcao invalida")


if __name__ == "__main__":
    menu_principal()
