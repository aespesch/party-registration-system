"""
Party Registration System - Main Application
A complete web system for managing event attendance confirmations and payments.
"""

import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import base64
import os
from datetime import datetime
import unicodedata
import re
import uuid
import crcmod
from config import *


# Page configuration
st.set_page_config(**PAGE_CONFIG)

# Initialize session state
if 'confirmed' not in st.session_state:
    st.session_state.confirmed = False
if 'participant_data' not in st.session_state:
    st.session_state.participant_data = None
if 'show_payment' not in st.session_state:
    st.session_state.show_payment = False
if 'guest_counts' not in st.session_state:
    st.session_state.guest_counts = None
if 'total_amount' not in st.session_state:
    st.session_state.total_amount = 0

def normalize_name(name):
    """
    Normalize name for comparison by removing accents, extra spaces, 
    and converting to lowercase.
    """
    # If name is not a string, return empty string
    if not isinstance(name, str):
        return ""
    
    # Remove leading/trailing spaces
    name = name.strip()
    
    if name == "":
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Normalize to decomposed form and remove accents
    name = unicodedata.normalize('NFKD', name)
    name = ''.join([c for c in name if not unicodedata.combining(c)])
    
    # Remove non-alphanumeric characters except spaces
    name = re.sub(r'[^a-z0-9\s]', '', name)
    
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    
    return name

def load_participants():
    """Load participants from CSV file with debug info."""
    try:
        # Get absolute path and show debug info
        abs_path = os.path.abspath(PARTICIPANTS_FILE)
        #st.info(f"🔍 Tentando carregar arquivo: {abs_path}")
        
        # Try common encodings for Portuguese
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(PARTICIPANTS_FILE, encoding=encoding)
                #st.success(f"✅ Arquivo carregado com sucesso usando codificação: {encoding}")
                break
            except UnicodeDecodeError:
                st.warning(f"⚠️ Falha ao decodificar com {encoding}, tentando próxima...")
                continue
            except Exception as e:
                st.error(f"❌ Erro inesperado com codificação {encoding}: {str(e)}")
                continue
        
        if df is None:
            st.error("❌ Não foi possível carregar o arquivo com nenhuma codificação testada.")
            return pd.DataFrame()
        
        #st.info(f"📊 Total de registros carregados: {len(df)}")
        
        # Show first two rows for debugging
        # if not df.empty:
        #     st.info("📝 Amostra do arquivo (2 primeiras linhas):")
        #     st.dataframe(df.head(2))
        # else:
        #     st.warning("⚠️ O arquivo foi carregado, mas está vazio.")
        
        return df
    
    except FileNotFoundError:
        st.error(f"❌ Arquivo não encontrado: {PARTICIPANTS_FILE}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro inesperado ao carregar o arquivo: {str(e)}")
        return pd.DataFrame()

def find_participant(name, participants_df):
    """Find participant in the list with flexible name matching and debug info."""
    # st.info(f"🔍 Buscando por: '{name}'")
    normalized_input = normalize_name(name)
    # st.info(f"🔠 Nome normalizado: '{normalized_input}'")
    
    if participants_df.empty:
        st.warning("⚠️ A lista de participantes está vazia. Nenhum nome pode ser encontrado.")
        return None
    
    # Iterate over each row in the dataframe
    for idx, row in participants_df.iterrows():
        if 'full_name' in row:
            original_db_name = row['full_name']
            normalized_db_name = normalize_name(original_db_name)
            
            # Log comparison for debugging
            # st.info(f"🔍 Comparando com: '{original_db_name}' -> Normalizado: '{normalized_db_name}'")
            
            if normalized_input == normalized_db_name:
                st.success(f"✅ Correspondência encontrada para: {original_db_name}")
                return row
    
    st.warning("⚠️ Nenhuma correspondência encontrada na lista de participantes.")
    return None

def calculate_total(guests_under_5, guests_5_to_12, guests_above_12):
    """Calculate total amount based on guest counts."""
    total = (guests_under_5 * PRICING['under_5'] + 
             guests_5_to_12 * PRICING['5_to_12'] + 
             guests_above_12 * PRICING['above_12'])
    return total

