import streamlit as st
import pdfplumber
import re
from openai import OpenAI

# Sæt sideopsætning
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
# 2. OPENAI KLIENT INITIALISERING
# ==========================================
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("⚠️ Kunne ikke finde OPENAI_API_KEY i Streamlit Secrets. Tjek dine Secrets i Streamlit Cloud.")


# ==========================================
# 3. HOVEDAPPLIKATION (SAMMENLIGNING)
# ==========================================
st.title("🇧🇷 Import & Sammenligningsværktøj")
st.caption("ℹ️ *Bemærk: Filer og data bruges udelukkende til den aktuelle sammenligning og gemmes ikke permanent.*")
st.markdown("---")

# Generel Dokumenthåndtering til sammenligning
st.markdown("### 📂 Generel Dokumenthåndtering (Tilbud, Kontrakter, Certifikater)")
uploadede_filer = st.file_uploader(
    "Upload tilbud, kontrakter eller bilag til gennemsyn (Flere PDF-filer muligt)", 
    type=["pdf"],
    accept_multiple_files=True,
    help="Upload filer her. Systemet læser leverandørnavn og sletter filerne, når du lukker/opdaterer appen."
)

udlaest_leverandoer = ""
samlet_pdf_tekst = ""

if uploadede_filer:
    st.info(f"📁 {len(uploadede_filer)} generelle dokument(er) tilknyttet.")
    
    with st.spinner("Analyserer dokumenter..."):
        for fil in uploadede_filer:
            try:
                with pdfplumber.open(fil) as pdf:
                    for page in pdf.pages:
                        tekst = page.extract_text() or ""
                        samlet_pdf_tekst += f"\n--- Generelt dokument ({fil.name}) ---\n" + tekst
                
                if not udlaest_leverandoer:
                    match = re.search(r"(?:Leverandør|Exporter|Producent|Supplier):\s*(.+)", samlet_pdf_tekst, re.IGNORECASE)
                    if match:
                        udlaest_leverandoer = match.group(1).strip()
            except Exception:
                pass
                
    if udlaest_leverandoer:
        st.success(f"Fandt leverandør automatisk: **{udlaest_leverandoer}**")

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
    st.write("Indtast eller godkend de grundlæggende oplysninger til brug for sammenligningen.")
    
    col1, col2 = st.columns(2)
    with col1:
        producent = st.text_input(
            "Producent / Leverandør", 
            value=udlaest_leverandoer,
            help="Udfyldes automatisk ud fra de uploadede filer."
        )
    with col2:
        vare_type = st.selectbox(
            "Varetype", 
            ["Pomfritter (Fries)", "Kød (Meat)", "Olivenolie (Olive Oil)", "Tomat på dåse (Canned Tomatoes)", "Andet"]
        )

    st.info("💡 Data herfra bruges direkte i næste fane til sammenligning mod pro-forma og havnekrav.")

# ------------------------------------------
# FANE 2: PRO-FORMA SAMMENLIGNING (AI INTEGRATION)
# ------------------------------------------
with tab2:
    st.header("Sammenligning af Pro-forma mod Tilbud & Havnekrav")
    st.write("Hold pro-forma oplysningerne op imod den indgåede aftale og brasilianske toldkrav ved hjælp af AI.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Gældende Aftale")
        st.write(f"**Leverandør:** {producent if producent else 'Ikke angivet'}")
        st.write(f"**Varetype:** {vare_type}")
        
    with col2:
        st.markdown("### 📄 Pro-forma Oplysninger")
        proforma_no = st.text_input("Pro-forma Fakturanummer")
        proforma_beloeb = st.number_input("Pro-forma Beløb (EUR/USD)", min_value=0.0, step=100.0)

    proforma_filer = st.file_uploader(
        "Upload specifik pro-forma faktura (Flere PDF'er muligt)", 
        type=["pdf"], 
        accept_multiple_files=True,
        key="proforma_docs"
    )

    proforma_tekst = ""
    if proforma_filer:
        for p_fil in proforma_filer:
            try:
                with pdfplumber.open(p_fil) as pdf:
                    for page in pdf.pages:
                        proforma_tekst += f"\n--- Pro-forma ({p_fil.name}) ---\n" + (page.extract_text() or "")
            except Exception:
                pass

