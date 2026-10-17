import streamlit as st
import pdfplumber
import re
import json
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

    st.info("💡 Data herfra bruges direkte i sammenligningen mod pro-forma og havnekrav.")

# ------------------------------------------
# FANE 2: PRO-FORMA SAMMENLIGNING
# ------------------------------------------
with tab2:
    st.header("Sammenligning af Pro-forma mod Tilbud & Havnekrav")
    st.write("Hold pro-forma oplysningerne op imod den indgåede aftale og brasilianske toldkrav.")
    
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
        "Upload havne- og logistikdokumenter (Bill of Lading, Pakkeliste, MAPA certifikat osv.)", 
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
# 4. STRUKTURERET AI-ANALYSE, OPFØLGNING OG VISNING
# ==========================================
st.markdown("---")
st.subheader("🔍 AI-Import- & Havnekontrol")

# Hjælpefunktion til at køre OpenAI analysen
def koer_ai_analyse(prompt_tekst):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Du er en præcis assistent for brasiliansk importkontrol i Pecém. Svar altid i gyldig JSON."},
            {"role": "user", "content": prompt_tekst}
        ],
        temperature=0.1
    )

# Knap til at køre den første overordnede analyse
if st.button("🚀 Kør AI Sammenligning & Havnekontrol", type="primary", use_container_width=True):
    kombineret_tekst = samlet_pdf_tekst + "\n" + proforma_tekst + "\n" + logistik_tekst

    if not kombineret_tekst.strip():
        st.warning("⚠️ Upload venligst mindst ét PDF-dokument før du kører AI-sammenligningen.")
    else:
        with st.spinner("🤖 AI'en analyserer dokumenterne og opstiller resultatet..."):
            try:
                st.session_state["kombineret_tekst"] = kombineret_tekst
                st.session_state["chat_historik"] = [] # Nulstil opfølgende chat
                
                start_prompt = f"""
Du er en ekspert i brasiliansk importkontrol og logistik i Pecém.
Du skal analysere de uploadede dokumenter og returnere et svar I KORREKT JSON-FORMAT:

{{
  "status_godkendt": true eller false,
  "sammenfatning": "En kort sætning om det samlede resultat",
  "afvigelser": [
    {{"kategori": "Pris/Beløb", "beskrivelse": "Forklaring...", "kritisk": true/false}}
  ],
  "godkendte_punkter": [
    "Leverandørnavn matcher"
  ],
  "mangler_og_advarsler": [
    "Mangler 8-cifret NCM-kode"
  ]
}}

Varetype: {vare_type}
Angivet Pro-forma Beløb: {proforma_beloeb}
Ankomsthavn: {havn_ankomst}

Dokumenttekst:
{kombineret_tekst}
"""
                response = koer_ai_analyse(start_prompt)
                st.session_state["analyse_resultat"] = json.loads(response.choices[0].message.content)

            except Exception as e:
                st.error(f"⚠️ Der opstod en fejl under AI-sammenligningen: {e}")

# Hvis der findes et analyseresultat i Session State, vises det her
if "analyse_resultat" in st.session_state:
    resultat = st.session_state["analyse_resultat"]

    st.markdown("## 📊 Analyseresultat")
    
    # 1. Samlet Statusindikator
    if resultat.get("status_godkendt", False):
        st.success(f"🟢 **GODKENDT:** {resultat.get('sammenfatning')}")
    else:
        st.error(f"🔴 **OBS / AFVIGELSER FUNDET:** {resultat.get('sammenfatning')}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_res1, col_res2 = st.columns(2)

    # 2. Godkendte Punkter
    with col_res1:
        st.markdown("### ✅ Godkendte Punkter")
        godkendte = resultat.get("godkendte_punkter", [])
        if godkendte:
            for punkt in godkendte:
                st.write(f"✔️ {punkt}")
        else:
            st.write("Ingen registrerede godkendte punkter.")

    # 3. Mangler & Advarsler
    with col_res2:
        st.markdown("### ⚠️ Mangler & Tjekpunkter")
        mangler = resultat.get("mangler_og_advarsler", [])
        if mangler:
            for punkt in mangler:
                st.warning(f"⚠️ {punkt}")
        else:
            st.write("Ingen mangler fundet.")

    # 4. Detaljerede afvigelser
    afvigelser = resultat.get("afvigelser", [])
    if afvigelser:
        st.markdown("---")
        st.markdown("### 🚨 Detaljerede Afvigelser")
        for afv in afvigelser:
            kat = afv.get("kategori", "Afvigelse")
            besk = afv.get("beskrivelse", "")
            if afv.get("kritisk", False):
                st.error(f"**[{kat}]** {besk}")
            else:
                st.info(f"**[{kat}]** {besk}")

    # ==========================================
    # 5. OPFØLGENDE CHAT OG DYNAMISK OPDATERING
    # ==========================================
    st.markdown("---")
    st.subheader("💬 Spørg eller opdater analysen")
    st.caption("Skriv spørgsmål til analysen eller tilføj oplysninger (f.eks. 'CNPJ nummeret er 12.345.678/0001-90, opdater analysen').")

    # Vis tidligere chat-beskeder
    for besk in st.session_state.get("chat_historik", []):
        with st.chat_message(besk["role"]):
            st.write(besk["content"])

    # Chat felt til brugeren
    bruger_input = st.chat_input("Skriv spørgsmål eller yderligere oplysninger her...")

    if bruger_input:
        # Tilføj brugerens besked til historik
        if "chat_historik" not in st.session_state:
            st.session_state["chat_historik"] = []
        
        st.session_state["chat_historik"].append({"role": "user", "content": bruger_input})

        with st.spinner("🤖 AI'en opdaterer vurderingen..."):
            try:
                opdateret_prompt = f"""
Du er en ekspert i importkontrol for Pecém, Brasilien.
Her er den seneste analysestruktur: {json.dumps(resultat)}

Brugeren har givet følgende yderligere oplysninger eller spørgsmål:
"{bruger_input}"

Opdater hele JSON-strukturen ud fra den nye information. 
Hvis brugeren f.eks. har oplyst et manglende CNPJ-nummer, skal advarslen fjernes fra 'mangler_og_advarsler' og tilføjes til 'godkendte_punkter'.

Dokumenttekst:
{st.session_state.get('kombineret_tekst', '')}

Returner KUN den opdaterede JSON-struktur.
"""
                response = koer_ai_analyse(opdateret_prompt)
                st.session_state["analyse_resultat"] = json.loads(response.choices[0].message.content)
                
                # Tilføj bekræftelse til chat
                st.session_state["chat_historik"].append({"role": "assistant", "content": f"Analysen er opdateret på baggrund af din besked: '{bruger_input}'"})
                
                st.rerun()

            except Exception as e:
                st.error(f"⚠️ Kunne ikke opdatere analysen: {e}")
