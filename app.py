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
        "help_text": """
O aplicativo funciona como uma **ferramenta de comparação e cálculo inteligente**, garantindo que seus documentos de importação estejam livres de erros custosos e calculando os **custos nacionalizados com tributos brasileiros**.

* 🔍 **Comparação de Documentos:** Compare cotações, faturas pro-forma, listas de embalagem e contratos.
* 💰 **Cálculo de Nacionalização (Landed Cost):** Calcule o custo final em BRL incluindo II, IPI, PIS, COFINS, ICMS (Ceará) e frete/seguro.
* 🇧🇷 **Controle Alfandegário (Pecém):** Verificação de NCM (8 dígitos), CNPJ e certificados (MAPA / ANVISA).
* 💬 **Multiformato & Chat:** Lê PDF, Word, Excel, imagens (OCR) e e-mails/WhatsApp.
""",
        "instructions_title": "📋 Como usar o aplicativo:",
        "instructions_text": """
1. **Faça Login:** Digite a senha acima.
2. **Envie ou Cole:** Envie documentos ou cole conversas de WhatsApp/E-mail.
3. **Preencha os Dados:** Verifique a moeda (USD/EUR), taxa de câmbio, data e impostos.
4. **Calcule a Nacionalização:** Obtenha o custo total landed no Brasil em BRL.
""",
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
        "upload_logistics": "Upload de documentos logísticos (B/L, Packing List, MAPA etc.)",
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
        
        # Nacionalização
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
        "fx_info_box": "📌 **Base de Câmbio Utilizada:** 1 {curr} = **R\$ {fx:.4f}** (Data: **{dt}**)"
    },
    "en": {
        "title": "🇧🇷 Import Control & Nationalization",
        "subtitle": "Verification and landed cost calculator for imports arriving at Pecém, Brazil",
        "login_header": "🔒 Restricted Access",
        "password_label": "Enter access password",
        "login_btn": "🚀 Login to Import Control",
        "wrong_pass": "❌ Incorrect password. Please try again.",
        "help_title": "💡 How can this app help you?",
        "help_text": """
The app acts as an **intelligent comparison and calculation tool**, safeguarding your import documents against costly errors and calculating **landed costs with Brazilian taxes**.

* 🔍 **Document Comparison:** Compare quotes, pro-forma invoices, packing lists, and contracts.
* 💰 **Nationalization Calculation (Landed Cost):** Calculate final cost in BRL including II, IPI, PIS, COFINS, ICMS (Ceará), and freight/insurance.
* 🇧🇷 **Customs Control (Pecém):** Automatic checks for 8-digit NCM codes, CNPJ, and certificates (MAPA / ANVISA).
* 💬 **Multiformat & Chat:** Reads PDF, Word, Excel, images (OCR), and email/WhatsApp text.
""",
        "instructions_title": "📋 How to use the app:",
        "instructions_text": """
1. **Login:** Enter password above.
2. **Upload or Paste:** Upload files or paste WhatsApp/Email text.
3. **Fill Master Data:** Verify currency (USD/EUR), exchange rate, date, and tax rates.
4. **Calculate Landed Cost:** Get the total nationalized cost in BRL.
""",
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
        "upload_logistics": "Upload port and logistics documents (Bill of Lading, Packing List, MAPA cert, etc.)",
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
        
        # Nationalization
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
        "fx_info_box": "📌 **Exchange Rate Base Used:** 1 {curr} = **R\$ {fx:.4f}** (Date: **{dt}**)"
    },
    "da": {
        "title": "🇧🇷 Import- & Nationaliseringskontrol",
        "subtitle": "Verifikationsværktøj og beregner af nationaliserede priser for Pecém, Ceará",
        "login_header": "🔒 Begrænset Adgang",
        "password_label": "Indtast adgangskode",
        "login_btn": "🚀 Åbn Importkontrol",
        "wrong_pass": "❌ Forkert adgangskode. Prøv igen.",
        "help_title": "💡 Hvad kan appen hjælpe dig med?",
        "help_text": """
Appen fungerer som et **intelligent sammenlignings- og beregningsværktøj**, der sikrer importdokumenter mod dyre fejl og beregner **landed cost inklusiv brasilianske importafgifter**.

* 🔍 **Dokumentsammenligning:** Hold tilbud, pro-forma fakturaer, pakkelister og kontrakter op mod hinanden.
* 💰 **Nationaliseringsberegning (Landed Cost):** Beregn den endelige pris i BRL inkl. II, IPI, PIS, COFINS, ICMS (Ceará) samt fragt og forsikring.
* 🇧🇷 **Toldkontrol (Pecém):** Automatisk tjek af 8-cifrede NCM-koder, CNPJ og certifikater (MAPA / ANVISA).
* 💬 **Multiformat & Chat:** Læser PDF, Word, Excel, billeder (OCR) samt e-mail/WhatsApp-tekst.
""",
        "instructions_title": "📋 Sådan bruger du appen:",
        "instructions_text": """
1. **Log ind:** Indtast adgangskoden ovenfor.
2. **Upload eller Indsæt:** Upload dokumenter eller klistr WhatsApp/e-mails ind.
3. **Udfyld Stamdata:** Tjek valuta (USD/EUR), valutakurs, dato og afgiftssatser.
4. **Beregning:** Få den samlede nationaliserede pris i BRL leveret i Brasilien.
""",
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
        "upload_logistics": "Upload havne- og logistikdokumenter (B/L, Pakkeliste, MAPA certifikat osv.)",
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
        
        # Nationalization
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
        "fx_info_box": "📌 **Anvendt Valutakurs:** 1 {curr} = **R\$ {fx:.4f}** (Dato: **{dt}**)"
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
    # HOVEDAPPLIKATION (NÅR LOGGARET IND)
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
