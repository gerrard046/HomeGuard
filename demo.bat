@echo off
REM ============================================================
REM  demo.bat - Jalankan demo HomeGuard sekali klik (Windows)
REM ------------------------------------------------------------
REM  1) Membuka server IoT tiruan di jendela terpisah
REM  2) Menjalankan antarmuka web Streamlit
REM  Tutup jendela "Server Tiruan" untuk menghentikan demo.
REM ============================================================

cd /d "%~dp0"

echo.
echo  ============================================
echo   HomeGuard - Menyiapkan demo...
echo  ============================================
echo.

REM Jendela 1: server IoT tiruan (tetap hidup)
start "HomeGuard - Server Tiruan" cmd /k python demo_server.py

REM Beri jeda agar server siap
timeout /t 2 /nobreak >nul

echo  Server tiruan aktif. Membuka antarmuka web...
echo  Di browser: mode "Host tunggal", IP 127.0.0.1,
echo  Port 2323,8080,8554, lalu klik "Mulai Pindai".
echo.

REM Jendela ini: jalankan Streamlit
python -m streamlit run app.py
