#!/usr/bin/env python3

import os
import sys
import json
import subprocess
import datetime
import socket
from typing import Dict, List, Optional

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

AUDITORIA_DIR = os.path.join(os.path.dirname(__file__), '..', 'auditoria')
RELATORIOS_DIR = os.path.join(AUDITORIA_DIR, 'relatorios')
LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')

class AuditoriaSistema:
    
    def __init__(self):
        self._criar_diretorios()
        self.data_hora = datetime.datetime.now()
        self.timestamp = self.data_hora.strftime("%Y%m%d_%H%M%S")
    
    def _criar_diretorios(self):
        os.makedirs(AUDITORIA_DIR, exist_ok=True)
        os.makedirs(RELATORIOS_DIR, exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)
    
    def _executar_comando(self, comando: str) -> Dict:
        try:
            resultado = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                'stdout': resultado.stdout,
                'stderr': resultado.stderr,
                'codigo': resultado.returncode,
                'sucesso': resultado.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                'stdout': '',
                'stderr': 'Timeout: comando excedeu 10 segundos',
                'codigo': -1,
                'sucesso': False
            }
        except Exception as e:
            return {
                'stdout': '',
                'stderr': str(e),
                'codigo': -1,
                'sucesso': False
            }
    
    def coletar_who(self) -> Dict:
        resultado = self._executar_comando('who')
        
        usuarios = []
        if resultado['sucesso'] and resultado['stdout']:
            for linha in resultado['stdout'].strip().split('\n'):
                if linha:
                    partes = linha.split()
                    if len(partes) >= 3:
                        usuarios.append({
                            'usuario': partes[0],
                            'tty': partes[1],
                            'data': ' '.join(partes[2:5]) if len(partes) >= 5 else ' '.join(partes[2:]),
                            'origem': partes[5] if len(partes) > 5 else 'local'
                        })
        
        return {
            'comando': 'who',
            'sucesso': resultado['sucesso'],
            'codigo': resultado['codigo'],
            'dados': usuarios,
            'total': len(usuarios),
            'raw': resultado['stdout']
        }
    
    def coletar_last(self) -> Dict:
        resultado = self._executar_comando('last -n 20')
        
        logins = []
        if resultado['sucesso'] and resultado['stdout']:
            for linha in resultado['stdout'].strip().split('\n'):
                if linha and not linha.startswith('wtmp') and not linha.startswith('btmp'):
                    partes = linha.split()
                    if len(partes) >= 3:
                        logins.append({
                            'usuario': partes[0],
                            'tty': partes[1],
                            'origem': partes[2] if len(partes) > 2 else 'local',
                            'detalhes': ' '.join(partes[3:]) if len(partes) > 3 else ''
                        })
        
        return {
            'comando': 'last -n 20',
            'sucesso': resultado['sucesso'],
            'codigo': resultado['codigo'],
            'dados': logins,
            'total': len(logins),
            'raw': resultado['stdout']
        }
    
    def coletar_ss_tulpn(self) -> Dict:
        resultado = self._executar_comando('ss -tulpn')
        
        portas = []
        if resultado['sucesso'] and resultado['stdout']:
            linhas = resultado['stdout'].strip().split('\n')
            if len(linhas) > 1:
                for linha in linhas[1:]:
                    if linha:
                        partes = linha.split()
                        if len(partes) >= 5:
                            endereco = partes[4] if len(partes) > 4 else ''
                            porta = ''
                            if ':' in endereco:
                                porta = endereco.split(':')[-1]
                            
                            servico = ''
                            if len(partes) > 6:
                                servico = ' '.join(partes[6:])
                            
                            portas.append({
                                'estado': partes[0],
                                'recvq': partes[1],
                                'sendq': partes[2],
                                'endereco': endereco,
                                'porta': porta,
                                'servico': servico
                            })
        
        return {
            'comando': 'ss -tulpn',
            'sucesso': resultado['sucesso'],
            'codigo': resultado['codigo'],
            'dados': portas,
            'total': len(portas),
            'raw': resultado['stdout']
        }
    
    def coletar_ip_a(self) -> Dict:
        resultado = self._executar_comando('ip a')
        
        interfaces = []
        interface_atual = None
        
        if resultado['sucesso'] and resultado['stdout']:
            for linha in resultado['stdout'].strip().split('\n'):
                if not linha:
                    continue
                
                if ':' in linha and not linha.strip().startswith(' '):
                    if interface_atual:
                        interfaces.append(interface_atual)
                    
                    partes = linha.split(':')
                    if len(partes) >= 3:
                        interface_atual = {
                            'indice': partes[0].strip(),
                            'nome': partes[1].strip(),
                            'flags': partes[2].strip() if len(partes) > 2 else '',
                            'ip': [],
                            'mac': ''
                        }
                
                elif interface_atual and 'inet ' in linha:
                    ip_info = linha.strip().split()
                    if len(ip_info) >= 2:
                        interface_atual['ip'].append(ip_info[1])
                
                elif interface_atual and 'link/ether' in linha:
                    mac_info = linha.strip().split()
                    if len(mac_info) >= 2:
                        interface_atual['mac'] = mac_info[1]
            
            if interface_atual:
                interfaces.append(interface_atual)
        
        return {
            'comando': 'ip a',
            'sucesso': resultado['sucesso'],
            'codigo': resultado['codigo'],
            'dados': interfaces,
            'total': len(interfaces),
            'raw': resultado['stdout']
        }
    
    def coletar_dados_disk(self) -> Dict:
        resultado = self._executar_comando('df -h')
        
        discos = []
        if resultado['sucesso'] and resultado['stdout']:
            linhas = resultado['stdout'].strip().split('\n')
            if len(linhas) > 1:
                for linha in linhas[1:]:
                    if linha:
                        partes = linha.split()
                        if len(partes) >= 6:
                            discos.append({
                                'sistema': partes[0],
                                'tamanho': partes[1],
                                'usado': partes[2],
                                'disponivel': partes[3],
                                'uso': partes[4],
                                'montagem': partes[5]
                            })
        
        return {
            'comando': 'df -h',
            'sucesso': resultado['sucesso'],
            'codigo': resultado['codigo'],
            'dados': discos,
            'total': len(discos),
            'raw': resultado['stdout']
        }
    
    def coletar_dados_memoria(self) -> Dict:
        resultado = self._executar_comando('free -h')
        
        memoria = []
        if resultado['sucesso'] and resultado['stdout']:
            linhas = resultado['stdout'].strip().split('\n')
            for linha in linhas:
                if linha and not linha.startswith('total'):
                    partes = linha.split()
                    if len(partes) >= 7:
                        memoria.append({
                            'tipo': partes[0].replace(':', ''),
                            'total': partes[1],
                            'usado': partes[2],
                            'livre': partes[3],
                            'compartilhado': partes[4] if len(partes) > 4 else '',
                            'cache': partes[5] if len(partes) > 5 else '',
                            'disponivel': partes[6] if len(partes) > 6 else ''
                        })
        
        return {
            'comando': 'free -h',
            'sucesso': resultado['sucesso'],
            'codigo': resultado['codigo'],
            'dados': memoria,
            'total': len(memoria),
            'raw': resultado['stdout']
        }
    
    def coletar_todos(self) -> Dict:
        print("Coletando informacoes do sistema...")
        
        dados = {
            'timestamp': self.data_hora.isoformat(),
            'data': self.data_hora.strftime("%Y-%m-%d %H:%M:%S"),
            'hostname': socket.gethostname(),
            'sistema': self._executar_comando('uname -a')['stdout'].strip(),
            'who': self.coletar_who(),
            'last': self.coletar_last(),
            'portas': self.coletar_ss_tulpn(),
            'redes': self.coletar_ip_a(),
            'discos': self.coletar_dados_disk(),
            'memoria': self.coletar_dados_memoria()
        }
        
        print("Coleta concluida!")
        return dados
    
    def salvar_relatorio(self, dados: Dict) -> str:
        nome_arquivo = f"auditoria_{self.timestamp}.json"
        caminho = os.path.join(RELATORIOS_DIR, nome_arquivo)
        
        with open(caminho, 'w') as f:
            json.dump(dados, f, indent=2, default=str)
        
        print(f"Relatorio salvo: {caminho}")
        
        self._salvar_relatorio_texto(dados)
        
        return caminho
    
    def _salvar_relatorio_texto(self, dados: Dict):
        nome_arquivo = f"auditoria_{self.timestamp}.txt"
        caminho = os.path.join(RELATORIOS_DIR, nome_arquivo)
        
        with open(caminho, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("  SECURECHAIN - RELATORIO DE AUDITORIA DO SISTEMA\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Data/Hora: {dados['data']}\n")
            f.write(f"Hostname: {dados['hostname']}\n")
            f.write(f"Sistema: {dados['sistema']}\n")
            f.write("\n" + "=" * 60 + "\n\n")
            
            f.write("USUARIOS LOGADOS (who):\n")
            f.write("-" * 40 + "\n")
            for usuario in dados['who']['dados']:
                f.write(f"  {usuario['usuario']} - {usuario['tty']} - {usuario['data']} - {usuario['origem']}\n")
            f.write(f"\nTotal: {dados['who']['total']} usuarios\n\n")
            
            f.write("HISTORICO DE LOGINS (last -n 20):\n")
            f.write("-" * 40 + "\n")
            for login in dados['last']['dados'][:10]:
                f.write(f"  {login['usuario']} - {login['tty']} - {login['origem']}\n")
            f.write(f"\nTotal: {dados['last']['total']} registros\n\n")
            
            f.write("PORTAS E SERVICOS EM ESCUTA (ss -tulpn):\n")
            f.write("-" * 40 + "\n")
            if dados['portas']['dados']:
                for porta in dados['portas']['dados']:
                    f.write(f"  Porta: {porta['porta']} - Estado: {porta['estado']} - {porta['servico']}\n")
            else:
                f.write("  Nenhuma porta em escuta\n")
            f.write(f"\nTotal: {dados['portas']['total']} portas\n\n")
            
            f.write("INTERFACES DE REDE (ip a):\n")
            f.write("-" * 40 + "\n")
            for iface in dados['redes']['dados']:
                f.write(f"  {iface['nome']} - {iface['flags']}\n")
                if iface['ip']:
                    f.write(f"    IPs: {', '.join(iface['ip'])}\n")
                if iface['mac']:
                    f.write(f"    MAC: {iface['mac']}\n")
            f.write(f"\nTotal: {dados['redes']['total']} interfaces\n\n")
            
            f.write("USO DE DISCO (df -h):\n")
            f.write("-" * 40 + "\n")
            for disco in dados['discos']['dados']:
                f.write(f"  {disco['sistema']} - {disco['montagem']} - {disco['uso']} usado ({disco['tamanho']})\n")
            f.write("\n")
            
            f.write("MEMORIA (free -h):\n")
            f.write("-" * 40 + "\n")
            for mem in dados['memoria']['dados']:
                f.write(f"  {mem['tipo']}: Total: {mem['total']} - Usado: {mem['usado']} - Disponivel: {mem['disponivel']}\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("  FIM DO RELATORIO\n")
            f.write("=" * 60 + "\n")
        
        print(f"Relatorio texto salvo: {caminho}")
    
    def registrar_na_blockchain(self, arquivo: str):
        try:
            from event_handler import EventHandler
            
            handler = EventHandler()
            handler.registrar_evento(
                evento='AUDITORIA',
                descricao=f'Relatorio de auditoria do sistema gerado',
                usuario='sistema',
                detalhes={'arquivo': arquivo, 'timestamp': self.timestamp}
            )
            print("Evento registrado na blockchain")
        except Exception as e:
            print(f"Erro ao registrar na blockchain: {e}")


def menu_principal():
    auditor = AuditoriaSistema()
    
    while True:
        print("\n" + "="*50)
        print("  SECURECHAIN - AUDITORIA DO SISTEMA")
        print("="*50)
        print("  1. Coletar e salvar relatorio completo")
        print("  2. Verificar usuarios logados (who)")
        print("  3. Verificar historico de logins (last)")
        print("  4. Verificar portas em escuta (ss -tulpn)")
        print("  5. Verificar interfaces de rede (ip a)")
        print("  6. Verificar uso de disco (df -h)")
        print("  7. Verificar memoria (free -h)")
        print("  8. Listar relatorios salvos")
        print("  0. Sair")
        print("="*50)
        
        opcao = input("Escolha uma opcao: ").strip()
        
        if opcao == "1":
            print("\n" + "="*50)
            dados = auditor.coletar_todos()
            arquivo = auditor.salvar_relatorio(dados)
            auditor.registrar_na_blockchain(arquivo)
            print("="*50)
            print("Auditoria concluida!")
            
        elif opcao == "2":
            dados = auditor.coletar_who()
            print("\nUSUARIOS LOGADOS:")
            print("-"*30)
            for usuario in dados['dados']:
                print(f"  {usuario['usuario']} - {usuario['tty']} - {usuario['data']}")
            print(f"\nTotal: {dados['total']} usuarios")
            
        elif opcao == "3":
            dados = auditor.coletar_last()
            print("\nHISTORICO DE LOGINS:")
            print("-"*30)
            for login in dados['dados'][:10]:
                print(f"  {login['usuario']} - {login['tty']} - {login['origem']}")
            print(f"\nTotal: {dados['total']} registros")
            
        elif opcao == "4":
            dados = auditor.coletar_ss_tulpn()
            print("\nPORTAS EM ESCUTA:")
            print("-"*30)
            for porta in dados['dados']:
                print(f"  Porta: {porta['porta']} - Estado: {porta['estado']}")
            print(f"\nTotal: {dados['total']} portas")
            
        elif opcao == "5":
            dados = auditor.coletar_ip_a()
            print("\nINTERFACES DE REDE:")
            print("-"*30)
            for iface in dados['dados']:
                print(f"  {iface['nome']} - {iface['flags']}")
                if iface['ip']:
                    print(f"    IPs: {', '.join(iface['ip'])}")
            print(f"\nTotal: {dados['total']} interfaces")
            
        elif opcao == "6":
            dados = auditor.coletar_dados_disk()
            print("\nUSO DE DISCO:")
            print("-"*30)
            for disco in dados['dados']:
                print(f"  {disco['montagem']}: {disco['uso']} usado ({disco['tamanho']})")
            
        elif opcao == "7":
            dados = auditor.coletar_dados_memoria()
            print("\nMEMORIA:")
            print("-"*30)
            for mem in dados['dados']:
                print(f"  {mem['tipo']}: Total: {mem['total']} - Disponivel: {mem['disponivel']}")
            
        elif opcao == "8":
            print("\nRELATORIOS SALVOS:")
            print("-"*30)
            relatorios = os.listdir(RELATORIOS_DIR)
            if relatorios:
                for r in sorted(relatorios, reverse=True):
                    caminho = os.path.join(RELATORIOS_DIR, r)
                    tamanho = os.path.getsize(caminho)
                    print(f"  {r} ({tamanho} bytes)")
            else:
                print("  Nenhum relatorio encontrado")
            
        elif opcao == "0":
            break
        else:
            print("Opcao invalida")


if __name__ == "__main__":
    menu_principal()
