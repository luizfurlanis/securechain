import json
import hashlib
import datetime
import os
from typing import Dict, List, Optional, Tuple

CHAIN_FILE = os.path.join(os.path.dirname(__file__), '..', 'blockchain', 'chain.json')

class Bloco:
    
    def __init__(self, index: int, timestamp: str, dados: Dict, hash_anterior: str):
        self.index = index
        self.timestamp = timestamp
        self.dados = dados
        self.hash_anterior = hash_anterior
        self.hash = self.calcular_hash()
    
    def calcular_hash(self) -> str:
        # Concatenar todos os campos
        conteudo = f"{self.index}{self.timestamp}{json.dumps(self.dados, sort_keys=True)}{self.hash_anterior}"
        return hashlib.sha256(conteudo.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'dados': self.dados,
            'hash_anterior': self.hash_anterior,
            'hash': self.hash
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Bloco':
        bloco = Bloco(
            data['index'],
            data['timestamp'],
            data['dados'],
            data['hash_anterior']
        )
        bloco.hash = data['hash']
        return bloco


class BlockchainAuditoria:
    
    def __init__(self):
        self.cadeia: List[Bloco] = []
        self._carregar_ou_criar_cadeia()
    
    def _carregar_ou_criar_cadeia(self):
        """Carrega a blockchain do arquivo ou cria uma nova com bloco gênese"""
        if os.path.exists(CHAIN_FILE):
            with open(CHAIN_FILE, 'r') as f:
                dados = json.load(f)
                self.cadeia = [Bloco.from_dict(bloco) for bloco in dados]
            print(f"✅ Blockchain carregada: {len(self.cadeia)} blocos")
        else:
            self._criar_bloco_genese()
            self._salvar()
            print("✅ Blockchain criada com bloco gênese")
    
    def _criar_bloco_genese(self):
        bloco_genese = Bloco(
            index=0,
            timestamp=datetime.datetime.now().isoformat(),
            dados={
                'evento': 'BLOCO_GENESE',
                'descricao': 'Blockchain criada pelo SecureChain Audit',
                'usuario': 'sistema'
            },
            hash_anterior='0' * 64  # Hash vazio para o primeiro bloco
        )
        self.cadeia.append(bloco_genese)
    
    def _salvar(self):
        os.makedirs(os.path.dirname(CHAIN_FILE), exist_ok=True)
        with open(CHAIN_FILE, 'w') as f:
            json.dump([bloco.to_dict() for bloco in self.cadeia], f, indent=2, default=str)
    
    def adicionar_bloco(self, dados: Dict) -> Tuple[bool, str, Optional[Bloco]]:
        
        if not self.cadeia:
            self._criar_bloco_genese()
        
        ultimo_bloco = self.cadeia[-1]
        
        # Validar dados
        if 'evento' not in dados:
            return False, "Dados inválidos: campo 'evento' é obrigatório", None
        
        if not self._validar_ultimo_bloco():
            return False, "Blockchain corrompida! Último bloco inválido.", None
        
        novo_bloco = Bloco(
            index=len(self.cadeia),
            timestamp=datetime.datetime.now().isoformat(),
            dados=dados,
            hash_anterior=ultimo_bloco.hash
        )
        
        self.cadeia.append(novo_bloco)
        self._salvar()
        
        return True, f"Bloco #{novo_bloco.index} criado: {dados.get('evento', 'Evento')}", novo_bloco
    
    def _validar_ultimo_bloco(self) -> bool:
        if not self.cadeia:
            return True
        
        ultimo = self.cadeia[-1]
        hash_recalculado = ultimo.calcular_hash()
        return hash_recalculado == ultimo.hash
    
    def validar_integridade(self) -> Tuple[bool, List[Dict]]:
        erros = []
        
        if not self.cadeia:
            return True, []
        
        if self.cadeia[0].hash_anterior != '0' * 64:
            erros.append({
                'bloco': 0,
                'erro': 'Bloco gênese com hash_anterior inválido',
                'esperado': '0' * 64,
                'encontrado': self.cadeia[0].hash_anterior
            })
        
        for i, bloco in enumerate(self.cadeia):
            # Verificar hash do bloco
            hash_recalculado = bloco.calcular_hash()
            if hash_recalculado != bloco.hash:
                erros.append({
                    'bloco': i,
                    'erro': 'Hash do bloco não confere',
                    'esperado': bloco.hash,
                    'encontrado': hash_recalculado,
                    'dados': bloco.dados
                })
            
            if i > 0:
                bloco_anterior = self.cadeia[i-1]
                if bloco.hash_anterior != bloco_anterior.hash:
                    erros.append({
                        'bloco': i,
                        'erro': 'Quebra de encadeamento',
                        'hash_anterior_esperado': bloco_anterior.hash,
                        'hash_anterior_encontrado': bloco.hash_anterior
                    })
        
        return len(erros) == 0, erros
    
    def listar_eventos(self, filtro: Optional[str] = None) -> List[Dict]:
        eventos = []
        for bloco in self.cadeia[1:]:  
            evento = bloco.dados.copy()
            evento['_index'] = bloco.index
            evento['_timestamp'] = bloco.timestamp
            evento['_hash'] = bloco.hash
            eventos.append(evento)
        
        if filtro:
            eventos = [e for e in eventos if e.get('evento') == filtro]
        
        return eventos
    
    def buscar_evento(self, evento: str) -> List[Dict]:
        return self.listar_eventos(filtro=evento)
    
    def ultimo_bloco(self) -> Optional[Bloco]:
        return self.cadeia[-1] if self.cadeia else None
    
    def total_blocos(self) -> int:
        return len(self.cadeia)
    
    def obter_bloco(self, index: int) -> Optional[Bloco]:
        if 0 <= index < len(self.cadeia):
            return self.cadeia[index]
        return None
    
    def registrar_evento(self, evento: str, descricao: str, usuario: str = 'sistema', 
                         detalhes: Optional[Dict] = None) -> Tuple[bool, str]:
        dados = {
            'evento': evento,
            'descricao': descricao,
            'usuario': usuario
        }
        
        if detalhes:
            dados['detalhes'] = detalhes
        
        return self.adicionar_bloco(dados)
    
    def exportar_relatorio(self, arquivo: Optional[str] = None) -> str:
        """
        Exporta um relatório completo da blockchain
        
        Args:
            arquivo: Caminho do arquivo para salvar (opcional)
        
        Returns:
            Conteúdo do relatório
        """
        relatorio = []
        for i, bloco in enumerate(self.cadeia):
            relatorio.append({
                'bloco': i,
                'timestamp': bloco.timestamp,
                'evento': bloco.dados.get('evento', 'N/A'),
                'descricao': bloco.dados.get('descricao', 'N/A'),
                'usuario': bloco.dados.get('usuario', 'N/A'),
                'hash': bloco.hash,
                'hash_anterior': bloco.hash_anterior
            })
        
        if arquivo:
            with open(arquivo, 'w') as f:
                json.dump(relatorio, f, indent=2, default=str)
            print(f"Relatório salvo em: {arquivo}")
        
        return json.dumps(relatorio, indent=2, default=str)

def menu_principal():
    blockchain = BlockchainAuditoria()
    
    while True:
        print(f"Total de blocos: {blockchain.total_blocos()}")
        print("="*50)
        print("  1. Registrar evento")
        print("  2. Listar eventos")
        print("  3. Buscar evento por tipo")
        print("  4. Validar integridade da blockchain")
        print("  5. Ver último bloco")
        print("  6. Exportar relatório")
        print("  0. Sair")
        print("="*50)
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == "1":
            print("  - LOGIN")
            print("  - LOGOUT")
            print("  - LOGIN_FALHA")
            print("  - ARQUIVO_CRIADO")
            print("  - ARQUIVO_MODIFICADO")
            print("  - ARQUIVO_EXCLUIDO")
            print("  - BACKUP")
            print("  - USUARIO_CRIADO")
            print("  - USUARIO_REMOVIDO")
            print("  - ALERTA")
            
            evento = input("\nEvento: ").strip().upper()
            descricao = input("Descrição: ").strip()
            usuario = input("Usuário (padrão: sistema): ").strip() or "sistema"
            detalhes_str = input("Detalhes (JSON, opcional): ").strip()
            
            detalhes = None
            if detalhes_str:
                try:
                    detalhes = json.loads(detalhes_str)
                except:
                    print("❌ JSON inválido. Ignorando detalhes.")
            
            sucesso, msg = blockchain.registrar_evento(evento, descricao, usuario, detalhes)
            print(msg)
            
        elif opcao == "2":
            eventos = blockchain.listar_eventos()
            if eventos:
                print(f"\n📋 EVENTOS ({len(eventos)}):")
                for e in eventos:
                    print(f"  #{e['_index']} [{e['_timestamp'][:19]}] {e.get('evento')}")
                    print(f"     {e.get('descricao')} - {e.get('usuario')}")
            else:
                print("📭 Nenhum evento registrado")
                
        elif opcao == "3":
            evento = input("Tipo de evento: ").strip().upper()
            eventos = blockchain.buscar_evento(evento)
            if eventos:
                print(f"\n🔍 EVENTOS DO TIPO '{evento}':")
                for e in eventos:
                    print(f"  #{e['_index']} [{e['_timestamp'][:19]}] {e.get('descricao')}")
            else:
                print(f"📭 Nenhum evento do tipo '{evento}' encontrado")
                
        elif opcao == "4":
            print("\n🔍 Validando integridade da blockchain...")
            integro, erros = blockchain.validar_integridade()
            if integro:
                print("Blockchain íntegra! Nenhum erro encontrado.")
            else:
                print(f"ERROS ENCONTRADOS ({len(erros)}):")
                for erro in erros:
                    print(f"  Bloco #{erro.get('bloco')}: {erro.get('erro')}")
                    if 'esperado' in erro:
                        print(f"    Esperado: {erro['esperado']}")
                        print(f"    Encontrado: {erro['encontrado']}")
                        
        elif opcao == "5":
            ultimo = blockchain.ultimo_bloco()
            if ultimo:
                print(f"  Index: {ultimo.index}")
                print(f"  Timestamp: {ultimo.timestamp}")
                print(f"  Evento: {ultimo.dados.get('evento')}")
                print(f"  Descrição: {ultimo.dados.get('descricao')}")
                print(f"  Hash: {ultimo.hash}")
                print(f"  Hash Anterior: {ultimo.hash_anterior}")
            else:
                print("📭 Blockchain vazia")
                
        elif opcao == "6":
            arquivo = input("Caminho para salvar (padrão: blockchain/relatorio.json): ").strip()
            if not arquivo:
                arquivo = os.path.join(os.path.dirname(CHAIN_FILE), 'relatorio.json')
            blockchain.exportar_relatorio(arquivo)
            print(f"Relatório exportado para: {arquivo}")
            
        elif opcao == "0":
            break
        else:
            print("Opção inválida")


if __name__ == "__main__":
    menu_principal()