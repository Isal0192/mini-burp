# miniburps 🍔

**miniburps** adalah suite *Mobile Penetration Testing* berbasis Python untuk Android (Termux) yang terinspirasi dari workflow Burp Suite. Alat ini dirancang ringan, modular, dan fokus pada pengujian manual tanpa ketergantungan sistem yang berat.

Developed by **Isal0192**.

![Dashboard](https://via.placeholder.com/800x400?text=miniburps+Dashboard) 
*(Screenshot placeholder)*

## 🚀 Fitur Utama

*   **Dashboard:** Profiling dan panduan cepat.
*   **Proxy Interceptor:** Menangkap traffic HTTP/HTTPS secara real-time (powered by `mitmproxy`).
*   **Repeater:** Edit & Resend request dengan editor canggih (Syntax Highlighting + Beautify).
*   **Fuzzer (Intruder):** Brute-force parameter/direktori dengan wordlist bawaan atau kustom.
*   **Decoder:** Encode/Decode (URL, Base64, Hex, HTML) & Hashing (SHA256).

## 📥 Instalasi Cepat (Termux)

Salin dan jalankan perintah berikut di terminal Termux Anda:

```bash
curl -sL https://raw.githubusercontent.com/Isal0192/mini-burp/main/install.sh | bash
```

## 🛠 Instalasi Manual

Jika Anda lebih suka cara manual:

1.  **Clone Repository:**
    ```bash
    git clone https://github.com/Isal0192/mini-burp.git
    cd mini-burp
    ```

2.  **Jalankan Installer:**
    ```bash
    chmod +x install.sh
    ./install.sh
    ```

## 🎮 Cara Penggunaan

1.  **Jalankan Dashboard:**
    Ketik perintah berikut untuk memulai web server:
    ```bash
    miniburps
    ```
    Buka browser dan akses: `http://127.0.0.1:5000`

2.  **Jalankan Proxy:**
    Buka sesi terminal baru (geser layar Termux dari kiri ke kanan -> New Session), lalu ketik:
    ```bash
    prx
    ```
    *   Set Wi-Fi Proxy HP Anda ke `127.0.0.1` port `8081`.
    *   Kunjungi `mitm.it` untuk install sertifikat HTTPS.

## 🤝 Kontribusi

Pull requests dipersilakan. Untuk perubahan besar, harap buka issue terlebih dahulu untuk mendiskusikan apa yang ingin Anda ubah.

## ⚠️ Disclaimer

Alat ini dibuat untuk tujuan **edukasi dan pengujian keamanan etis** saja. Pengembang (Isal0192) tidak bertanggung jawab atas penyalahgunaan alat ini untuk menyerang target tanpa izin.

---
© 2026 miniburps by Isal0192
