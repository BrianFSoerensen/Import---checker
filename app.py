import streamlit as st
import pdfplumber
import docx
import openpyxl
import easyocr
from PIL import Image
import io
import re
import json

from datetime import date
from openai import OpenAI

# Sæt sideopsætning
st.set_page_config(
    page_title="Import Control - Pecém 🇧🇷", 
    page_icon="🇧🇷", 
    layout="wide"
)

# Initialiser EasyOCR til billeder
@st.cache_resource
def get_ocr_reader():
    return easyocr.Reader(['pt', 'en', 'da', 'es'])

# ==========================================
# 0. SPROGORDBOG (TRANSLATIONS)
# ==========================================
TRANSLATIONS = {
    "pt": {
        "title": "🇧🇷 Controle de Importação & Nacionalização",
        "subtitle": "Ferramenta de verificação e cálculo de custos nacionalizados para Pecém, Ceará",
        "login_header": "🔒 Acesso Restrito",
        "password_label": "Digite a senha de acesso",
        "login_btn": "🚀 Entrar no Controle de Importação",
        "wrong_pass": "❌ Senha incorreta. Tente novamente.",
        "help_title": "💡 Como o aplicativo pode te ajudar?",
        "help_text": "O aplicativo funciona como uma ferramenta de comparação e cálculo inteligente, garantindo que seus documentos de importação estejam livres de erros e calculando custos com tributos.",
        "instructions_title": "📋 Como usar o aplicativo:",
        "instructions_text": "1. Faça Login. 2. Envie documentos ou cole textos. 3. Preencha os dados e taxas. 4. Execute a análise.",
        "notice": "ℹ️ *Nota: Arquivos e textos são usados exclusivamente para a comparação atual e não são salvos.*",
        "sec_docs": "📂 Documentos & Correspondência",
        "upload_label": "Upload de cotações, contratos ou imagens (PDF, Word, Excel, TXT, PNG, JPG)",
        "chat_paste_label": "💬 Copie e cole textos de e-mails, WhatsApp ou conversas aqui (Opcional):",
        "chat_paste_placeholder": "Exemplo:\n'O fornecedor confirmou no WhatsApp que o preço é €1.05/kg FOB e o frete marítimo é €2.500...'",
        "supplier_found": "Fornecedor identificado automaticamente:",
        "currency_select_label": "Moeda Principal dos Documentos:",
        "tab1": "1️⃣ Oferta & Acordo Ativo",
        "tab2": "2️⃣ Comparação Pro-forma",
        "tab3": "3️⃣ Portos & Logística",
        "tab4": "4️⃣ Calculadora de Nacionalização 💰",
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
        "proforma_amount": "Valor FOB/EXW da Mercadoria",
        "upload_proforma": "Upload da fatura pro-forma específica",
        "pol_label": "Porto de Origem (POL)",
        "pod_label": "Porto de Destino (POD)",
        "etd_label": "Data Prevista de Saída (ETD)",
        "eta_label": "Data Prevista de Chegada (ETA)",
        "upload_logistics": "Upload de documentos logísticos",
        "run_ai_btn": "🚀 Executar Comparação IA & Análise Completa",
        "no_docs_warn": "⚠️ Envie pelo menos um documento/imagem ou cole o texto do e-mail/chat.",
        "analyzing": "🤖 A IA está analisando os documentos e calculando...",
        "results_header": "📊 Resultado da Análise",
        "approved": "🟢 APROVADO:",
        "discrepancies_found": "🔴 ATENÇÃO / DISCREPÂNCIAS ENCONTRADAS:",
        "approved_points": "✅ Pontos Aprovados",
        "warnings_points": "⚠️ Pendências & Alertas",
        "detailed_discrepancies": "🚨 Discrepâncias Detalhadas",
        "no_approved": "Nenhum ponto aprovado registrado.",
        "no_warnings": "Nenhuma pendência encontrada.",
        "followup_title": "💬 Pergunte ou atualize a análise",
        "followup_caption": "Escreva perguntas sobre a análise ou adicione informações para atualizar.",
        "chat_placeholder": "Escreva suas dúvidas ou novas informações aqui...",
        "ai_lang_instruction": "Responda obrigatoriamente em PORTUGUÊS DO BRASIL.",
        "nat_title": "🧮 Simulação de Custos de Nacionalização (Brasil / Pecém)",
        "nat_desc": "Defina a moeda, taxa de câmbio, data da cotação e alíquotas tributárias.",
        "weight_qty": "Quantidade Total (kg / caixas)",
        "freight_cost": "Frete Internacional",
        "insurance_cost": "Seguro Internacional",
        "exchange_rate": "Taxa de Câmbio (1 {curr} = X BRL)",
        "fx_date": "Data da Cotação do Câmbio",
        "ii_rate": "Imposto de Importação - II (%)",
        "ipi_rate": "IPI (%)",
        "pis_cofins_rate": "PIS + COFINS (%)",
        "icms_rate": "ICMS Ceará (%)",
        "cif_res": "Valor CIF / Aduaneiro",
        "tax_res": "Total de Impostos Estimados",
        "total_landed": "Custo Total Nacionalizado",
        "unit_landed": "Custo Final por Unidade/kg",
        "fx_info_box": "📌 **Base de Câmbio Utilizada:** 1 {curr} = **R$ {fx:.4f}** (Data: **{dt}**)"
    },
    "en": {
        "title": "🇧🇷 Import Control & Nationalization",
        "subtitle": "Verification and landed cost calculator for imports arriving at Pecém, Brazil",
        "login_header": "🔒 Restricted Access",
        "password_label": "Enter access password",
        "login_btn": "🚀 Login to Import Control",
        "wrong_pass": "❌ Incorrect password. Please try again.",
        "help_title": "💡 How can this app help you?",
        "help_text": "The app acts as an intelligent comparison and calculation tool, safeguarding your import documents against costly errors and calculating landed costs.",
        "instructions_title": "📋 How to use the app:",
        "instructions_text": "1. Login. 2. Upload files or paste text. 3. Fill data and rates. 4. Run analysis.",
        "notice": "ℹ️ *Note: Files and text are used exclusively for current comparison and are not saved.*",
        "sec_docs": "📂 Documents & Correspondence",
        "upload_label": "Upload quotes, contracts, or images (PDF, Word, Excel, TXT, PNG, JPG)",
        "chat_paste_label": "💬 Copy & paste text from emails, WhatsApp or chat here (Optional):",
        "chat_paste_placeholder": "Example:\n'Supplier confirmed on WhatsApp today that the price is €1.05/kg FOB and sea freight is €2,500...'",
        "supplier_found": "Supplier automatically detected:",
        "currency_select_label": "Primary Document Currency:",
        "tab1": "1️⃣ Quote & Active Agreement",
        "tab2": "2️⃣ Pro-forma Comparison",
        "tab3": "3️⃣ Ports & Logistics",
        "tab4": "4️⃣ Landed Cost Calculator 💰",
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
        "proforma_amount": "FOB/EXW Goods Value",
        "upload_proforma": "Upload specific pro-forma invoice",
        "pol_label": "Port of Loading (POL)",
        "pod_label": "Port of Discharge (POD)",
        "etd_label": "Expected Departure Date (ETD)",
        "eta_label": "Expected Arrival Date (ETA)",
        "upload_logistics": "Upload port and logistics documents",
        "run_ai_btn": "🚀 Run AI Comparison & Full Analysis",
        "no_docs_warn": "⚠️ Please upload at least one document/image or paste email/chat text.",
        "analyzing": "🤖 AI is analyzing documents and calculating...",
        "results_header": "📊 Analysis Results",
        "approved": "🟢 APPROVED:",
        "discrepancies_found": "🔴 ATTENTION / DISCREPANCIES FOUND:",
        "approved_points": "✅ Approved Items",
        "warnings_points": "⚠️ Pending Items & Warnings",
        "detailed_discrepancies": "🚨 Detailed Discrepancies",
        "no_approved": "No approved items recorded.",
        "no_warnings": "No pending items found.",
        "followup_title": "💬 Ask or update the analysis",
        "followup_caption": "Type questions about the analysis or add information to update.",
        "chat_placeholder": "Type your questions or new information here...",
        "ai_lang_instruction": "You MUST respond in ENGLISH.",
        "nat_title": "🧮 Nationalization Cost Simulation (Brazil / Pecém)",
        "nat_desc": "Set document currency, exchange rate, quote date, and tax parameters.",
        "weight_qty": "Total Quantity (kg / boxes)",
        "freight_cost": "International Freight",
        "insurance_cost": "International Insurance",
        "exchange_rate": "Exchange Rate (1 {curr} = X BRL)",
        "fx_date": "Exchange Rate Date",
        "ii_rate": "Import Duty - II (%)",
        "ipi_rate": "IPI (%)",
        "pis_cofins_rate": "PIS + COFINS (%)",
        "icms_rate": "ICMS Ceará (%)",
        "cif_res": "CIF / Customs Value",
        "tax_res": "Estimated Total Taxes",
        "total_landed": "Total Nationalized Cost",
        "unit_landed": "Final Cost per Unit/kg",
        "fx_info_box": "📌 **Exchange Rate Base Used:** 1 {curr} = **R$ {fx:.4f}** (Date: **{dt}**)"
    },
    "da": {
        "title": "🇧🇷 Import- & Nationaliseringskontrol",
        "subtitle": "Verifikationsværktøj og beregner af nationaliserede priser for Pecém, Ceará",
        "login_header": "🔒 Begrænset Adgang",
        "password_label": "Indtast adgangskode",
        "login_btn": "🚀 Åbn Importkontrol",
        "wrong_pass": "❌ Forkert adgangskode. Prøv igen.",
        "help_title": "💡 Hvad kan appen hjælpe dig med?",
        "help_text": "Appen fungerer som et intelligent sammenlignings- og beregningsværktøj, der sikrer importdokumenter mod fejl og beregner landed cost inklusiv afgifter.",
        "instructions_title": "📋 Sådan bruger du appen:",
        "instructions_text": "1. Log ind. 2. Upload dokumenter eller tekst. 3. Tjek valuta og satser. 4. Beregn.",
        "notice": "ℹ️ *Bemærk: Filer og tekst bruges udelukkende til den aktuelle sammenligning og gemmes ikke.*",
        "sec_docs": "📂 Dokumenter & Korrespondance",
        "upload_label": "Upload tilbud, kontrakter eller bilag (PDF, Word, Excel, TXT, PNG, JPG)",
        "chat_paste_label": "💬 Kopiér & indsæt tekst fra e-mails, WhatsApp eller chat her (Valgfrit):",
        "chat_paste_placeholder": "Eksempel:\n'Leverandør har bekræftet på WhatsApp at prisen er €1.05/kg FOB og søfragten er €2.500...'",
        "supplier_found": "Fandt leverandør automatisk:",
        "currency_select_label": "Hovedvaluta i Dokumenter:",
        "tab1": "1️⃣ Tilbud & Aktiv Aftale",
        "tab2": "2️⃣ Pro-forma Sammenligning",
        "tab3": "3️⃣ Havne & Logistik",
        "tab4": "4️⃣ Landed Cost & Toldberegner 💰",
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
        "proforma_amount": "FOB/EXW Vareværdi",
        "upload_proforma": "Upload specifik pro-forma faktura",
        "pol_label": "Afgangshavn (POL)",
        "pod_label": "Ankomsthavn (POD)",
        "etd_label": "Forventet Afgangsdato (ETD)",
        "eta_label": "Forventet Ankomstdato (ETA)",
        "upload_logistics": "Upload havne- og logistikdokumenter",
        "run_ai_btn": "🚀 Kør AI Sammenligning & Samlet Analyse",
        "no_docs_warn": "⚠️ Upload venligst mindst ét dokument/billede eller indsæt e-mail/chattekst.",
        "analyzing": "🤖 AI'en analyserer dokumenter og beregner afgifter...",
        "results_header": "📊 Analyseresultat",
        "approved": "🟢 GODKENDT:",
        "discrepancies_found": "🔴 OBS / AFVIGELSER FUNDET:",
        "approved_points": "✅ Godkendte Punkter",
        "warnings_points": "⚠️ Mangler & Tjekpunkter",
        "detailed_discrepancies": "🚨 Detaljerede Afvigelser",
        "no_approved": "Ingen registrerede godkendte punkter.",
        "no_warnings": "Ingen mangler fundet.",
        "followup_title": "💬 Spørg eller opdater analysen",
        "followup_caption": "Skriv spørgsmål til analysen eller tilføj oplysninger for at genberegne.",
        "chat_placeholder": "Skriv spørgsmål eller yderligere oplysninger her...",
        "ai_lang_instruction": "Du SKAL svare på DANSK.",
        "nat_title": "🧮 Nationaliseringsberegner (Brasilien / Pecém)",
        "nat_desc": "Angiv dokumentvaluta, valutakurs, dato for kursen og skattesatser.",
        "weight_qty": "Samlet Mængde (kg / kasser)",
        "freight_cost": "International Fragt",
        "insurance_cost": "International Forsikring",
        "exchange_rate": "Valutakurs (1 {curr} = X BRL)",
        "fx_date": "Dato for Valutakurs",
        "ii_rate": "Importafgift - II (%)",
        "ipi_rate": "IPI (%)",
        "pis_cofins_rate": "PIS + COFINS (%)",
        "icms_rate": "ICMS Ceará (%)",
        "cif_res": "CIF / Toldværdi",
        "tax_res": "Estimerede Samlede Skatter",
        "total_landed": "Samlet Nationaliseret Pris",
        "unit_landed": "Endelig Pris pr. Enhed/kg",
        "fx_info_box": "📌 **Anvendt Valutakurs:** 1 {curr} = **R$ {fx:.4f}** (Dato: **{dt}**)"
    }
}

