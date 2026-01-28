# miniburps

**miniburps** adalah alat pentesting web sederhana untuk Android (Termux).

Saya membuat tools ini karena merasa butuh cara yang praktis untuk melakukan analisis HTTP request secara manual langsung dari HP. Fitur-fiturnya terinspirasi dari workflow dasar Burp Suite, tapi dibuat seringan mungkin agar nyaman dijalankan di Termux tanpa bikin HP nge-lag.

**Dev:** Isal0192

## Fitur Saat Ini

*   **Proxy:** Menangkap traffic HTTP/HTTPS (menggunakan engine `mitmproxy`).
*   **Repeater:** Edit request, kirim ulang, dan lihat responnya (dilengkapi highlight warna agar mudah dibaca).
*   **Fuzzer:** Untuk brute-force parameter atau mencari direktori tersembunyi. Bisa pakai wordlist bawaan atau punya sendiri.
*   **Decoder:** Tools bantu untuk encode/decode URL, Base64, Hex, dan Hashing.

## Instalasi

Cara paling gampang, copy-paste perintah ini di terminal Termux:

```bash
curl -sL https://raw.githubusercontent.com/Isal0192/mini-burp/main/install.sh | bash
```

Atau kalau mau install manual:

1.  Clone repo ini: `git clone https://github.com/Isal0192/mini-burp.git`
2.  Masuk folder: `cd mini-burp`
3.  Install dependency: `pip install -r requirements.txt`

## Cara Pakai

Tools ini terdiri dari dua bagian: Dashboard (Web UI) dan Proxy (Background Process).

1.  **Jalankan Dashboard:**
    Ketik `miniburps` di terminal.
    Buka browser dan buka alamat: `http://127.0.0.1:5000`

2.  **Jalankan Proxy:**
    Buka session baru di Termux, lalu ketik `prx`.
    *   Setting WiFi HP: Proxy Manual ke `127.0.0.1` port `8081`.
    *   Jangan lupa install sertifikat `mitm.it` kalau mau intercept HTTPS.

## Catatan

Project ini masih aktif dikembangkan. Kalau nemu bug atau punya ide fitur yang sekiranya berguna buat pentesting di HP, silakan open issue atau kontak saya.

Gunakan tools ini secara bijak dan hanya untuk tujuan edukasi atau testing sistem milik sendiri.

---
© 2026 Isal0192