def generate_emv_code(key, amount, merchant_name, city, tx_id=None):
    """Generate 100% valid PIX EMV code following Brazilian Central Bank specs"""
    # Helper function to sanitize and format text
    def format_text(text, max_length, remove_accents=True):
        if remove_accents:
            # Remove accents
            text = unicodedata.normalize('NFD', text)
            text = ''.join(c for c in text if not unicodedata.combining(c))
        # Keep spaces and basic punctuation for readability
        text = re.sub(r'[^a-zA-Z0-9\s\.\-]', '', text)
        # Truncate to max length
        return text[:max_length]
    
    # Format amount with ALWAYS 2 decimal places
    amount_str = f"{amount:.2f}"
    
    # Clean the PIX key (remove spaces and special chars)
    clean_key = re.sub(r'[^a-zA-Z0-9@\.\-]', '', key)
    
    # Sanitize merchant name and city
    sanitized_merchant = format_text(merchant_name, 25, remove_accents=True).upper()
    sanitized_city = format_text(city, 15, remove_accents=True).upper()
    
    # Build payload components
    payload = "000201"  # Payload format indicator
    
    # Merchant Account Information (26)
    gui = "BR.GOV.BCB.PIX"
    # Format: 0014BR.GOV.BCB.PIX + 01 + key length + key
    pix_key_field = f"01{len(clean_key):02d}{clean_key}"
    pix_data = f"0014{gui}{pix_key_field}"
    payload += f"26{len(pix_data):02d}{pix_data}"
    
    # Merchant Category Code (52)
    mcc = "0000"
    payload += f"52{len(mcc):02d}{mcc}"
    
    # Transaction Currency (53)
    currency = "986"  # BRL
    payload += f"53{len(currency):02d}{currency}"
    
    # Transaction Amount (54) - only include if amount > 0
    if amount > 0:
        payload += f"54{len(amount_str):02d}{amount_str}"
    
    # Country Code (58)
    country = "BR"
    payload += f"58{len(country):02d}{country}"
    
    # Merchant Name (59)
    payload += f"59{len(sanitized_merchant):02d}{sanitized_merchant}"
    
    # Merchant City (60)
    payload += f"60{len(sanitized_city):02d}{sanitized_city}"
    
    # Additional Data Field (62) - Transaction ID
    if tx_id and tx_id != "***":
        tx_field = f"05{len(tx_id):02d}{tx_id}"
        payload += f"62{len(tx_field):02d}{tx_field}"
    else:
        # Generate a unique transaction ID
        unique_id = f"PIX{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8]}"
        tx_field = f"05{len(unique_id):02d}{unique_id}"
        payload += f"62{len(tx_field):02d}{tx_field}"
    
    # Add CRC placeholder
    payload += "6304"
    
    # Calculate CRC16-CCITT
    crc16 = crcmod.predefined.Crc('crc-ccitt-false')
    crc16.update(payload.encode('utf-8'))
    crc_value = format(crc16.crcValue, '04X')
    
    return payload + crc_value

def generate_pix_qr_code(amount, participant_name, participant_id=None, tx_id=None):
    """Generate PIX QR Code for payment with participant ID comment"""
    # Generate a unique transaction ID with participant ID comment
    if not tx_id:
        # Add participant ID as comment in transaction ID format: IDNNNID
        if participant_id is not None and str(participant_id).strip() != '':
            tx_id = f"ID{participant_id}ID"
        else:
            # Fallback to unique transaction ID if no participant ID
            tx_id = f"PIX{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6]}"
    
    # Pass transaction ID with participant ID comment
    pix_payload = generate_emv_code(
        PIX_KEY,
        amount,
        PIX_MERCHANT_NAME,
        PIX_CITY,
        tx_id=tx_id
    )
    
    # Generate QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(pix_payload)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    buf = BytesIO()
    img.save(buf, format='PNG')
    byte_img = buf.getvalue()
    
    return byte_img, pix_payload

def save_confirmation(participant_data, guest_counts, total_amount):
    """Save confirmation to CSV file."""
    # Create confirmations directory if it doesn't exist
    os.makedirs('./data', exist_ok=True)
    
    confirmation_id = str(uuid.uuid4())[:8]
    
    confirmation_data = {
        'confirmation_id': confirmation_id,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'participant_name': participant_data['full_name'],
        'participant_id': participant_data.get('id', ''),
        'guests_under_5': guest_counts['under_5'],
        'guests_5_to_12': guest_counts['5_to_12'],
        'guests_above_12': guest_counts['above_12'],
        'total_amount': total_amount,
        'payment_status': 'pending'
    }
    
    # Check if file exists
    file_path = './data/confirmations.csv'
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df = pd.concat([df, pd.DataFrame([confirmation_data])], ignore_index=True)
    else:
        df = pd.DataFrame([confirmation_data])
    
    df.to_csv(file_path, index=False)
    
    return confirmation_id

