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
