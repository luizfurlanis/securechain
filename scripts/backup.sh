DOCUMENTOS_DIR="/home/securechain/documentos"
BACKUP_DIR="/home/securechain/backup"
LOG_DIR="/home/securechain/logs"
BLOCKCHAIN_DIR="/home/securechain/blockchain"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="backup_${TIMESTAMP}"
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
ENCRYPTED_FILE="${BACKUP_DIR}/${BACKUP_NAME}.enc"

ENCRYPTION_PASSWORD=$(openssl rand -base64 32)

log() {
    local msg="$1"
    local level="${2:-INFO}"
    local log_file="${LOG_DIR}/backup_$(date +%Y%m%d).log"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $msg" | tee -a "$log_file"
}

registrar_blockchain() {
    local status="$1"
    local tamanho="$2"
    local arquivo="$3"
    
    python3 -c "
import sys
sys.path.append('/home/securechain/src')
from event_handler import EventHandler

handler = EventHandler()
if '$status' == 'SUCESSO':
    handler.registrar_backup('sistema', '$arquivo', $tamanho)
    print('Evento registrado na blockchain')
else:
    handler.registrar_evento(
        evento='BACKUP_FALHA',
        descricao='Falha no backup: $arquivo',
        usuario='sistema'
    )
    print('Evento de falha registrado na blockchain')
" 2>/dev/null
}

echo "SECURECHAIN - BACKUP SEGURO AUTOMATIZADO"

log "Criando diretórios necessários..." "INFO"
mkdir -p "$DOCUMENTOS_DIR" "$BACKUP_DIR" "$LOG_DIR" "$BLOCKCHAIN_DIR"

if [ ! -d "$DOCUMENTOS_DIR" ]; then
    log "Diretório de documentos não encontrado: $DOCUMENTOS_DIR" "ERRO"
    exit 1
fi

if [ -z "$(ls -A "$DOCUMENTOS_DIR")" ]; then
    log "Diretório de documentos está vazio. Criando arquivos de exemplo..." "AVISO"
    echo "Documento exemplo 1" > "$DOCUMENTOS_DIR/exemplo1.txt"
    echo "Documento exemplo 2" > "$DOCUMENTOS_DIR/exemplo2.txt"
    log "Arquivos de exemplo criados" "INFO"
fi

log "Compactando documentos de $DOCUMENTOS_DIR..." "INFO"
tar -czf "$BACKUP_FILE" -C "$DOCUMENTOS_DIR" . 2>&1

if [ $? -ne 0 ]; then
    log "ERRO: Falha ao compactar documentos" "ERRO"
    registrar_blockchain "FALHA" 0 "$BACKUP_NAME"
    exit 1
fi

FILE_SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || stat -f%z "$BACKUP_FILE" 2>/dev/null)
FILE_SIZE_KB=$((FILE_SIZE / 1024))
FILE_SIZE_MB=$((FILE_SIZE / 1048576))

log "Compactação concluída: $BACKUP_FILE ($FILE_SIZE_KB KB)" "INFO"

log "Criptografando backup com AES-256..." "INFO"

openssl enc -aes-256-cbc -salt -in "$BACKUP_FILE" -out "$ENCRYPTED_FILE" \
    -pass pass:"$ENCRYPTION_PASSWORD" 2>&1

if [ $? -ne 0 ]; then
    log "ERRO: Falha ao criptografar o backup" "ERRO"
    registrar_blockchain "FALHA" 0 "$BACKUP_NAME"
    exit 1
fi

rm -f "$BACKUP_FILE"

ENC_SIZE=$(stat -c%s "$ENCRYPTED_FILE" 2>/dev/null || stat -f%z "$ENCRYPTED_FILE" 2>/dev/null)
ENC_SIZE_KB=$((ENC_SIZE / 1024))
ENC_SIZE_MB=$((ENC_SIZE / 1048576))

log "Criptografia concluída: $ENCRYPTED_FILE ($ENC_SIZE_KB KB)" "INFO"

PASSWORD_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.key"
echo "SENHA: $ENCRYPTION_PASSWORD" > "$PASSWORD_FILE"
echo "DATA: $(date -Iseconds)" >> "$PASSWORD_FILE"
echo "ARQUIVO: $ENCRYPTED_FILE" >> "$PASSWORD_FILE"
chmod 600 "$PASSWORD_FILE"
log "Senha salva em: $PASSWORD_FILE" "INFO"

METADATA_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.meta"
cat > "$METADATA_FILE" << EOF
{
  "nome": "$BACKUP_NAME",
  "timestamp": "$(date -Iseconds)",
  "arquivo": "$ENCRYPTED_FILE",
  "tamanho_bytes": $ENC_SIZE,
  "tamanho_kb": $ENC_SIZE_KB,
  "tamanho_mb": $ENC_SIZE_MB,
  "arquivos_origem": "$DOCUMENTOS_DIR",
  "algoritmo": "AES-256-CBC",
  "senha_arquivo": "$PASSWORD_FILE"
}
EOF
chmod 600 "$METADATA_FILE"

log "Registrando backup na blockchain..." "INFO"
registrar_blockchain "SUCESSO" "$ENC_SIZE" "$BACKUP_NAME"

echo ""
echo "============================================================"
echo "  ✅ BACKUP CONCLUÍDO COM SUCESSO!"
echo "============================================================"
echo "  Arquivo criptografado: $ENCRYPTED_FILE"
echo "  Tamanho: $ENC_SIZE_MB MB ($ENC_SIZE_KB KB)"
echo "  Senha: $PASSWORD_FILE"
echo "  Metadados: $METADATA_FILE"
echo "============================================================"
echo ""

log "Backup concluído com sucesso!" "SUCESSO"

log "Limpando backups antigos (mantendo 5 mais recentes)..." "INFO"

cd "$BACKUP_DIR" || exit 1
ls -t backup_*.enc 2>/dev/null | tail -n +6 | while read -r old_backup; do
    rm -f "$old_backup"
    key_file=$(echo "$old_backup" | sed 's/\.enc$/.key/')
    rm -f "$key_file"
    meta_file=$(echo "$old_backup" | sed 's/\.enc$/.meta/')
    rm -f "$meta_file"
    log "Removido backup antigo: $old_backup" "INFO"
done

echo ""
log "Backup finalizado. Últimos 5 backups mantidos." "INFO"

exit 0