# Setup & Import Library
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

# Konfigurasi halaman streamlit
st.set_page_config(layout="wide")

# Tema visual untuk seaborn
sns.set(style='dark')
sns.set_context("poster", font_scale=1.0) 

# Helper function untuk membuat dataframe yang diperlukan untuk analisis

# Mengelompokkan data berdasarkan bulan untuk menghitung total pesanan dan pendapatan
def create_monthly_orders_df(df):
    monthly_orders_df = df.resample(rule='ME', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    
    # Format index waktu menjadi Tahun-Bulan (YYYY-MM)
    monthly_orders_df.index = monthly_orders_df.index.strftime('%Y-%m')
    monthly_orders_df = monthly_orders_df.reset_index()
    monthly_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)
    return monthly_orders_df

# Menghitung jumlah produk terjual berdasarkan kategori produk
def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("product_category_name_english").product_id.count().sort_values(ascending=False).reset_index()
    sum_order_items_df.rename(columns={"product_id": "quantity"}, inplace=True)
    return sum_order_items_df

# Menghitung jumlah pelanggan unik berdasarkan negara bagian (state)
def create_by_state_df(df):
    bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bystate_df

# Menghitung jumlah pelanggan unik berdasarkan kota (city)
def create_by_city_df(df):
    bycity_df = df.groupby(by="customer_city").customer_id.nunique().reset_index()
    bycity_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bycity_df

# Mencari kombinasi dua kategori produk yang paling sering dibeli dalam satu pesanan
def create_product_pairs_df(df):
    # Ambil kolom yang dibutuhkan dan hapus missing values
    transaction_df = df[['order_id', 'product_category_name_english']].dropna()
    
    # Melakukan self-merge pada order_id untuk menemukan produk yang dibeli bersamaan
    product_pairs = pd.merge(
        transaction_df,
        transaction_df,
        on='order_id',
        suffixes=('_A', '_B')
    )
    # Mencegah duplikasi kombinasi (misal: A & B sama dengan B & A) dan mencegah produk dipasangkan dengan dirinya sendiri
    product_pairs = product_pairs[product_pairs['product_category_name_english_A'] < product_pairs['product_category_name_english_B']]
    
    # Menghitung frekuensi kemunculan pasangan produk
    product_pairs_df = product_pairs.groupby(['product_category_name_english_A', 'product_category_name_english_B']).size().reset_index(name='frequency')
    product_pairs_df = product_pairs_df.sort_values(by='frequency', ascending=False).head(5)
    
    # Menggabungkan nama produk untuk keperluan visualisasi
    product_pairs_df['product_pair'] = product_pairs_df['product_category_name_english_A'] + " & " + product_pairs_df['product_category_name_english_B']
    return product_pairs_df

# Membuat dataframe RFM (Recency, Frequency, Monetary) untuk analisis pelanggan
def create_rfm_df(df):
    # Menentukan tanggal acuan perhitungan (1 hari setelah transaksi terakhir)
    recent_date = df['order_purchase_timestamp'].max() + pd.DateOffset(days=1)
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": lambda x: (recent_date - x.max()).days, # Recency
        "order_id": "nunique",                                              # Frequency
        "price": "sum"                                                      # Monetary                            
    })
    rfm_df.columns = ["customer_unique_id", "recency", "frequency", "monetary"]
    return rfm_df


# Data Loading 

# Memuat data utama dan memastikan format datetime yang benar.
# Menggunakan st.cache_data agar data tidak dimuat ulang setiap interaksi UI.
@st.cache_data
def load_data():
    all_df = pd.read_csv("main_data.csv")
    all_df["order_purchase_timestamp"] = pd.to_datetime(all_df["order_purchase_timestamp"])
    return all_df

all_df = load_data()

# Mendapatkan rentang tanggal untuk filter di sidebar
min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

# Sidebar untuk filter data berdasarkan rentang waktu
with st.sidebar:
    st.image("https://storage.googleapis.com/kaggle-organizations/1942/thumbnail.png?r=51")
    st.header("Filter Data")
    
    # Input rentang tanggal dari pengguna
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# Filter dataframe utama berdasarkan input tanggal
main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & 
                (all_df["order_purchase_timestamp"] <= str(end_date))]

# Persiapan data agregasi berdasarkan data yang sudah difilter
monthly_orders_df = create_monthly_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bystate_df = create_by_state_df(main_df)
bycity_df = create_by_city_df(main_df)
product_pairs_df = create_product_pairs_df(main_df)
rfm_df = create_rfm_df(main_df)


# Main Page (UI Dashboard)
st.title("E-Commerce Dashboard Analysis")

st.markdown("""
    <div style="font-size: 24px; margin-bottom: 20px;">
        Dashboard ini menampilkan performa penjualan, demografi pelanggan, dan analisis produk.
    </div>
""", unsafe_allow_html=True)

