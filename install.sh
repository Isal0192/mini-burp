#!/bin/bash

# Warna untuk output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
  __  __ _       _ _                       
 |  \/  (_)     (_) |                      
 | \  / |_ _ __  _| |__  _   _ _ __ _ __   ___ 
 | |\/| | | '_ \| | '_ \| | | | '__| '_ \ / __|
 | |  | | | | | | | |_) | |_| | |  | |_) |\__ \
 |_|  |_|_|_| |_|_|_.__/ \__,_|_|  | .__/ |___/
                                   | |         
    Dev: Isal0192                  |_|         
EOF
echo -e "${NC}"

echo -e "${BLUE}[*] Memulai instalasi miniburps...${NC}"

# 1. Setup Termux Dependencies
echo -e "${BLUE}[*] Mengupdate paket Termux & menginstall dependencies...${NC}"
pkg update -y
pkg install -y python git rust binutils make clang
pkg install -y libffi openssl

# 2. Clone Repository (jika script ini dijalankan via curl dan folder belum ada)
INSTALL_DIR="$HOME/miniburps"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${GREEN}[*] Folder miniburps ditemukan, memperbarui...${NC}"
    cd "$INSTALL_DIR"
    git pull
else
    echo -e "${BLUE}[*] Cloning repository...${NC}"
    git clone https://github.com/Isal0192/mini-burp.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 3. Setup Python Virtual Environment (Optional but recommended, skipping for simplicity in Termux)
# Langsung install pip packages
echo -e "${BLUE}[*] Menginstall Python dependencies (ini mungkin agak lama)...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 4. Setup Shortcuts
echo -e "${BLUE}[*] Membuat shortcut command...${NC}"

# Shortcut untuk menjalankan aplikasi
cat <<EOF > $PREFIX/bin/miniburps
#!/bin/bash
cd $INSTALL_DIR
python app.py
EOF

# Shortcut untuk menjalankan proxy
cat <<EOF > $PREFIX/bin/prx
#!/bin/bash
cd $INSTALL_DIR
echo "Starting Proxy on 127.0.0.1:8081..."
mitmdump -s proxy.py --set block_global=false --listen-port 8081 --set dns_server=8.8.8.8
EOF

chmod +x $PREFIX/bin/miniburps
chmod +x $PREFIX/bin/prx

echo -e "${GREEN}"
echo "========================================="
echo "   INSTALASI SUKSES!"
echo "========================================="
echo -e "${NC}"
echo "Cara Penggunaan:"
echo "1. Ketik 'miniburps' untuk menjalankan dashboard."
echo "2. Ketik 'prx' (di tab baru) untuk menjalankan proxy."
echo ""
echo "Dashboard: http://127.0.0.1:5000"
echo ""
