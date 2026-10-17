import streamlit as st

# --- ADGANGSKODE BESKYTTELSE ---
def check_password():
    """Returnerer True hvis brugeren har indtastet den korrekte kode."""
    KORREKT_KODE = "brasilien2026"  # Skift denne til din ønskede kode!

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("## 🔒 Log ind på Import-kontrol")
    st.write("Indtast adgangskoden for at få adgang til systemet.")
    
    password_input = st.text_input("Adgangskode", type="password")
    
    if st.button("Log ind"):
        if password_input == KORREKT_KODE:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ Forkert adgangskode. Prøv igen.")
            
    return False

if not check_password():
    st.stop()
# ------------------------------
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

# 1. Lav en boks hvor man kan uploade en fil (f.eks. en PDF)
uploaded_file = st.file_uploader("Upload dokument (f.eks. PDF)", type=["pdf"])

# 2. Start med et tomt leverandør-felt
fundet_leverandoer = ""

# 3. Hvis der ER uploadet en fil, kigger vi i den
if uploaded_file is not None:
    # Her kan koden læse filen (eksempelvis hvis det er en PDF)
    # Hvis filen f.eks. indeholder teksten "Leverandør: [Navn]", kan vi fange det:
    import pdfplumber
    
    with pdfplumber.open(uploaded_file) as pdf:
        samlet_tekst = ""
        for page in pdf.pages:
            samlet_tekst += page.extract_text() or ""
            
    # Simpelt tjek: Hvis ordet "European Food Corp" står i filen, sætter vi det ind automatisk
    if "European Food Corp" in samlet_tekst:
        fundet_leverandoer = "European Food Corp"
    elif "En anden leverandør" in samlet_tekst:
        fundet_leverandoer = "En anden leverandør"

# 4. Selve tekstfeltet (hvis koden fandt noget i filen, står det heri automatisk, ellers kan du selv skrive det)
producent = st.text_input("Producent / Leverandør", value=fundet_leverandoer)
vare_type = st.selectbox("Varetype", ["Pomfritter (Fries)", "Kød (Meat)", "Olivenolie (Olive Oil)", "Tomat på dåse (Canned Tomatoes)", "Andet"])
if st.button("💾 Gem som Aktiv Aftale"):
        st.success("✅ Aftale er gemt som standard for denne session!")

with tab2:
    st.header("Trin 2: Proforma Faktura Kontrol")
    st.file_uploader("Upload Proforma Faktura (PDF)", type=["pdf", "png", "jpg"], key="proforma")

with tab3:
    st.header("Trin 3: Frigivelsesdokumenter til Brasilien")
    st.file_uploader("Upload alle frigivelsesdokumenter", type=["pdf", "png", "jpg"], accept_multiple_files=True, key="frigivelse")
    
