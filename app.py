import streamlit as st
import pdfplumber
import docx
import openpyxl
import easyocr
from PIL import Image
import io
import re
import json
from openai import OpenAI

# Sæt sideopsætning
st.set_page_config(
    page_title="Importkontrol - Brasilien", 
    page_icon="🇧🇷", 
    layout="wide"
)

# Initialiser EasyOCR til billeder (Dansk, Engelsk, Portugisisk, Spansk)
@st.cache_resource
def get_ocr_reader():
    return easyocr.Reader(['en', 'da', 'pt', 'es'])

# ==========================================
# 1. ADGANGSKODE BESKYTTELSE & VELKOMST
# ==========================================
def check_password():
    """Viser adgangskode feltet øverst og introduktion/instruktion nedenunder."""
    KORREKT_KODE = "brasilien2026"

    if st.session_state.get("password_correct", False):
        return True

    # Centreret layout til login- og velkomstskærm
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("# 🇧🇷 Import- & Sammenligningskontrol")
        st.caption("Verifikationsværktøj til fødevareimport med ankomst i Pecém, Nordøst-Brasilien")
        st.markdown("---")

        # LOGIN-FORMULAR ØVERST
        st.markdown("### 🔒 Log ind")
        password_input = st.text_input("Indtast adgangskode", type="password", help="Indtast adgangskoden for at få adgang.")
        
        if st.button("🚀 Åbn Importkontrol", type="primary", use_container_width=True):
            if password_input == KORREKT_KODE:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Forkert adgangskode. Prøv igen.")

        st.markdown("---")

        # INTRODUKTION: Hvad kan appen hjælpe med?
        st.markdown("### 💡 Hvad kan appen hjælpe dig med?")
        st.markdown("""
Appen fungerer som et **intelligent sammenligningsværktøj**, der sikrer dine importdokumenter mod dyre fejl, prisafvigelser og forsinkelser i tolden.

* 🔍 **Dokumentsammenligning:** Hold tilbud, pro-forma fakturaer, pakkelister og kontrakter op mod hinanden.
* 🇧🇷 **Told- & Havnekontrol (Pecém):** Tjek automatisk for lovpligtige brasilianske importkrav:
  * 8-cifrede **NCM-koder** (Mercosur HS-koder)
  * Modtagerens skatte-ID (**CNPJ-nummer**) på faktura og Bill of Lading
  * Påkrævede fødevarecertifikater (**MAPA / ANVISA**) ud fra varetype
* 💬 **Multiformat & Chat:** Læser **PDF, Word, Excel, billeder/screenshots (OCR) og e-mails/WhatsApp-tekst**. Bagefter kan du stille spørgsmål eller opdatere analysen direkte i en chat.
* 🔒 **Sikker & Fortrolig:** Ingen dokumenter gemmes permanent. Alt slettes automatisk fra hukommelsen, når du lukker siden.
""")

        st.markdown("---")

        # INSTRUKTIONER: Hvordan bruges appen?
        st.markdown("### 📋 Sådan bruger du appen:")
        st.markdown("""
1. **Log ind:** Indtast adgangskoden øverst for at åbne værktøjet.
2. **Upload eller Indsæt:** Upload relevante dokumenter (eller klistr e-mails/WhatsApp-aftaler ind).
3. **Udfyld Stamdata:** Tjek varetype og havneoplysninger under fanerne.
4. **Kør AI-Analyse:** Tryk på knappen og modtag et farvekodet og struktureret resultat.
5. **Opfølgning:** Brug chatten i bunden til at stille spørgsmål eller rette oplysninger.
""")
                
    return False

if not check_password():
    st.stop()
# ==========================================


# ==========================================
# 2. UNIVERSEL TEKSTUDTRÆKNING
# ==========================================
ACCEPTED_TYPES = ["pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg"]