def show_guest_form():
    """Show the guest information form."""
    participant = st.session_state.participant_data
    
    st.markdown(f"### Bem-vindo(a), {participant['full_name']}! 👋")
    
    # Attendance confirmation
    will_attend = st.radio("Você irá ao evento?", 
                           ["Sim, confirmo presença", "Não poderei comparecer"])
    
    if will_attend == "Não poderei comparecer":
        st.info(MESSAGES['thank_you_not_attending'])
        if st.button("Finalizar"):
            st.session_state.confirmed = False
            st.session_state.participant_data = None
            st.rerun()
    else:
        st.markdown("### 👥 Informações sobre Participantes (R$ 250/pessoa)")
        st.markdown("Só está sendo cobrado 30% do valor total. Abaixo de 5 anos é grátis. Entre 5 e 12 anos paga meia.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Crianças até 5 anos** (Grátis)")
            guests_under_5 = st.number_input("Quantidade:", 
                                              min_value=0, 
                                              max_value=MAX_GUESTS_PER_CATEGORY,
                                              value=0,
                                              key="under_5")
        
        with col2:
            st.markdown(f"**Crianças 5-12 anos** (R$ {PRICING['5_to_12']})")
            guests_5_to_12 = st.number_input("Quantidade:", 
                                              min_value=0, 
                                              max_value=MAX_GUESTS_PER_CATEGORY,
                                              value=0,
                                              key="5_to_12")
        
        with col3:
            st.markdown(f"**Acima de 12 anos** (R$ {PRICING['above_12']})")
            guests_above_12 = st.number_input("Quantidade:", 
                                               min_value=1,  # At least the participant
                                               max_value=MAX_GUESTS_PER_CATEGORY,
                                               value=1,
                                               key="above_12")
        
        # Calculate total
        guest_counts = {
            'under_5': guests_under_5,
            '5_to_12': guests_5_to_12,
            'above_12': guests_above_12
        }
        
        total_amount = calculate_total(guests_under_5, guests_5_to_12, guests_above_12)
        
        st.markdown("---")
        st.markdown(f"### 💰 Valor Total: R$ {total_amount:.2f}")
        
        # Generate payment
        if total_amount > 0:
            if st.button("Gerar QR Code para Pagamento", type="primary"):
                st.session_state.guest_counts = guest_counts
                st.session_state.total_amount = total_amount
                st.session_state.show_payment = True
                st.rerun()
        else:
            # Free entry (only children under 5)
            if st.button("Confirmar Presença", type="primary"):
                confirmation_id = save_confirmation(participant, guest_counts, total_amount)
                st.success(f"✅ Confirmação registrada! ID: {confirmation_id}")
                st.info("Entrada gratuita confirmada!")
                
                if st.button("Nova Confirmação"):
                    st.session_state.confirmed = False
                    st.session_state.participant_data = None
                    st.rerun()

def show_payment_page():
    """Show the payment page with QR code."""
    participant = st.session_state.participant_data
    guest_counts = st.session_state.guest_counts
    total_amount = st.session_state.total_amount
    
    st.markdown(f"### 💳 Pagamento - {participant['full_name']}")
    st.markdown("---")
    
    # Save confirmation
    confirmation_id = save_confirmation(participant, guest_counts, total_amount)
    
    # Generate QR Code and get PIX payload
    participant_id = participant.get('id', '')
    qr_img, pix_payload = generate_pix_qr_code(total_amount, participant['full_name'], participant_id)
    
    # Display QR Code
    st.markdown("### 📱 QR Code PIX")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(qr_img, width=300)
    
    # Display PIX copy code
    st.markdown("### 📋 Código PIX Copia e Cola")
    st.markdown("Clique no botão de copiar no canto direito do campo abaixo:")
    st.code(pix_payload, language=None)
    
    # Display amount breakdown
    st.markdown("### 📊 Resumo dos Valores")
    
    if guest_counts['under_5'] > 0:
        st.markdown(f"- **Crianças até 5 anos:** {guest_counts['under_5']} × R\\$ {PRICING['under_5']:.2f} = R\\$ {guest_counts['under_5'] * PRICING['under_5']:.2f}")
    
    if guest_counts['5_to_12'] > 0:
        st.markdown(f"- **Crianças 5-12 anos:** {guest_counts['5_to_12']} × R\\$ {PRICING['5_to_12']:.2f} = R\\$ {guest_counts['5_to_12'] * PRICING['5_to_12']:.2f}")
    
    if guest_counts['above_12'] > 0:
        st.markdown(f"- **Acima de 12 anos:** {guest_counts['above_12']} × R\\$ {PRICING['above_12']:.2f} = R\\$ {guest_counts['above_12'] * PRICING['above_12']:.2f}")
    
    st.markdown(f"### 💰 **Total a pagar: R\\$ {total_amount:.2f}**")
    
    st.markdown("---")
    
    # Payment instructions
    st.markdown(MESSAGES['payment_instructions'])
    
    # Confirmation details
    st.success(f"✅ Confirmação registrada! ID: {confirmation_id}")
    
    # Navigation buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("← Voltar e Corrigir Dados", type="secondary"):
            st.session_state.show_payment = False
            st.rerun()
    
    with col2:
        if st.button("Nova Confirmação", type="primary"):
            st.session_state.confirmed = False
            st.session_state.participant_data = None
            st.session_state.show_payment = False
            st.session_state.guest_counts = None
            st.session_state.total_amount = 0
            st.rerun()


