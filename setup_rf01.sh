echo "Configuração SecureChain Audit"

echo "criando grupos"
sudo groupadd securechain 2>/dev/null
sudo groupadd securechain-analista 2>/dev/null
sudo groupadd securechain-admnin 2>/dev/null

echo "criando usuarios"
sudo useradd -m -G securechain,securechain-analista,securechain-admin,sudo administrador 2>/dev/null
sudo useradd -m -G securechain,securechain-analista analista 2>/dev/null
sudo useradd -m -G securechain visitante 2>/dev/null

echo "criando diretórios"
sudo mkdir -p src documentos backup blockchain logs auditoria/relatorios scripts

echo "definindo permissões"
sudo chown -R administrador:securechain /home/securechain
sudo chmod 750 src/ documentos/ backup/ blockchain/ logs/ auditoria/relatorios/ scripts/
 