# ==========================================
# 1. SPROG- OG SESSION-INITIALISERING
# ==========================================
if "lang" not in st.session_state:
    st.session_state["lang"] = "pt"

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

# ==========================================
# 2. LOGIN / VELKOMSTSKÆRM ELLER HOVEDAPP
# ==========================================
if not st.session_state["password_correct"]:
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        selected_lang_code = st.selectbox(
            "🌐 Idioma / Language / Sprog:",
            options=["pt", "en", "da"],
            format_func=lambda x: "🇧🇷 Português (Brasil)" if x == "pt" else ("🇬🇧 English" if x == "en" else "🇩🇰 Dansk"),
            index=["pt", "en", "da"].index(st.session_state["lang"])
        )
        st.session_state["lang"] = selected_lang_code
        t = TRANSLATIONS[selected_lang_code]

        st.markdown(f"# {t['title']}")
        st.caption(t['subtitle'])
        st.markdown("---")

        st.markdown(f"### {t['login_header']}")
        password_input = st.text_input(t['password_label'], type="password")
        
        if st.button(t['login_btn'], type="primary", use_container_width=True):
            if password_input == "brasilien2026":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error(t['wrong_pass'])

        st.markdown("---")
        st.markdown(f"### {t['help_title']}")
        st.markdown(t['help_text'])
        st.markdown("---")
        st.markdown(f"### {t['instructions_title']}")
        st.markdown(t['instructions_text'])