def main():
    """Main application flow."""
    # Custom CSS for better title display - smaller font to prevent line wrapping
    st.markdown("""
    <style>
    .event-title {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: rgb(9, 171, 59) !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.2 !important;
    }
    @media (max-width: 768px) {
        .event-title {
            font-size: 1.5rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display title with custom styling to prevent line wrapping
    st.markdown(f'<h1 class="event-title">🎉 {EVENT_NAME}</h1>', unsafe_allow_html=True)
    
    st.markdown(f"📅 **Data:** {EVENT_DATE}")
    st.markdown(f"📍 **Local:** {EVENT_LOCATION}")
    st.markdown("---")
    
    # Load participants
    # st.info("Sistema iniciado...")
    participants_df = load_participants()
    
    if participants_df.empty:
        st.error("Lista de participantes vazia ou não carregada")
        return
    
    # st.success(f"Total de participantes carregados: {len(participants_df)}")
    
    # Check which page to show
    if st.session_state.show_payment:
        show_payment_page()
    elif not st.session_state.confirmed:
        # Step 1: Name verification
        st.markdown("### 👤 Verificação de Convidado")
        
        name_input = st.text_input("Digite seu nome completo e acione o botão 'Verificar':", 
                                   placeholder="Ex: João da Silva")
        
        if st.button("Verificar"):
            if name_input:
                participant = find_participant(name_input, participants_df)
                
                if participant is not None:
                    st.session_state.participant_data = participant
                    st.success(f"✅ Olá, {participant['full_name']}!")
                    st.session_state.confirmed = True
                    st.rerun()
                else:
                    st.error(MESSAGES['not_found'])
            else:
                st.warning("Por favor, digite seu nome.")
    else:
        # Step 2: Guest information form
        show_guest_form()

def admin_panel():
    """Admin panel for viewing confirmations."""
    st.title("🔐 Painel Administrativo")
    
    password = st.text_input("Senha:", type="password")
    
    if password == ADMIN_PASSWORD:
        st.success("Acesso autorizado!")
        
        # Load confirmations
        try:
            df = pd.read_csv('./data/confirmations.csv')
            
            # Statistics
            st.markdown("### 📊 Estatísticas")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Confirmações", len(df))
            
            with col2:
                total_guests = df['guests_under_5'].sum() + df['guests_5_to_12'].sum() + df['guests_above_12'].sum()
                st.metric("Total de Pessoas", total_guests)
            
            with col3:
                total_revenue = df['total_amount'].sum()
                st.metric("Valor Total", f"R\\$ {total_revenue:.2f}")
            
            with col4:
                avg_amount = df['total_amount'].mean()
                st.metric("Ticket Médio", f"R\\$ {avg_amount:.2f}")
            
            # Confirmations table
            st.markdown("### 📋 Lista de Confirmações")
            st.dataframe(df.sort_values('timestamp', ascending=False))
            
            # Export option
            if FEATURES['export_data']:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Baixar CSV",
                    data=csv,
                    file_name=f"confirmacoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        except FileNotFoundError:
            st.info("Nenhuma confirmação registrada ainda.")
    
    elif password:
        st.error("Senha incorreta!")

# Run the app
if __name__ == "__main__":
    # Check if admin mode
    query_params = st.query_params
    
    if 'admin' in query_params:
        admin_panel()
    else:
        main()