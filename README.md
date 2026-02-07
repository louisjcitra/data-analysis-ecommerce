# Proyek Analisis Data: E-Commerce Public Dataset

Proyek ini melakukan analisis mendalam terhadap data e-commerce Olist di Brasil. Fokus utama analisis adalah untuk memberikan gambaran menyeluruh mengenai performa bisnis, perilaku pelanggan, dan segmentasi pasar melalui parameter RFM.

## Struktur Direktori

- **dashboard/**: Berisi file utama untuk menjalankan dashboard Streamlit (`dashboard.py`) dan data yang telah dibersihkan (`main_data.csv`).
- **data/**: Berisi dataset mentah dalam format .csv.
- **Proyek Analisis Data.ipynb**: File notebook yang berisi proses analisis data mulai dari Data Wrangling, EDA, hingga Visualisasi.
- **README.md**: File dokumentasi proyek ini.

## Setup Environment - Anaconda

Jika menggunakan Anaconda/Miniconda, ikuti langkah berikut:
1. **Buka Terminal/Command Prompt**:
   Pastikan Anda sudah berada di dalam direktori folder proyek ini (di mana file `requirements.txt` berada).

2.  **Buat Environment Baru**:
    ```bash
    conda create --name main-ds python=3.9
    ```

3.  **Aktifkan Environment**:
    ```bash
    conda activate main-ds
    ```

4.  **Install Library yang Dibutuhkan**:
    Jalankan:
    ```bash
    pip install -r requirements.txt
    ```

## Cara Menjalankan Dashboard

Setelah environment aktif dan library terinstall, jalankan perintah berikut dari terminal:

```bash
streamlit run dashboard/dashboard.py