else:
    # ------------------------------------------
    # HOVEDAPPLIKATION (NÅR LOGGET IND)
    # ------------------------------------------
    lang_code = st.session_state["lang"]
    t = TRANSLATIONS[lang_code]

    ACCEPTED_TYPES = ["pdf", "docx", "xlsx", "txt", "png", "jpg", "jpeg"]

    def udtraek_tekst_fra_fil(fil):
        tekst = ""
        fil_navn = fil.name
        fil_ext = fil_navn.split(".")[-1].lower()

        try:
            if fil_ext == "pdf":
                with pdfplumber.open(fil) as pdf:
                    for page in pdf.pages:
                        tekst += (page.extract_text() or "") + "\n"
            elif fil_ext == "docx":
                doc = docx.Document(fil)
                for p in doc.paragraphs:
                    tekst += p.text + "\n"
                for table in doc.tables:
                    for row in table.rows:
                        row_text = [cell.text.strip() for cell in row.cells]
                        tekst += " | ".join(row_text) + "\n"
            elif fil_ext == "xlsx":
                wb = openpyxl.load_workbook(fil, data_only=True)
                for sheet in wb.sheetnames:
                    ws = wb[sheet]
                    tekst += f"\n--- Sheet: {sheet} ---\n"
                    for row in ws.iter_rows(values_only=True):
                        row_vals = [str(val) if val is not None else "" for val in row]
                        if any(row_vals):
                            tekst += " | ".join(row_vals) + "\n"
            elif fil_ext == "txt":
                tekst = fil.read().decode("utf-8", errors="ignore")
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

    # OpenAI Klient
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    except Exception:
        st.error("⚠️ OPENAI_API_KEY not found in Streamlit Secrets.")

    col_title, col_lang = st.columns([3, 1])

    with col_lang:
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

    # Automatisk valutadetektion fra tekst (eller manuel overstyring)
    detected_currency = "EUR" if "EUR" in samlet_pdf_tekst or "€" in samlet_pdf_tekst else ("USD" if "USD" in samlet_pdf_tekst or "$" in samlet_pdf_tekst else "EUR")

    col_curr_select, col_space = st.columns([1, 2])
    with col_curr_select:
        valgt_valuta = st.selectbox(
            t["currency_select_label"],
            options=["EUR", "USD"],
            index=0 if detected_currency == "EUR" else 1,
            help="Vælg om dokumentpriser er angivet i EUR eller USD."
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Opdeling i 4 faner (Inkl. Nacionalização)
    tab1, tab2, tab3, tab4 = st.tabs([
        t["tab1"], 
        t["tab2"], 
        t["tab3"],
        t["tab4"]
    ])

    with tab1:
        st.header(t["tab1"])
        col1, col2 = st.columns(2)
        with col1:
            producent = st.text_input(t["supplier_input"], value=udlaest_leverandoer)
        with col2:
            vare_type = st.selectbox(t["product_type"], [t["prod_fries"], t["prod_meat"], t["prod_oil"], t["prod_canned"], t["prod_other"]])

    with tab2:
        st.header(t["tab2"])
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 📋 {t['active_agreement']}")
            st.write(f"**{t['supplier_input']}:** {producent if producent else '-'}")
            st.write(f"**{t['product_type']}:** {vare_type}")
            st.write(f"**Moeda / Valuta:** {valgt_valuta}")
        with col2:
            st.markdown(f"### 📄 {t['proforma_info']}")
            proforma_no = st.text_input(t["proforma_no"])
            proforma_beloeb = st.number_input(f"{t['proforma_amount']} ({valgt_valuta})", min_value=0.0, step=100.0)

        proforma_filer = st.file_uploader(t["upload_proforma"], type=ACCEPTED_TYPES, accept_multiple_files=True, key="proforma_docs")
        proforma_tekst = ""
        if proforma_filer:
            for p_fil in proforma_filer:
                proforma_tekst += f"\n--- Pro-forma ({p_fil.name}) ---\n" + udtraek_tekst_fra_fil(p_fil)

    with tab3:
        st.header(t["tab3"])
        col1, col2 = st.columns(2)
        with col1:
            havn_afgang = st.text_input(t["pol_label"], placeholder="e.g. Rotterdam, Santos")
            havn_ankomst = st.text_input(t["pod_label"], value="Pecém, Ceará, Brasil")
        with col2:
            etd = st.date_input(t["etd_label"])
            eta = st.date_input(t["eta_label"])

        logistik_filer = st.file_uploader(t["upload_logistics"], type=ACCEPTED_TYPES, accept_multiple_files=True, key="logistik_docs")
        logistik_tekst = ""
        if logistik_filer:
            for l_fil in logistik_filer:
                logistik_tekst += f"\n--- Logistics ({l_fil.name}) ---\n" + udtraek_tekst_fra_fil(l_fil)

    with tab4:
        st.header(t["nat_title"])
        st.write(t["nat_desc"])
        
        col_n1, col_n2, col_n3 = st.columns(3)
        default_fx = 6.10 if valgt_valuta == "EUR" else 5.50
        
        with col_n1:
            st.markdown(f"##### 📦 Vare & Fragt ({valgt_valuta})")
            val_fob = st.number_input(f"Valor Mercadoria ({valgt_valuta})", value=float(proforma_beloeb), min_value=0.0)
            val_qty = st.number_input(t["weight_qty"], value=24000.0, min_value=1.0)
            val_freight = st.number_input(f"{t['freight_cost']} ({valgt_valuta})", value=2500.0, min_value=0.0)
            val_insurance = st.number_input(f"{t['insurance_cost']} ({valgt_valuta})", value=150.0, min_value=0.0)

        with col_n2:
            st.markdown("##### 💱 Câmbio & Impostos Federais")
            val_fx_date = st.date_input(t["fx_date"], value=date.today())
            val_fx = st.number_input(t["exchange_rate"].format(curr=valgt_valuta), value=default_fx, min_value=0.1, step=0.01, format="%.4f")
            rate_ii = st.number_input(t["ii_rate"], value=10.0, min_value=0.0, max_value=100.0)
            rate_ipi = st.number_input(t["ipi_rate"], value=0.0, min_value=0.0, max_value=100.0)

        with col_n3:
            st.markdown("##### 🏖️ Impostos Estaduais (Ceará)")
            rate_piscofins = st.number_input(t["pis_cofins_rate"], value=11.75, min_value=0.0, max_value=100.0)
            rate_icms = st.number_input(t["icms_rate"], value=20.0, min_value=0.0, max_value=100.0)

        cif_foreign = val_fob + val_freight + val_insurance
        cif_brl = cif_foreign * val_fx
        
        val_ii = cif_brl * (rate_ii / 100.0)
        val_ipi = (cif_brl + val_ii) * (rate_ipi / 100.0)
        val_piscofins = cif_brl * (rate_piscofins / 100.0)
        
        base_icms = (cif_brl + val_ii + val_ipi + val_piscofins) / (1.0 - (rate_icms / 100.0)) if rate_icms < 100 else 0
        val_icms = base_icms * (rate_icms / 100.0)
        
        total_impostos_brl = val_ii + val_ipi + val_piscofins + val_icms
        total_landed_brl = cif_brl + total_impostos_brl
        unit_landed_brl = total_landed_brl / val_qty if val_qty > 0 else 0

        st.markdown("---")
        st.info(t["fx_info_box"].format(curr=valgt_valuta, fx=val_fx, dt=val_fx_date.strftime('%d/%m/%Y')))
        st.markdown("### 📊 Resultado da Simulação")
        
        c_res1, c_res2, c_res3, c_res4 = st.columns(4)
        c_res1.metric(t["cif_res"], f"R$ {cif_brl:,.2f}", f"{cif_foreign:,.2f} {valgt_valuta}")
        c_res2.metric(t["tax_res"], f"R$ {total_impostos_brl:,.2f}")
        c_res3.metric(t["total_landed"], f"R$ {total_landed_brl:,.2f}")
        c_res4.metric(t["unit_landed"], f"R$ {unit_landed_brl:,.2f} / kg")

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
  "sammenfatning": "A concise summary including nationalization cost assessment",
  "afvigelser": [
    {{"kategori": "Price/Taxes", "beskrivelse": "Explanation...", "kritisk": true/false}}
  ],
  "godkendte_punkter": [
    "Supplier name matches"
  ],
  "mangler_og_advarsler": [
    "Missing 8-digit NCM code"
  ]
}}

STRICT CURRENCY RULE: The document currency is verified as {valgt_valuta}. DO NOT write EUR/USD, ONLY write {valgt_valuta} or BRL.
Exchange Rate Used: 1 {valgt_valuta} = {val_fx} BRL (Date: {val_fx_date.strftime('%d/%m/%Y')}).

LANGUAGE REQUIREMENT: Write all text values in: {t['ai_lang_instruction']}

Product Category: {vare_type}
Pro-forma Amount: {proforma_beloeb} {valgt_valuta}
Port of Discharge: {havn_ankomst}
Calculated CIF (BRL): R$ {cif_brl:,.2f} ({cif_foreign:,.2f} {valgt_valuta})
Calculated Total Landed Cost (BRL): R$ {total_landed_brl:,.2f}

Combined Content:
{kombineret_tekst}
"""
                    response = koer_ai_analyse(start_prompt)
                    st.session_state["analyse_resultat"] = json.loads(response.choices[0].message.content)

                except Exception as e:
                    st.error(f"⚠️ Error during AI Analysis: {e}")

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

Currency: {valgt_valuta}. Exchange rate: 1 {valgt_valuta} = {val_fx} BRL ({val_fx_date.strftime('%d/%m/%Y')}).
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
