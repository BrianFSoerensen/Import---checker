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
    page_title="Import Control - Pecém 🇧🇷", 
    page_icon="🇧🇷", 
    layout="wide"
)

# Initialiser EasyOCR til billeder (Dansk, Engelsk, Portugisisk, Spansk)
@st.cache_resource
def get_ocr_reader():
    return easyocr.Reader(['pt', 'en', 'da', 'es'])

# ==========================================
# 0. SPROGORDBOG (TRANSLATIONS)
# ==========================================
TRANSLATIONS = {
    "pt": {
        "title": "🇧🇷 Controle de Importação & Comparação",
        "subtitle": "Ferramenta de verificação para importação de alimentos com chegada em Pecém, Ceará",
        "login_header": "🔒 Acesso Restrito",
        "password_label": "Digite a senha de acesso",
        "login_btn": "🚀 Entrar no Controle de Importação",
        "wrong_pass": "❌ Senha incorreta. Tente novamente.",
        "help_title": "💡 Como o aplicativo pode te ajudar?",
        "help_text": """
O aplicativo funciona como uma **ferramenta de comparação inteligente**, garantindo que seus documentos de importação estejam livres de erros custosos, discrepâncias de preços e atrasos na alfândega.

* 🔍 **Comparação de Documentos:** Compare cotações, faturas pro-forma, listas de embalagem (packing lists) e contratos.
* 🇧🇷 **Controle Alfandegário & Portuário (Pecém):** Verificação automática das exigências legais brasileiras:
  * Códigos **NCM** de 8 dígitos (Classificação Mercosul)
  * Registro de **CNPJ** do importador na fatura e no Bill of Lading (B/L)
  * Certificados sanitários e fitossanitários exigidos (**MAPA / ANVISA**) conforme o tipo de produto
* 💬 **Multiformato & Chat:** Lê **PDF, Word, Excel, imagens/screenshots (OCR) e textos de e-mail/WhatsApp**. Depois, você pode tirar dúvidas ou atualizar a análise diretamente no chat.
* 🔒 **Seguro & Confidencial:** Nenhum documento é armazenado permanentemente. Tudo é excluído da memória ao fechar a página.
""",
        "instructions_title": "📋 Como usar o aplicativo:",
        "instructions_text": """
1. **Faça Login:** Digite a senha acima para acessar a ferramenta.
2. **Envie ou Cole:** Envie os documentos relevantes (ou cole acordos de e-mail/WhatsApp).
3. **Preencha os Dados:** Verifique o tipo de mercadoria e informações portuárias nas abas.
4. **Execute a Análise IA:** Clique no botão e receba um relatório estruturado e colorido.
5. **Acompanhamento:** Use o chat no final da página para tirar dúvidas ou corrigir dados.
""",
        "notice": "ℹ️ *Nota: Arquivos e textos são usados exclusivamente para a comparação atual e não são salvos.*",
        "sec_docs": "📂 Documentos & Correspondência",
        "upload_label": "Upload de cotações, contratos, comprovantes ou imagens (PDF, Word, Excel, TXT, PNG, JPG)",
        "chat_paste_label": "💬 Copie e cole textos de e-mails, WhatsApp ou conversas aqui (Opcional):",
        "chat_paste_placeholder": "Exemplo:\n'O fornecedor confirmou no WhatsApp hoje que o preço é $1.05/kg e que cobrem o frete até Pecém...'",
        "supplier_found": "Fornecedor identificado automaticamente:",
        "tab1": "1️⃣ Oferta & Acordo Ativo",
        "tab2": "2️⃣ Comparação Pro-forma",
        "tab3": "3️⃣ Portos & Logística",
        "supplier_input": "Produtor / Fornecedor",
        "product_type": "Tipo de Mercadoria",
        "prod_fries": "Batata Frita (Fries)",
        "prod_meat": "Carne (Meat)",
        "prod_oil": "Azeite de Oliva (Olive Oil)",
        "prod_canned": "Tomate Enlatado (Canned Tomatoes)",
        "prod_other": "Outros",
        "active_agreement": "Acordo Vigente",
        "proforma_info": "Informações da Pro-forma",
        "proforma_no": "Número da Fatura Pro-forma",
        "proforma_amount": "Valor da Pro-forma (EUR/USD)",
        "upload_proforma": "Upload da fatura pro-forma específica (PDF, Word, Excel, Imagens etc.)",
        "pol_label": "Porto de Origem (POL)",
        "pod_label": "Porto de Destino (POD)",
        "etd_label": "Data Prevista de Saída (ETD)",
        "eta_label": "Data Prevista de Chegada (ETA)",
        "upload_logistics": "Upload de documentos logísticos e portuários (Bill of Lading, Packing List, Certificado MAPA etc.)",
        "run_ai_btn": "🚀 Executar Comparação IA & Controle Portuário",
        "no_docs_warn": "⚠️ Envie pelo menos um documento/imagem ou cole o texto do e-mail/chat antes de executar a análise.",
        "analyzing": "🤖 A IA está analisando os documentos, e-mails e imagens...",
        "results_header": "📊 Resultado da Análise",
        "approved": "🟢 APROVADO:",
        "discrepancies_found": "🔴 ATENÇÃO / DISCREPÂNCIAS ENCONTRADAS:",
        "approved_points": "✅ Pontos Aprovados",
        "warnings_points": "⚠️ Pendências & Alertas",
        "detailed_discrepancies": "🚨 Discrepâncias Detalhadas",
        "no_approved": "Nenhum ponto aprovado registrado.",
        "no_warnings": "Nenhuma pendência encontrada.",
        "followup_title": "💬 Pergunte ou atualize a análise",
        "followup_caption": "Escreva perguntas sobre a análise ou adicione informações (ex: 'O CNPJ é 12.345.678/0001-90, atualize a análise').",
        "chat_placeholder": "Escreva suas dúvidas ou novas informações aqui...",
        "ai_lang_instruction": "Responda obrigatoriamente em PORTUGUÊS DO BRASIL."
    },
    "en": {
        "title": "🇧🇷 Import Control & Comparison",
        "subtitle": "Verification tool for food import arriving at Pecém Port, Northeast Brazil",
        "login_header": "🔒 Restricted Access",
        "password_label": "Enter access password",
        "login_btn": "🚀 Login to Import Control",
        "wrong_pass": "❌ Incorrect password. Please try again.",
        "help_title": "💡 How can this app help you?",
        "help_text": """
The app acts as an **intelligent comparison tool**, safeguarding your import documents against costly errors, price discrepancies, and customs delays.

* 🔍 **Document Comparison:** Compare quotes, pro-forma invoices, packing lists, and contracts side-by-side.
* 🇧🇷 **Customs & Port Control (Pecém):** Automatic verification against Brazilian legal import requirements:
  * 8-digit **NCM codes** (Mercosur HS Codes)
  * Importer's tax ID (**CNPJ number**) on invoices and Bill of Lading (B/L)
  * Required food certificates (**MAPA / ANVISA**) based on product category
* 💬 **Multiformat & Chat:** Reads **PDF, Word, Excel, images/screenshots (OCR), and email/WhatsApp text**. Afterward, ask questions or update the analysis directly in chat.
* 🔒 **Secure & Confidential:** No documents are permanently stored. Everything is cleared from memory when you close the tab.
""",
        "instructions_title": "📋 How to use the app:",
        "instructions_text": """
1. **Login:** Enter the password above to access the tool.
2. **Upload or Paste:** Upload relevant documents (or paste email/WhatsApp agreements).
3. **Fill Master Data:** Check product type and port details in the tabs.
4. **Run AI Analysis:** Click the button to receive a color-coded, structured report.
5. **Follow-up:** Use the chat at the bottom to ask questions or update details.
""",
        "notice": "ℹ️ *Note: Files and text are used exclusively for the current comparison and are not permanently saved.*",
        "sec_docs": "📂 Documents & Correspondence",
        "upload_label": "Upload quotes, contracts, receipts or screenshots (PDF, Word, Excel, TXT, PNG, JPG)",
        "chat_paste_label": "💬 Copy & paste text from emails, WhatsApp or chat here (Optional):",
        "chat_paste_placeholder": "Example:\n'Supplier confirmed on WhatsApp today that the price is $1.05/kg and they cover freight to Pecém...'",
        "supplier_found": "Supplier automatically detected:",
        "tab1": "1️⃣ Quote & Active Agreement",
        "tab2": "2️⃣ Pro-forma Comparison",
        "tab3": "3️⃣ Ports & Logistics",
        "supplier_input": "Producer / Supplier",
        "product_type": "Product Category",
        "prod_fries": "French Fries",
        "prod_meat": "Meat",
        "prod_oil": "Olive Oil",
        "prod_canned": "Canned Tomatoes",
        "prod_other": "Other",
        "active_agreement": "Active Agreement",
        "proforma_info": "Pro-forma Information",
        "proforma_no": "Pro-forma Invoice Number",
        "proforma_amount": "Pro-forma Amount (EUR/USD)",
        "upload_proforma": "Upload specific pro-forma invoice (PDF, Word, Excel, Images, etc.)",
        "pol_label": "Port of Loading (POL)",
        "pod_label": "Port of Discharge (POD)",
        "etd_label": "Expected Departure Date (ETD)",
        "eta_label": "Expected Arrival Date (ETA)",
        "upload_logistics": "Upload port and logistics documents (Bill of Lading, Packing List, MAPA cert, Images, etc.)",
        "run_ai_btn": "🚀 Run AI Comparison & Port Control",
        "no_docs_warn": "⚠️ Please upload at least one document/image or paste email/chat text before running the AI analysis.",
        "analyzing": "🤖 AI is analyzing documents, emails, and images...",
        "results_header": "📊 Analysis Results",
        "approved": "🟢 APPROVED:",
        "discrepancies_found": "🔴 ATTENTION / DISCREPANCIES FOUND:",
        "approved_points": "✅ Approved Items",
        "warnings_points": "⚠️ Pending Items & Warnings",
        "detailed_discrepancies": "🚨 Detailed Discrepancies",
        "no_approved": "No approved items recorded.",
        "no_warnings": "No pending items found.",
        "followup_title": "💬 Ask or update the analysis",
        "followup_caption": "Type questions about the analysis or add information (e.g. 'CNPJ number is 12.345.678/0001-90, update analysis').",
        "chat_placeholder": "Type your questions or new information here...",
        "ai_lang_instruction": "You MUST respond in ENGLISH."
    },
    "da": {
        "title": "🇧🇷 Import- & Sammenligningskontrol",
        "subtitle": "Verifikationsværktøj til fødevareimport med ankomst i Pecém, Nordøst-Brasilien",
        "login_header": "🔒 Begrænset Adgang",
        "password_label": "Indtast adgangskode",
        "login_btn": "🚀 Åbn Importkontrol",
        "wrong_pass": "❌ Forkert adgangskode. Prøv igen.",
        "help_title": "💡 Hvad kan appen hjælpe dig med?",
        "help_text": """
Appen fungerer som et **intelligent sammenligningsværktøj**, der sikrer dine importdokumenter mod dyre fejl, prisafvigelser og forsinkelser i tolden.

* 🔍 **Dokumentsammenligning:** Hold tilbud, pro-forma fakturaer, pakkelister og kontrakter op mod hinanden.
* 🇧🇷 **Told- & Havnekontrol (Pecém):** Tjek automatisk for lovpligtige brasilianske importkrav:
  * 8-cifrede **NCM-koder** (Mercosur HS-koder)
  * Modtagerens skatte-ID (**CNPJ-nummer**) på faktura og Bill of Lading
  * Påkrævede fødevarecertifikater (**MAPA / ANVISA**) ud fra varetype
* 💬 **Multiformat & Chat:** Læser **PDF, Word, Excel, billeder/screenshots (OCR) og e-mails/WhatsApp-tekst**. Bagefter kan du stille spørgsmål eller opdatere analysen direkte i en chat.
* 🔒 **Sikker & Fortrolig:** Ingen dokumenter gemmes permanent. Alt slettes automatisk fra hukommelsen, når du lukker siden.
""",
        "instructions_title": "📋 Sådan bruger du appen:",
        "instructions_text": """
1. **Log ind:** Indtast adgangskoden ovenfor for at åbne værktøjet.
2. **Upload eller Indsæt:** Upload relevante dokumenter (eller klistr e-mails/WhatsApp-aftaler ind).
3. **Udfyld Stamdata:** Tjek varetype og havneoplysninger under fanerne.
4. **Kør AI-Analyse:** Tryk på knappen og modtag et farvekodet og struktureret resultat.
5. **Opfølgning:** Brug chatten i bunden til at stille spørgsmål eller rette oplysninger.
""",
        "notice": "ℹ️ *Bemærk: Filer og tekst bruges udelukkende til den aktuelle sammenligning og gemmes ikke permanent.*",
        "sec_docs": "📂 Dokumenter & Korrespondance",
        "upload_label": "Upload tilbud, kontrakter, bilag eller screenshots (PDF, Word, Excel, TXT, PNG, JPG)",
        "chat_paste_label": "💬 Kopiér & indsæt tekst fra e-mails, WhatsApp eller chat her (Valgfrit):",
        "chat_paste_placeholder": "Eksempel:\n'Leverandør har bekræftet på WhatsApp i dag, at prisen er $1.05/kg og at de dækker fragten til Pecém...'",
        "supplier_found": "Fandt leverandør automatisk:",
        "tab1": "1️⃣ Tilbud & Aktiv Aftale",
        "tab2": "2️⃣ Pro-forma Sammenligning",
        "tab3": "3️⃣ Havne & Logistik",
        "supplier_input": "Producent / Leverandør",
        "product_type": "Varetype",
        "prod_fries": "Pomfritter (Fries)",
        "prod_meat": "Kød (Meat)",
        "prod_oil": "Olivenolie (Olive Oil)",
        "prod_canned": "Tomat på dåse (Canned Tomatoes)",
        "prod_other": "Andet",
        "active_agreement": "Gældende Aftale",
        "proforma_info": "Pro-forma Oplysninger",
        "proforma_no": "Pro-forma Fakturanummer",
        "proforma_amount": "Pro-forma Beløb (EUR/USD)",
        "upload_proforma": "Upload specifik pro-forma faktura (PDF, Word, Excel, Billeder m.m.)",
        "pol_label": "Afgangshavn (POL)",
        "pod_label": "Ankomsthavn (POD)",
        "etd_label": "Forventet Afgangsdato (ETD)",
        "eta_label": "Forventet Ankomstdato (ETA)",
        "upload_logistics": "Upload havne- og logistikdokumenter (Bill of Lading, Pakkeliste, MAPA certifikat, Billeder osv.)",
        "run_ai_btn": "🚀 Kør AI Sammenligning & Havnekontrol",
        "no_docs_warn": "⚠️ Upload venligst mindst ét dokument/billede eller indsæt e-mail/chattekst før du kører AI-sammenligningen.",
        "analyzing": "🤖 AI'en analyserer dokumenter, e-mails og billeder...",
        "results_header": "📊 Analyseresultat",
        "approved": "🟢 GODKENDT:",
        "discrepancies_found": "🔴 OBS / AFVIGELSER FUNDET:",
        "approved_points": "✅ Godkendte Punkter",
        "warnings_points": "⚠️ Mangler & Tjekpunkter",
        "detailed_discrepancies": "🚨 Detaljerede Afvigelser",
        "no_approved": "Ingen registrerede godkendte punkter.",
        "no_warnings": "Ingen mangler fundet.",
        "followup_title": "💬 Spørg eller opdater analysen",
        "followup_caption": "Skriv spørgsmål til analysen eller tilføj oplysninger (f.eks. 'CNPJ nummeret er 12.345.678/0001-90, opdater analysen').",
        "chat_placeholder": "Skriv spørgsmål eller yderligere oplysninger her...",
        "ai_lang_instruction": "Du SKAL svare på DANSK."
    }
}

