import streamlit as st
import pdfplumber
import re

# ==========================================
# 1. ADGANGSKODE BESKYTTELSE
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
# 2. SELVE APPLIKATIONEN OG FANER
# ==========================================
st.title("📋 Importkontrol")

# ÉN samlet fil-uploader til alle informationer øverst
uploadet_fil = st.file_uploader("Upload dokumentation / tilbudsfil (PDF)", type=["pdf"])

udlaest_leverandoer = ""

if uploadet_fil is not None:
    try:
        with pdfplumber.open(uploadet_fil) as pdf:
            fuld_tekst = ""
            for page in pdf.pages:
                fuld_tekst += page.extract_text() or ""
        
        # Udtræk leverandørnavn hvis muligt
        match = re.search(r"(?:Leverandør|Exporter|Producent|Supplier):\s*(.+)", fuld_tekst, re.IGNORECASE)
        if match:
            udlaest_leverandoer = match.group(1).strip()
    except Exception:
        st.warning("Kunne ikke automatisk læse teksten fra PDF'en.")

# Opdeling i 3 overskuelige faner
tab1, tab2, tab3 = st.tabs([
    "1. Tilbud & Aktiv Aftale", 
    "2. Pro-forma Sammenligning", 
    "3. Havne & Logistik"
])

# ------------------------------------------
# FANE 1: TILBUD & AKTIV AFTALE
# ------------------------------------------
with tab1:
    st.header("Aktiv Aftale / Tilbud")
    
    producent = st.text_input(
        "Producent / Leverandør", 
        value=udlaest_leverandoer,
        help="Udfyldes automatisk ud fra filen hvis muligt. Kan rette manuelt."
    )

    vare_type = st.selectbox(
        "Varetype", 
        ["Pomfritter (Fries)", "Kød (Meat)", "Olivenolie (Olive Oil)", "Tomat på dåse (Canned Tomatoes)", "Andet"]
    )

    if st.button("💾 Gem som Aktiv Aftale"):
        if producent.strip() == "":
            st.warning("⚠️ Angiv venligst en producent/leverandør før du gemmer.")
        else:
            st.success(f"Aftale gemt for {producent} ({vare_type})!")

# ------------------------------------------
# FANE 2: PRO-FORMA SAMMENLIGNING
# ------------------------------------------
with tab2:
    st.header("Sammenligning af Pro-forma faktura mod tilbud")
    st.write("Her kan du sammenligne oplysningerne fra Pro-forma fakturaen direkte i forhold til den valgte aftale/tilbud.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Tilbudsværdier")
        st.write(f"**Leverandør:** {producent if producent else 'Ikke angivet'}")
        st.write(f"**Varetype:** {vare_type}")
        
    with col2:
        st.subheader("Pro-forma oplysninger")
        proforma_no = st.text_input("Pro-forma Fakturanummer")
        proforma_beloeb = st.number_input("Pro-forma Beløb (EUR/USD)", min_value=0.0, step=100.0)

    if st.button("🔍 Kør Sammenligning"):
        st.info("Kører sammenlignings-tjek mellem pro-forma og tilbud...")

# ------------------------------------------
# FANE 3: HAVNE & LOGISTIK
# ------------------------------------------
with tab3:
    st.header("Havne & Logistik")
    st.write("Sammenligning og verifikation af oplysninger mod havnene.")
    
    havn_afgang = st.text_input("Afgangshavn (POL)", placeholder="f.eks. udskibningshavn")
    
    # Pecém sat som fast standardværdi for modtagelseshavnen
    havn_ankomst = st.text_input("Ankomsthavn (POD)", value="Pecém, Nordøst-Brasilien")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.date_input("Forventet Afgangsdato (ETD)")
    with col_d2:
        st.date_input("Forventet Ankomstdato (ETA)")

    if st.button("🚢 Bekræft Havneoplysninger"):
        st.success(f"Havneoplysninger registreret med ankomst i {havn_ankomst}!")