def udtraek_tekst_fra_fil(fil):
    """Udtrækker tekst fra PDF, Word, Excel, Tekst og Billeder (OCR)."""
    tekst = ""
    fil_navn = fil.name
    fil_ext = fil_navn.split(".")[-1].lower()

    try:
        # 1. PDF
        if fil_ext == "pdf":
            with pdfplumber.open(fil) as pdf:
                for page in pdf.pages:
                    tekst += (page.extract_text() or "") + "\n"

        # 2. Word (.docx)
        elif fil_ext == "docx":
            doc = docx.Document(fil)
            for p in doc.paragraphs:
                tekst += p.text + "\n"
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells]
                    tekst += " | ".join(row_text) + "\n"

        # 3. Excel (.xlsx)
        elif fil_ext == "xlsx":
            wb = openpyxl.load_workbook(fil, data_only=True)
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                tekst += f"\n--- Ark: {sheet} ---\n"
                for row in ws.iter_rows(values_only=True):
                    row_vals = [str(val) if val is not None else "" for val in row]
                    if any(row_vals):
                        tekst += " | ".join(row_vals) + "\n"

        # 4. Tekstfiler (.txt)
        elif fil_ext == "txt":
            tekst = fil.read().decode("utf-8", errors="ignore")

        # 5. Billeder (PNG, JPG, JPEG via OCR)
        elif fil_ext in ["png", "jpg", "jpeg"]:
            image = Image.open(fil)
            reader = get_ocr_reader()
            image_bytes = io.BytesIO()
            image.save(image_bytes, format=image.format or 'PNG')
            ocr_result = reader.readtext(image_bytes.getvalue(), detail=0)
            tekst = "\n".join(ocr_result)

    except Exception as e:
        st.warning(f"⚠️ Kunne ikke udtrække fuld tekst fra '{fil_navn}': {e}")

    return tekst


# ==========================================
# 3. OPENAI KLIENT INITIALISERING
# ==========================================
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("⚠️ Kunne ikke finde OPENAI_API_KEY i Streamlit Secrets. Tjek dine Secrets i Streamlit Cloud.")


# ==========================================
# 4. HOVEDAPPLIKATION
# ==========================================
st.title("🇧🇷 Import & Sammenligningsværktøj")
st.caption("ℹ️ *Bemærk: Filer og tekst bruges udelukkende til den aktuelle sammenligning og gemmes ikke permanent.*")
st.markdown("---")

# Generel Dokumenthåndtering & Mail/Chat-input
st.markdown("### 📂 Dokumenter & Korrespondance")

col_upload, col_text = st.columns([1, 1])

with col_upload:
    uploadede_filer = st.file_uploader(
        "Upload tilbud, kontrakter, bilag eller screenshots (PDF, Word, Excel, TXT, PNG, JPG)", 
        type=ACCEPTED_TYPES,
        accept_multiple_files=True,
        help="Upload filer her. Systemet læser leverandørnavn og sletter filerne ved genstart."
    )

with col_text:
    mail_og_chat_tekst = st.text_area(
        "💬 Kopiér & indsæt tekst fra e-mails, WhatsApp eller chat her (Valgfrit):",
        placeholder="Eksempel:\n'Leverandør har bekræftet på WhatsApp i dag, at prisen er $1.05/kg og at de dækker fragten til Pecém...'",
        height=135
    )

udlaest_leverandoer = ""
samlet_pdf_tekst = ""

if mail_og_chat_tekst.strip():
    samlet_pdf_tekst += f"\n--- Indsat Mail / Chat Korrespondance ---\n{mail_og_chat_tekst}\n"

if uploadede_filer:
    st.info(f"📁 {len(uploadede_filer)} generelle dokument(er) tilknyttet.")
    
    with st.spinner("Analyserer dokumenter..."):
        for fil in uploadede_filer:
            udtrukket = udtraek_tekst_fra_fil(fil)
            samlet_pdf_tekst += f"\n--- Dokument ({fil.name}) ---\n" + udtrukket
            
            if not udlaest_leverandoer:
                match = re.search(r"(?:Leverandør|Exporter|Producent|Supplier):\s*(.+)", udtrukket, re.IGNORECASE)
                if match:
                    udlaest_leverandoer = match.group(1).strip()
                
    if udlaest_leverandoer:
        st.success(f"Fandt leverandør automatisk: **{udlaest_leverandoer}**")

st.markdown("<br>", unsafe_allow_html=True)

# Opdeling i 3 faner
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

    st.info("💡 Data herfra bruges direkte i sammenligningen mod pro-forma, e-mails og havnekrav.")

