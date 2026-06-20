# SecureChain Audit

Sistema de auditoria e monitoramento de integridade de arquivos com registro imutavel em blockchain local. Desenvolvido para ambientes Linux.

## Visao Geral

O SecureChain Audit combina autenticacao com controle de perfis, monitoramento de integridade via SHA-256, auditoria do sistema operacional e registro de eventos em uma blockchain local. Todas as acoes relevantes sao registradas de forma imutavel para garantir rastreabilidade.

## Estrutura do Projeto

```
securechain/
├── src/
│   ├── auth.py            # Autenticacao e controle de sessao
│   ├── monitor.py         # Monitoramento de integridade de arquivos
│   ├── blockchain.py      # Implementacao da blockchain local
│   ├── event_handler.py   # Integrador de eventos com a blockchain
│   └── validator.py       # Validacao e deteccao de corrupcao na blockchain
├── scripts/
│   ├── auditor.py         # Coleta de informacoes do sistema operacional
│   └── backup.sh          # Backup automatizado com criptografia AES-256
├── documentos/            # Arquivos monitorados pelo sistema
├── blockchain/            # Dados da blockchain e usuarios (JSON)
├── logs/                  # Logs de alteracoes e alertas
├── auditoria/relatorios/  # Relatorios gerados pelo auditor
└── setup_rf01.sh          # Script de configuracao inicial (grupos, usuarios, permissoes)
```

## Modulos

### auth.py

Sistema de autenticacao com bcrypt (12 rounds). Gerencia cadastro, login, logout e controle de sessao. Tres perfis disponiveis: admin, analista e visitante. Admins podem listar e remover usuarios. Dados persistidos em JSON.

### monitor.py

Monitora a integridade dos arquivos no diretorio `/documentos` usando SHA-256. Detecta criacao, modificacao e exclusao de arquivos comparando hashes de referencia. Gera alertas com niveis de severidade (CRITICO/ALTO) e suporta monitoramento continuo com intervalo configuravel.

### blockchain.py

Blockchain local para registro imutavel de eventos. Cada bloco contem hash SHA-256, referencia ao bloco anterior, timestamp e dados do evento. Garante que o historico de acoes nao pode ser alterado sem deteccao.

### event_handler.py

Camada de integracao entre os demais modulos e a blockchain. Registra eventos de login, logout, criacao/modificacao/exclusao de arquivos, backups, criacao de usuarios e alertas de seguranca.

### validator.py

Validador especializado da blockchain. Verifica integridade de blocos individuais e da cadeia completa. Detecta corrupcao, gera alertas e permite reparacao de blocos. Inclui funcao de simulacao de corrupcao para testes.

### auditor.py

Coleta informacoes do sistema operacional executando comandos Linux (who, last, ss -tulpn, ip a, df -h, free -h). Gera relatorios em JSON e texto plano, e registra a auditoria na blockchain.

### backup.sh

Script de backup automatizado. Compacta o diretorio de documentos, criptografa com AES-256-CBC via OpenSSL, salva metadados e registra o evento na blockchain. Mantem apenas os 5 backups mais recentes.

## Requisitos

- Python 3.8+
- Linux (comandos do auditor dependem de utilitarios Linux)
- bcrypt (`pip install bcrypt`)
- OpenSSL (para o script de backup)

## Configuracao Inicial

```bash
chmod +x setup_rf01.sh
sudo ./setup_rf01.sh
```

Esse script cria os grupos do sistema (securechain, securechain-analista, securechain-admin), os usuarios (administrador, analista, visitante), os diretorios necessarios e define as permissoes.

## Uso

Cada modulo pode ser executado individualmente via terminal:

```bash
python3 src/auth.py          # Sistema de autenticacao
python3 src/monitor.py       # Monitor de integridade
python3 src/validator.py     # Validador da blockchain
python3 scripts/auditor.py   # Auditoria do sistema
bash scripts/backup.sh       # Executar backup
```

Todos os modulos possuem menu interativo via CLI.

## Credenciais Padrao

| Usuario | Senha      | Perfil |
|---------|------------|--------|
| admin   |   admin    | admin  |