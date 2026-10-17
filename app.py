import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Brasilien Import Kontrol",
    page_icon="🇧🇷",
    layout="wide"
)

st.title("🇧🇷 Import & Frigivelses-Kontrol (Fødevarer til Brasilien)")
st.markdown("Verifikation af tilbud, proforma og havnedokumenter mod brasilianske krav (MAPA / Receita Federal).")

st.sidebar.header("⚙️ Logistik & Havnevalg")
available_ports = [
    "Porto do Pecém (BRPEC)",
    "Porto de Suape (BRSUAP)",
    "Porto de Salvador (BRSSA)",
    "Porto de Santos (BRSSZ)",
    "Porto de Paranaguá (BRPNG)"
]
valgt_udlosningshavn = st.sidebar.selectbox("Standard Udlosningshavn:", options=available_ports, index=0)

tab1, tab2, tab3 = st.tabs([
    "1️⃣ Tilbud & Aftale (Drag & Drop)",
    "2️⃣ Proforma Kontrol",
    "3️⃣ Brasiliansk Havne- & Fødevarekontrol"
])

with tab1:
    st.header("Trin 1: Upload Tilbud / Aftale")
    uploaded_tilbud = st.file_uploader("Træk tilbudsfil hertil", type=["pdf", "txt", "docx", "png", "jpg"], key="tilbud")
    producent = st.text_input("Producent / Leverandør", value="European Food Corp")
    vare_type = st.selectbox("Varetype", ["Pomfritter (Fries)", "Kød (Meat)", "Olivenolie (Olive Oil)", "Tomat på dåse (Canned Tomatoes)", "Andet"])
    if st.button("💾 Gem som Aktiv Aftale"):
        st.success("✅ Aftale er gemt som standard for denne session!")

with tab2:
    st.header("Trin 2: Proforma Faktura Kontrol")
    st.file_uploader("Upload Proforma Faktura (PDF)", type=["pdf", "png", "jpg"], key="proforma")

with tab3:
    st.header("Trin 3: Frigivelsesdokumenter til Brasilien")
    st.file_uploader("Upload alle frigivelsesdokumenter", type=["pdf", "png", "jpg"], accept_multiple_files=True, key="frigivelse")
    