# ------------------------------------------
# FANE 3: HAVNE & LOGISTIK
# ------------------------------------------
with tab3:
    st.header("Havne & Logistisk Verifikation")
    st.write("Tjek at afgangshavn, ankomsthavn og havnedokumenter stemmer overens med importkravene.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        havn_afgang = st.text_input("Afgangshavn (POL)", placeholder="f.eks. Rotterdam, Santos osv.")
        havn_ankomst = st.text_input("Ankomsthavn (POD)", value="Pecém, Nordøst-Brasilien")
        
    with col2:
        etd = st.date_input("Forventet Afgangsdato (ETD)")
        eta = st.date_input("Forventet Ankomstdato (ETA)")

    logistik_filer = st.file_uploader(
        "Upload havne- og logistikdokumenter (Bill of Lading, Pakkeliste, MAPA certifikat osv. - Flere PDF'er muligt)", 
        type=["pdf"], 
        accept_multiple_files=True,
        key="logistik_docs"
    )

    logistik_tekst = ""
    if logistik_filer:
        for l_fil in logistik_filer:
            try:
                with pdfplumber.open(l_fil) as pdf:
                    for page in pdf.pages:
                        logistik_tekst += f"\n--- Logistik/Havnedokument ({l_fil.name}) ---\n" + (page.extract_text() or "")
            except Exception:
                pass

# ==========================================
# 4. SAMLET AI-ANALYSE PÅ TVÆRS AF ALLE DOKUMENTER
# ==========================================
st.markdown("---")
st.subheader("🔍 Samlet AI-Import- & Havnekontrol")
st.write("Kør en komplet AI-analyse på tværs af **alle** uploadede dokumenter (tilbud, pro-forma samt havne/logistikpapirer).")

if st.button("🚀 Kør AI Sammenligning & Havnekontrol", type="primary", use_container_width=True):
    kombineret_tekst = samlet_pdf_tekst + "\n" + proforma_tekst + "\n" + logistik_tekst

    if not kombineret_tekst.strip():
        st.warning("⚠️ Upload venligst mindst ét PDF-dokument før du kører AI-sammenligningen.")
    else:
        with st.spinner("🤖 AI'en analyserer samtlige dokumenter og kontrollerer mod brasilianske havnekrav..."):
            try:
                prompt = f"""
Du er en ekspert i brasiliansk importkontrol, tolddeklarering og logistik med særligt kendskab til ankomst i Pecém, Brasilien.

Dine opgaver:
1. SAMMENLIGNING AF DOKUMENTER:
   - Sammenlign oplysningerne fra tilbud/kontrakt, pro-forma faktura og logistikdokumenter (f.eks. Bill of Lading / B/L, pakkeliste).
   - Tjek for afvigelser i leverandørnavn, priser, beløb (Angivet pro-forma beløb: {proforma_beloeb}), mængder, vægt og Incoterms.

2. TJEK AF HAVNE- OG TOLD-DOKUMENTKRAV (Pecém / Receita Federal):
   - **Bill of Lading (B/L):** Er havne korrekt angivet? (POL: {havn_afgang if havn_afgang else 'Tjek dokument'}, POD: {havn_ankomst})
   - **NCM / HS-koder:** Fremgår den 8-cifrede NCM-kode for varerne?
   - **Skatte-ID / CNPJ:** Fremgår importørens CNPJ-nummer på dokumenterne?
   - **Særlige certifikater:** Kræver varetypen '{vare_type}' særlige certifikater (f.eks. MAPA sundhedscertifikat for kød/fødevarer eller ANVISA godkendelse)? Er de til stede i de uploadede papirer?

Opstil resultatet kort, overskueligt og opdelt i klare punkter på dansk. 
Brug ⚠️ til at fremhæve eventuelle mangler, afvigelser eller kritiske fejl i havnedokumenterne.

Dokumenttekst til samlet analyse:
{kombineret_tekst}
"""
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Du er en skarp assistent til importkontrol og brasiliansk logistik."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )

                st.markdown("### 🤖 AI Import- & Havnerapport")
                st.success("Analysen er gennemført!")
                st.write(response.choices[0].message.content)

            except Exception as e:
                st.error(f"⚠️ Der opstod en fejl under AI-sammenligningen: {e}")