# Menampilkan metrik utama (Total Orders, Total Revenue, Average Monthly Revenue) dalam tiga kolom
col1, col2, col3 = st.columns(3)

with col1:
    total_orders = monthly_orders_df.order_count.sum()
    st.markdown(f"""
    <div style="font-size: 20px; color: #fafafa; margin-bottom: 5px;">Total Orders</div>
    <div style="font-size: 35px; color: #fafafa; font-weight: bold;">{total_orders}</div>
    """, unsafe_allow_html=True)

with col2:
    total_revenue = format_currency(monthly_orders_df.revenue.sum(), "BRL", locale='pt_BR') 
    st.markdown(f"""
    <div style="font-size: 20px; color: #fafafa; margin-bottom: 5px;">Total Revenue</div>
    <div style="font-size: 35px; color: #fafafa; font-weight: bold; word-wrap: break-word;">{total_revenue}</div>
    """, unsafe_allow_html=True)

with col3:
    avg_revenue = format_currency(monthly_orders_df.revenue.mean(), "BRL", locale='pt_BR')
    st.markdown(f"""
    <div style="font-size: 20px; color: #fafafa; margin-bottom: 5px;">Avg Monthly Revenue</div>
    <div style="font-size: 35px; color: #fafafa; font-weight: bold;">{avg_revenue}</div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Custom styling untuk ukuran font pada tab Streamlit
st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Membuat tiga tab untuk analisis tren & wilayah, analisis produk, dan analisis pelanggan (RFM)
tab1, tab2, tab3 = st.tabs([" 📈 Tren & Wilayah ", " 📦 Analisis Produk ", " 👤 Analisis Pelanggan (RFM) "])

# Visualisasi tren penjualan bulanan dan distribusi pelanggan berdasarkan wilayah (state & city)
with tab1:
    st.subheader("Tren Penjualan Bulanan")
    fig, ax = plt.subplots(figsize=(24, 10)) 
    ax.plot(
        monthly_orders_df["order_purchase_timestamp"],
        monthly_orders_df["order_count"],
        marker='o', 
        linewidth=5,
        color="#72BCD4"
    )
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray', alpha=0.5)
    ax.set_title("Number of Orders per Month", loc="center", fontsize=40)
    ax.tick_params(axis='x', labelsize=25, rotation=45)
    ax.tick_params(axis='y', labelsize=25)
    st.pyplot(fig)

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    FIG_SIZE = (20, 15) 
    
    with col1:
        st.subheader("Customer by State")
        fig, ax = plt.subplots(figsize=FIG_SIZE)
        
        # Memberikan warna khusus untuk state dengan jumlah pelanggan terbanyak, sementara yang lain diberi warna netral
        colors_ = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
        sns.barplot(
            x="customer_count", 
            y="customer_state",
            data=bystate_df.sort_values(by="customer_count", ascending=False).head(8),
            palette=colors_,
            hue="customer_state",
            legend=False,
            ax=ax
        )
        ax.set_title("Number of Customer by States", loc="center", fontsize=35)
        ax.set_ylabel(None)
        ax.set_xlabel(None)
        ax.tick_params(axis='y', labelsize=30)
        ax.tick_params(axis='x', labelsize=25)
        st.pyplot(fig)
        
    with col2:
        st.subheader("Customer by City")
        fig, ax = plt.subplots(figsize=FIG_SIZE)
        
        # Memberikan warna khusus untuk city dengan jumlah pelanggan paling banyak, sementara yang lain diberi warna netral
        colors_ = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
        sns.barplot(
            x="customer_count", 
            y="customer_city",
            data=bycity_df.sort_values(by="customer_count", ascending=False).head(8),
            palette=colors_,
            hue="customer_city",
            legend=False,
            ax=ax
        )
        ax.set_title("Number of Customer by Cities", loc="center", fontsize=35)
        ax.set_ylabel(None)
        ax.set_xlabel(None)
        ax.tick_params(axis='y', labelsize=30)
        ax.tick_params(axis='x', labelsize=25)
        st.pyplot(fig)

# Visualisasi produk terlaris, kurang laris, dan pola pembelian produk bersamaan (product bundling)
with tab2:
    st.subheader("Produk Terlaris & Kurang Laris")
    col1, col2 = st.columns(2)
    
    CHART_SIZE = (24, 12)

    with col1:
        st.markdown("#### Best Performing Product")
        fig, ax = plt.subplots(figsize=CHART_SIZE)
        
        # Memberikan warna khusus untuk produk dengan jumlah penjualan terbanyak, sementara yang lain diberi warna netral
        colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
        sns.barplot(
            x="quantity", 
            y="product_category_name_english", 
            data=sum_order_items_df.head(5), 
            palette=colors, 
            hue="product_category_name_english",
            legend=False,
            ax=ax
        )
        ax.set_ylabel(None)
        ax.set_xlabel(None)
        ax.tick_params(axis='y', labelsize=30)
        ax.tick_params(axis='x', labelsize=25)
        st.pyplot(fig)
        
    with col2:
        st.markdown("#### Worst Performing Product")
        fig, ax = plt.subplots(figsize=CHART_SIZE)
        
        # Memberikan warna khusus untuk produk dengan jumlah penjualan paling sedikit, sementara yang lain diberi warna netral
        colors_worst = ["#D9534F", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
        sns.barplot(
            x="quantity", 
            y="product_category_name_english", 
            data=sum_order_items_df.sort_values(by="quantity", ascending=True).head(5), 
            palette=colors_worst, 
            hue="product_category_name_english",
            legend=False,
            ax=ax
        )
        ax.set_ylabel(None)
        ax.set_xlabel(None)
        ax.invert_xaxis()
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()
        ax.tick_params(axis='y', labelsize=30)
        ax.tick_params(axis='x', labelsize=25)
        st.pyplot(fig)
    
    st.markdown("---")
    
    # Visualisasi produk bundling (kombinasi produk yang sering dibeli bersamaan)
    st.subheader("Pola Pembelian Produk Bersamaan (Product Bundling)")
    if not product_pairs_df.empty:
        colors_bundling = ["#72BCD4" if i == 0 else "#D3D3D3" for i in range(len(product_pairs_df))]
        
        fig, ax = plt.subplots(figsize=(24, 10))
        sns.barplot(
            x="frequency",
            y="product_pair",
            data=product_pairs_df,
            palette=colors_bundling,
            hue="product_pair",
            legend=False,
            ax=ax
        )
        ax.set_title("Top 5 Most Common Product Combinations", fontsize=40)
        ax.set_xlabel("Frequency (Transactions)", fontsize=30)
        ax.set_ylabel(None)
        ax.tick_params(axis='y', labelsize=25)
        ax.tick_params(axis='x', labelsize=25)
        st.pyplot(fig)
    else:
        st.text("Tidak ada data kombinasi produk yang cukup untuk ditampilkan.")

# Visualisasi pelanggan terbaik berdasarkan parameter RFM (Recency, Frequency, Monetary)
with tab3:
    st.subheader("Best Customer Based on RFM Parameters")
    
    col1, col2, col3 = st.columns(3)
    RFM_SIZE = (20, 20)

    # Pada recency, nilai lebih kecil lebih baik (pelanggan yang lebih baru).
    # Sedangkan pada frequency dan monetary, nilai lebih besar lebih baik (pelanggan yang lebih sering membeli dan menghasilkan pendapatan lebih banyak). 
    with col1:
        st.markdown('<div style="font-size: 25px; font-weight: bold; margin-bottom: 10px;">By Recency (Days)</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=RFM_SIZE)
        sns.barplot(
            y="recency", 
            x="customer_unique_id", 
            data=rfm_df.sort_values(by="recency", ascending=True).head(5), 
            palette=["#72BCD4"]*5, 
            hue="customer_unique_id",
            legend=False,
            ax=ax
        )
        ax.set_ylabel(None)
        ax.set_xlabel(None)
        ax.tick_params(axis='x', labelsize=25, rotation=90)
        ax.tick_params(axis='y', labelsize=25)
        st.pyplot(fig)
        
    with col2:
        st.markdown('<div style="font-size: 25px; font-weight: bold; margin-bottom: 10px;">By Frequency</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=RFM_SIZE)
        sns.barplot(
            y="frequency", 
            x="customer_unique_id", 
            data=rfm_df.sort_values(by="frequency", ascending=False).head(5), 
            palette=["#72BCD4"]*5, 
            hue="customer_unique_id",
            legend=False,
            ax=ax
        )
        ax.set_ylabel(None)
        ax.set_xlabel(None)
        ax.tick_params(axis='x', labelsize=25, rotation=90)
        ax.tick_params(axis='y', labelsize=25)
        st.pyplot(fig)
        
    with col3:
        st.markdown('<div style="font-size: 25px; font-weight: bold; margin-bottom: 10px;">By Monetary</div>', unsafe_allow_html=True)
        fig, ax = plt.subplots(figsize=RFM_SIZE)
        sns.barplot(
            y="monetary", 
            x="customer_unique_id", 
            data=rfm_df.sort_values(by="monetary", ascending=False).head(5), 
            palette=["#72BCD4"]*5, 
            hue="customer_unique_id",
            legend=False,
            ax=ax
        )
        ax.set_ylabel(None)
        ax.set_xlabel(None)
        ax.tick_params(axis='x', labelsize=25, rotation=90)
        ax.tick_params(axis='y', labelsize=25)
        st.pyplot(fig)

st.caption('Dicoding Submission: Proyek Analisis Data - Louis Januardy Citra')