# ------------------------------------------
# FANE 2: PRO-FORMA SAMMENLIGNING
# ------------------------------------------
with tab2:
    st.header("Sammenligning af Pro-forma mod Tilbud & Havnekrav")
    st.write("Hold pro-forma oplysningerne op imod den indgåede aftale, e-mails og brasilianske toldkrav.")
    
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
        "Upload specifik pro-forma faktura (PDF, Word, Excel, Billeder m.m.)", 
        type=ACCEPTED_TYPES, 
        accept_multiple_files=True,
        key="proforma_docs"
    )

    proforma_tekst = ""
    if proforma_filer:
        for p_fil in proforma_filer:
            proforma_tekst += f"\n--- Pro-forma ({p_fil.name}) ---\n" + udtraek_tekst_fra_fil(p_fil)

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
        "Upload havne- og logistikdokumenter (Bill of Lading, Pakkeliste, MAPA certifikat, Billeder osv.)", 
        type=ACCEPTED_TYPES, 
        accept_multiple_files=True,
        key="logistik_docs"
    )

    logistik_tekst = ""
    if logistik_filer:
        for l_fil in logistik_filer:
            logistik_tekst += f"\n--- Logistik/Havnedokument ({l_fil.name}) ---\n" + udtraek_tekst_fra_fil(l_fil)

# ==========================================
# 5. STRUKTURERET AI-ANALYSE OG CHAT
# ==========================================
st.markdown("---")
st.subheader("🔍 AI-Import- & Havnekontrol")

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

if st.button("🚀 Kør AI Sammenligning & Havnekontrol", type="primary", use_container_width=True):
    kombineret_tekst = samlet_pdf_tekst + "\n" + proforma_tekst + "\n" + logistik_tekst

    if not kombineret_tekst.strip():
        st.warning("⚠️ Upload venligst mindst ét dokument/billede eller indsæt e-mail/chattekst før du kører AI-sammenligningen.")
    else:
        with st.spinner("🤖 AI'en analyserer dokumenter, e-mails og billeder..."):
            try:
                st.session_state["kombineret_tekst"] = kombineret_tekst
                st.session_state["chat_historik"] = []
                
                start_prompt = f"""
Du er en ekspert i brasiliansk importkontrol og logistik i Pecém.
Du skal analysere de uploadede dokumenter, e-mail/chat-korrespondance og bilag og returnere et svar I KORREKT JSON-FORMAT:

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

Samlet tekst (inkl. dokumenter, e-mails og beskeder):
{kombineret_tekst}
"""
                response = koer_ai_analyse(start_prompt)
                st.session_state["analyse_resultat"] = json.loads(response.choices[0].message.content)

            except Exception as e:
                st.error(f"⚠️ Der opstod en fejl under AI-sammenligningen: {e}")

# Vis resultater
if "analyse_resultat" in st.session_state:
    resultat = st.session_state["analyse_resultat"]

    st.markdown("## 📊 Analyseresultat")
    
    if resultat.get("status_godkendt", False):
        st.success(f"🟢 **GODKENDT:** {resultat.get('sammenfatning')}")
    else:
        st.error(f"🔴 **OBS / AFVIGELSER FUNDET:** {resultat.get('sammenfatning')}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_res1, col_res2 = st.columns(2)

    with col_res1:
        st.markdown("### ✅ Godkendte Punkter")
        godkendte = resultat.get("godkendte_punkter", [])
        if godkendte:
            for punkt in godkendte:
                st.write(f"✔️ {punkt}")
        else:
            st.write("Ingen registrerede godkendte punkter.")

    with col_res2:
        st.markdown("### ⚠️ Mangler & Tjekpunkter")
        mangler = resultat.get("mangler_og_advarsler", [])
        if mangler:
            for punkt in mangler:
                st.warning(f"⚠️ {punkt}")
        else:
            st.write("Ingen mangler fundet.")

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

    # Opfølgende Chat
    st.markdown("---")
    st.subheader("💬 Spørg eller opdater analysen")
    st.caption("Skriv spørgsmål til analysen eller tilføj oplysninger (f.eks. 'CNPJ nummeret er 12.345.678/0001-90, opdater analysen').")

    for besk in st.session_state.get("chat_historik", []):
        with st.chat_message(besk["role"]):
            st.write(besk["content"])

    bruger_input = st.chat_input("Skriv spørgsmål eller yderligere oplysninger her...")

    if bruger_input:
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
Returner KUN den opdaterede JSON-struktur.

Samlet tekst:
{st.session_state.get('kombineret_tekst', '')}
"""
                response = koer_ai_analyse(opdateret_prompt)
                st.session_state["analyse_resultat"] = json.loads(response.choices[0].message.content)
                st.session_state["chat_historik"].append({"role": "assistant", "content": f"Analysen er opdateret ud fra din besked: '{bruger_input}'"})
                st.rerun()

            except Exception as e:
                st.error(f"⚠️ Kunne ikke opdatere analysen: {e}")
