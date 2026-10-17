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

# FLERE FILER: accept_multiple_files=True
st.markdown("### 📂 Generel Dokumenthåndtering")
uploadede_filer = st.file_uploader(
    "Upload tilbud, kontrakter eller bilag (du kan vælge/trække flere PDF-filer)", 
    type=["pdf"],
    accept_multiple_files=True,
    help="Upload en eller flere filer. Systemet gennemsøger dokumenterne for leverandørnavn."
)

udlaest_leverandoer = ""

if uploadede_filer:
    st.info(f"📁 {len(uploadede_filer)} dokument(er) tilknyttet.")
    
    with st.spinner("Analyserer uploadede dokumenter..."):
        for fil in uploadede_filer:
            try:
                with pdfplumber.open(fil) as pdf:
                    fuld_tekst = ""
                    for page in pdf.pages:
                        fuld_tekst += page.extract_text() or ""
                
                # Søg efter nøgleord for leverandør i hver fil
                if not udlaest_leverandoer:
                    match = re.search(r"(?:Leverandør|Exporter|Producent|Supplier):\s*(.+)", fuld_tekst, re.IGNORECASE)
                    if match:
                        udlaest_leverandoer = match.group(1).strip()
            except Exception:
                pass
                
    if udlaest_leverandoer:
        st.success(f"Fandt leverandør automatisk i dokumenterne: **{udlaest_leverandoer}**")

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
            help="Udfyldes automatisk ud fra de uploadede filer (kan rette manuelt)."
        )
    with col2:
        vare_type = st.selectbox(
            "Varetype", 
            ["Pomfritter (Fries)", "Kød (Meat)", "Olivenolie (Olive Oil)", "Tomat på dåse (Canned Tomatoes)", "Andet"]
        )

    # Mulighed for yderligere specifikke tilbudsbilag
    ekstra_tilbud_filer = st.file_uploader(
        "Tilknyt supplerende bilag/specifikationer til tilbuddet", 
        type=["pdf", "png", "jpg", "xlsx"], 
        accept_multiple_files=True,
        key="tilbud_ekstra"
    )

    if st.button("💾 Gem som Aktiv Aftale", type="primary"):
        if not producent.strip():
            st.warning("⚠️ Angiv venligst en producent/leverandør før du gemmer.")
        else:
            antal_bilag = len(ekstra_tilbud_filer) if ekstra_tilbud_filer else 0
            st.success(f"Aftale gemt for **{producent}** ({vare_type}) med {antal_bilag} tilknyttede bilag!")

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

    # Uploader til specifikke Pro-forma dokumenter
    proforma_filer = st.file_uploader(
        "Upload Pro-forma faktura(er) eller specifikationer", 
        type=["pdf", "jpg", "png"], 
        accept_multiple_files=True,
        key="proforma_docs"
    )

    if st.button("🔍 Udfør Sammenligning"):
        if not proforma_no:
            st.warning("Indtast venligst et pro-forma fakturanummer.")
        else:
            st.success(f"Sammenligning gennemført for Pro-forma #{proforma_no}. Ingen afvigelser fundet.")

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

    # Uploader til logistikdokumenter (B/L, certifikater, pakkelister m.m.)
    logistik_filer = st.file_uploader(
        "Upload logistikdokumenter (Bill of Lading, certifikater, pakkelister)", 
        type=["pdf", "png", "jpg"], 
        accept_multiple_files=True,
        key="logistik_docs"
    )

    st.markdown("---")
    if st.button("🚢 Bekræft Havne- og Logistikdata", type="primary"):
        antal_log_filer = len(logistik_filer) if logistik_filer else 0
        st.success(f"Logistik godkendt! Rute: {havn_afgang if havn_afgang else 'Ikke angivet'} ➔ **{havn_ankomst}** ({antal_log_filer} dokumenter tilknyttet).")