# ==========================================
# 1. ADGANGSKODE BESKYTTELSE & VELKOMST
# ==========================================
def check_password():
    """Viser adgangskode feltet øverst og introduktion/instruktion nedenunder."""
    KORREKT_KODE = "brasilien2026"

    if st.session_state.get("password_correct", False):
        return True

    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        # Sprogvelger med Portugisisk som standard
        selected_lang_code = st.selectbox(
            "🌐 Idioma / Language / Sprog:",
            options=["pt", "en", "da"],
            format_func=lambda x: "🇧🇷 Português (Brasil)" if x == "pt" else ("🇬🇧 English" if x == "en" else "🇩🇰 Dansk"),
            index=0
        )
        st.session_state["lang"] = selected_lang_code
        t = TRANSLATIONS[selected_lang_code]

        st.markdown(f"# {t['title']}")
        st.caption(t['subtitle'])
        st.markdown("---")

        # LOGIN-FORMULAR ØVERST
        st.markdown(f"### {t['login_header']}")
        password_input = st.text_input(t['password_label'], type="password")
        
        if st.button(t['login_btn'], type="primary", use_container_width=True):
            if password_input == KORREKT_KODE:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error(t['wrong_pass'])

        st.markdown("---")

        # INTRODUKTION
        st.markdown(f"### {t['help_title']}")
        st.markdown(t['help_text'])

        st.markdown("---")

        # INSTRUKTIONER
        st.markdown(f"### {t['instructions_title']}")
        st.markdown(t['instructions_text'])
                
    return False

