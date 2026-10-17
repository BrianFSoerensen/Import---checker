import streamlit as st
import pdfplumber
import re

# ==========================================
# 1. ADGANGSKODE BESKYTTELSE (LÆGGES ØVERST)
# ==========================================
def check_password():
    """Returnerer True hvis brugeren har indtastet den korrekte kode."""
    KORREKT_KODE = "brasilien2026"

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
# ==========================================


# ==========================================
# 2. SELVE APPLIKATIONEN (ÉNSAMLET UPLOAD)
# ==========================================
st.title("📋 Importkontrol")

# ÉN samlet fil-uploader til alle informationer
uploadet_fil = st.file_uploader("Upload tilbud og/eller kontrakt (PDF)", type=["pdf"])

udlaest_leverandoer = ""

# Hvis en fil bliver uploadet, forsøger vi at læse teksten igennem
if uploadet_fil is not None:
    try:
        with pdfplumber.open(uploadet_fil) as pdf:
            fuld_tekst = ""
            for page in pdf.pages:
                fuld_tekst += page.extract_text() or ""
        
        # Søg efter nøgleord som "Leverandør:", "Exporter:", "Producent:" eller "Supplier:"
        match = re.search(r"(?:Leverandør|Exporter|Producent|Supplier):\s*(.+)", fuld_tekst, re.IGNORECASE)
        if match:
            udlaest_leverandoer = match.group(1).strip()
    except Exception:
        st.warning("Kunne ikke automatisk læse teksten fra den uploadede PDF.")

# Tekstfelt til Producent / Leverandør
# (Starter enten med det udlæste navn eller er helt tomt, så man selv kan indtaste)
producent = st.text_input(
    "Producent / Leverandør", 
    value=udlaest_leverandoer,
    help="Udfyldes automatisk ud fra filen hvis muligt. Kan rette manuelt."
)

# Varetype valg
vare_type = st.selectbox(
    "Varetype", 
    ["Pomfritter (Fries)", "Kød (Meat)", "Olivenolie (Olive Oil)", "Tomat på dåse (Canned Tomatoes)", "Andet"]
)

# Gem-knap
if st.button("💾 Gem som Aktiv Aftale"):
    if producent.strip() == "":
        st.warning("⚠️ Angiv venligst en producent/leverandør før du gemmer.")
    else:
        st.success(f"Aftale gemt for {producent} med varetype {vare_type}!")
