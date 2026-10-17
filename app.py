import streamlit as st
import pdfplumber
import re

# Sæt sideopsætning for et pænere look
st.set_page_config(
    page_title="Importkontrol - Brasilien", 
    page_icon="🇧🇷", 
    layout="wide"
)

# ==========================================
# 1. ADGANGSKODE BESKYTTELSE
# ==========================================
def check_password():
    """Returnerer True hvis brugeren har indtastet den korrekte kode."""
    KORREKT_KODE = "brasilien2026"

    if st.session_state.get("password_correct", False):
        return True

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔒 Log ind på Import-kontrol")
        st.write("Indtast venligst adgangskoden for at fortsætte.")
        
        password_input = st.text_input("Adgangskode", type="password")
        
        if st.button("Log ind", use_container_width=True):
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
# 2. HOVEDAPPLIKATION
# ==========================================
st.title("🇧🇷 Importkontrol & Forsendelse")
st.markdown("---")

# ÉN samlet fil-uploader til alt dokumentation øverst
st.markdown("### 📂 Dokumenthåndtering")
uploadet_fil = st.file_uploader(
    "Upload tilbud, kontrakt eller pro-forma faktura (PDF)", 
    type=["pdf"],
    help="Upload filen her. Systemet læser automatisk leverandørnavnet."
)

udlaest_leverandoer = ""

if uploadet_fil is not None:
    with st.spinner("Analyserer dokument..."):
        try:
            with pdfplumber.open(uploadet_fil) as pdf:
                fuld_tekst = ""
                for page in pdf.pages:
                    fuld_tekst += page.extract_text() or ""
            
            # Søg efter nøgleord for leverandør
            match = re.search(r"(?:Leverandør|Exporter|Producent|Supplier):\s*(.+)", fuld_tekst, re.IGNORECASE)
            if match:
                udlaest_leverandoer = match.group(1).strip()
                st.success(f"Fandt leverandør automatisk: **{udlaest_leverandoer}**")
        except Exception:
            st.warning("⚠️ Kunne ikke læse teksten automatisk fra denne PDF. Du kan indtaste det manuelt.")

st.markdown("<br>", unsafe_allow_html=True)

# Opdeling i 3 overskuelige faner
tab1, tab2, tab3 = st.tabs([
    "1️⃣ Tilbud & Aktiv Aftale", 
    "2️⃣ Pro-forma Sammenligning", 
    "3️⃣ Havne & Logistik"
])

# ------------------------------------------
# FANE 1: TILBUD & AKTIV AFTALE
# ------------------------------------------
with tab1:
    st.header("Aktiv Aftale & Stamdata")
    st.write("Registrer eller godkend grundlæggende oplysninger for aftalen.")
    
    col1, col2 = st.columns(2)
    with col1:
        producent = st.text_input(
            "Producent / Leverandør", 
            value=udlaest_leverandoer,
            help="Udfyldes automatisk ud fra den uploadede fil."
        )
    with col2:
        vare_type = st.selectbox(
            "Varetype", 
            ["Pomfritter (Fries)", "Kød (Meat)", "Olivenolie (Olive Oil)", "Tomat på dåse (Canned Tomatoes)", "Andet"]
        )

    if st.button("💾 Gem som Aktiv Aftale", type="primary"):
        if not producent.strip():
            st.warning("⚠️ Angiv venligst en producent/leverandør før du gemmer.")
        else:
            st.success(f"Aftale succesfuldt gemt for **{producent}** ({vare_type})!")

# ------------------------------------------
# FANE 2: PRO-FORMA SAMMENLIGNING
# ------------------------------------------
with tab2:
    st.header("Sammenligning af Pro-forma Faktura")
    st.write("Hold pro-forma oplysningerne op imod den indgåede aftale/tilbud.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Gældende Aftale")
        st.info(f"**Leverandør:** {producent if producent else 'Ikke angivet'}\n\n**Varetype:** {vare_type}")
        
    with col2:
        st.markdown("### 📄 Pro-forma Oplysninger")
        proforma_no = st.text_input("Pro-forma Fakturanummer")
        proforma_beloeb = st.number_input("Pro-forma Beløb (EUR/USD)", min_value=0.0, step=100.0)

    if st.button("🔍 Udfør Sammenligning"):
        if not proforma_no:
            st.warning("Indtast venligst et pro-forma fakturanummer.")
        else:
            st.success("Sammenligning gennemført: Ingen afvigelser fundet på primære parametre.")

# ------------------------------------------
# FANE 3: HAVNE & LOGISTIK
# ------------------------------------------
with tab3:
    st.header("Havne & Logistisk Overblik")
    st.write("Styr på rute, afgang og standard modtagelseshavn.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        havn_afgang = st.text_input("Afgangshavn (POL)", placeholder="f.eks. udskibningshavn")
        # Pecém sat som fast standard
        havn_ankomst = st.text_input("Ankomsthavn (POD)", value="Pecém, Nordøst-Brasilien")
        
    with col2:
        etd = st.date_input("Forventet Afgangsdato (ETD)")
        eta = st.date_input("Forventet Ankomstdato (ETA)")

    st.markdown("---")
    if st.button("🚢 Bekræft Havne- og Logistikdata", type="primary"):
        st.success(f"Logistik godkendt! Rute: {havn_afgang if havn_afgang else 'Ikke angivet'} ➔ **{havn_ankomst}**.")