if not check_password():
    st.stop()
# ==========================================

# Hent det valgte sprog fra session_state (default 'pt')
lang_code = st.session_state.get("lang", "pt")
t = TRANSLATIONS[lang_code]

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
                tekst += f"\n--- Sheet: {sheet} ---\n"
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
        st.warning(f"⚠️ Error extracting text from '{fil_navn}': {e}")

    return tekst


# ==========================================
# 3. OPENAI KLIENT INITIALISERING
# ==========================================
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("⚠️ OPENAI_API_KEY not found in Streamlit Secrets.")


# ==========================================
# 4. HOVEDAPPLIKATION
# ==========================================
col_title, col_lang = st.columns([3, 1])

with col_lang:
    # Dropdown øverst i hoved-appen til at skifte sprog
    selected_lang_code = st.selectbox(
        "🌐 Language / Idioma:",
        options=["pt", "en", "da"],
        format_func=lambda x: "🇧🇷 Português (Brasil)" if x == "pt" else ("🇬🇧 English" if x == "en" else "🇩🇰 Dansk"),
        index=["pt", "en", "da"].index(lang_code)
    )
    if selected_lang_code != lang_code:
        st.session_state["lang"] = selected_lang_code
        st.rerun()

with col_title:
    st.title(t["title"])
    st.caption(t["notice"])

st.markdown("---")

# Generel Dokumenthåndtering & Mail/Chat-input
st.markdown(f"### {t['sec_docs']}")

col_upload, col_text = st.columns([1, 1])

with col_upload:
    uploadede_filer = st.file_uploader(
        t['upload_label'], 
        type=ACCEPTED_TYPES,
        accept_multiple_files=True
    )

with col_text:
    mail_og_chat_tekst = st.text_area(
        t['chat_paste_label'],
        placeholder=t['chat_paste_placeholder'],
        height=135
    )

udlaest_leverandoer = ""
samlet_pdf_tekst = ""

if mail_og_chat_tekst.strip():
    samlet_pdf_tekst += f"\n--- Mail / Chat Correspondence ---\n{mail_og_chat_tekst}\n"

if uploadede_filer:
    st.info(f"📁 {len(uploadede_filer)} document(s) attached.")
    
    with st.spinner("Analyzing..."):
        for fil in uploadede_filer:
            udtrukket = udtraek_tekst_fra_fil(fil)
            samlet_pdf_tekst += f"\n--- Document ({fil.name}) ---\n" + udtrukket
            
            if not udlaest_leverandoer:
                match = re.search(r"(?:Leverandør|Exporter|Producent|Supplier|Fornecedor):\s*(.+)", udtrukket, re.IGNORECASE)
                if match:
                    udlaest_leverandoer = match.group(1).strip()
                
    if udlaest_leverandoer:
        st.success(f"{t['supplier_found']} **{udlaest_leverandoer}**")

st.markdown("<br>", unsafe_allow_html=True)

# Opdeling i 3 faner
tab1, tab2, tab3 = st.tabs([
    t["tab1"], 
    t["tab2"], 
    t["tab3"]
])

# ------------------------------------------
# FANE 1: TILBUD & AKTIV AFTALE
# ------------------------------------------
with tab1:
    st.header(t["tab1"])
    col1, col2 = st.columns(2)
    with col1:
        producent = st.text_input(
            t["supplier_input"], 
            value=udlaest_leverandoer
        )
    with col2:
        vare_type = st.selectbox(
            t["product_type"], 
            [t["prod_fries"], t["prod_meat"], t["prod_oil"], t["prod_canned"], t["prod_other"]]
        )

# ------------------------------------------
# FANE 2: PRO-FORMA SAMMENLIGNING
# ------------------------------------------
with tab2:
    st.header(t["tab2"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### 📋 {t['active_agreement']}")
        st.write(f"**{t['supplier_input']}:** {producent if producent else '-'}")
        st.write(f"**{t['product_type']}:** {vare_type}")
        
    with col2:
        st.markdown(f"### 📄 {t['proforma_info']}")
        proforma_no = st.text_input(t["proforma_no"])
        proforma_beloeb = st.number_input(t["proforma_amount"], min_value=0.0, step=100.0)

    proforma_filer = st.file_uploader(
        t["upload_proforma"], 
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
    st.header(t["tab3"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        havn_afgang = st.text_input(t["pol_label"], placeholder="e.g. Rotterdam, Santos")
        havn_ankomst = st.text_input(t["pod_label"], value="Pecém, Ceará, Brasil")
        
    with col2:
        etd = st.date_input(t["etd_label"])
        eta = st.date_input(t["eta_label"])

    logistik_filer = st.file_uploader(
        t["upload_logistics"], 
        type=ACCEPTED_TYPES, 
        accept_multiple_files=True,
        key="logistik_docs"
    )

    logistik_tekst = ""
    if logistik_filer:
        for l_fil in logistik_filer:
            logistik_tekst += f"\n--- Logistics/Port Document ({l_fil.name}) ---\n" + udtraek_tekst_fra_fil(l_fil)

# ==========================================
# 5. STRUKTURERET AI-ANALYSE OG CHAT
# ==========================================
st.markdown("---")
st.subheader(f"🔍 {t['run_ai_btn']}")

def koer_ai_analyse(prompt_tekst):
    return client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": f"You are a precise import control assistant for Pecém, Brazil. Always respond in valid JSON. {t['ai_lang_instruction']}"},
            {"role": "user", "content": prompt_tekst}
        ],
        temperature=0.1
    )

if st.button(t['run_ai_btn'], type="primary", use_container_width=True):
    kombineret_tekst = samlet_pdf_tekst + "\n" + proforma_tekst + "\n" + logistik_tekst

    if not kombineret_tekst.strip():
        st.warning(t['no_docs_warn'])
    else:
        with st.spinner(t['analyzing']):
            try:
                st.session_state["kombineret_tekst"] = kombineret_tekst
                st.session_state["chat_historik"] = []
                
                start_prompt = f"""
You are an expert in Brazilian import control and port logistics for Pecém, Brazil.
Analyze the provided documents, email/chat correspondence, and attachments and return a response IN STRICT JSON FORMAT:

{{
  "status_godkendt": true or false,
  "sammenfatning": "A concise one-sentence summary of the overall result",
  "afvigelser": [
    {{"kategori": "Price/Amount", "beskrivelse": "Explanation...", "kritisk": true/false}}
  ],
  "godkendte_punkter": [
    "Supplier name matches"
  ],
  "mangler_og_advarsler": [
    "Missing 8-digit NCM code"
  ]
}}

LANGUAGE REQUIREMENT: All textual fields inside the JSON ('sammenfatning', 'beskrivelse', 'godkendte_punkter', 'mangler_og_advarsler') MUST be written in the target language specified here: {t['ai_lang_instruction']}

Product Category: {vare_type}
Pro-forma Amount: {proforma_beloeb}
Port of Discharge: {havn_ankomst}

Combined Content:
{kombineret_tekst}
"""
                response = koer_ai_analyse(start_prompt)
                st.session_state["analyse_resultat"] = json.loads(response.choices[0].message.content)

            except Exception as e:
                st.error(f"⚠️ Error during AI Analysis: {e}")

# Vis resultater
if "analyse_resultat" in st.session_state:
    resultat = st.session_state["analyse_resultat"]

    st.markdown(f"## {t['results_header']}")
    
    if resultat.get("status_godkendt", False):
        st.success(f"{t['approved']} {resultat.get('sammenfatning')}")
    else:
        st.error(f"{t['discrepancies_found']} {resultat.get('sammenfatning')}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_res1, col_res2 = st.columns(2)

    with col_res1:
        st.markdown(f"### {t['approved_points']}")
        godkendte = resultat.get("godkendte_punkter", [])
        if godkendte:
            for punkt in godkendte:
                st.write(f"✔️ {punkt}")
        else:
            st.write(t['no_approved'])

    with col_res2:
        st.markdown(f"### {t['warnings_points']}")
        mangler = resultat.get("mangler_og_advarsler", [])
        if mangler:
            for punkt in mangler:
                st.warning(f"⚠️ {punkt}")
        else:
            st.write(t['no_warnings'])

    afvigelser = resultat.get("afvigelser", [])
    if afvigelser:
        st.markdown("---")
        st.markdown(f"### {t['detailed_discrepancies']}")
        for afv in afvigelser:
            kat = afv.get("kategori", "Discrepancy")
            besk = afv.get("beskrivelse", "")
            if afv.get("kritisk", False):
                st.error(f"**[{kat}]** {besk}")
            else:
                st.info(f"**[{kat}]** {besk}")

    # Opfølgende Chat
    st.markdown("---")
    st.subheader(t['followup_title'])
    st.caption(t['followup_caption'])

    for besk in st.session_state.get("chat_historik", []):
        with st.chat_message(besk["role"]):
            st.write(besk["content"])

    bruger_input = st.chat_input(t['chat_placeholder'])

    if bruger_input:
        if "chat_historik" not in st.session_state:
            st.session_state["chat_historik"] = []
        
        st.session_state["chat_historik"].append({"role": "user", "content": bruger_input})

        with st.spinner("🤖 ..."):
            try:
                opdateret_prompt = f"""
You are an expert in import control for Pecém, Brazil.
Latest JSON structure: {json.dumps(resultat)}

User input / query:
"{bruger_input}"

Update the JSON structure based on the new info. 
LANGUAGE REQUIREMENT: Write JSON text values in target language: {t['ai_lang_instruction']}
Return ONLY the updated JSON structure.

Combined text:
{st.session_state.get('kombineret_tekst', '')}
"""
                response = koer_ai_analyse(opdateret_prompt)
                st.session_state["analyse_resultat"] = json.loads(response.choices[0].message.content)
                st.session_state["chat_historik"].append({"role": "assistant", "content": f"Analysis updated based on: '{bruger_input}'"})
                st.rerun()

            except Exception as e:
                st.error(f"⚠️ Could not update analysis: {e}")
