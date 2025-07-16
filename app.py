"""
Main Streamlit application for party registration and payment.
This file orchestrates the entire user flow from name verification to payment.
"""

import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import os
from datetime import datetime
import hashlib

# Import our configuration settings
from config import (
    PRICING, PIX_KEY, PIX_MERCHANT_NAME, PIX_CITY,
    PARTICIPANTS_FILE, MESSAGES, MAX_GUESTS_PER_CATEGORY,
    PAGE_CONFIG, EVENT_NAME, EVENT_DATE, EVENT_LOCATION,
    FEATURES
)

# Configure the Streamlit page using our centralized settings
st.set_page_config(**PAGE_CONFIG)

# Initialize session state variables
# Session state allows us to maintain data between page reloads
def initialize_session_state():
    """
    Initialize all session state variables if they don't exist.
    This prevents errors and ensures clean state management.
    """
    defaults = {
        'step': 'name_input',
        'participant_name': '',
        'participant_data': None,
        'will_attend': None,
        'guest_data': None,
        'confirmation_id': None
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Load participants from CSV file
@st.cache_data  # This decorator caches the data to improve performance
def load_participants():
    """
    Load participant data from CSV file.
    Returns a DataFrame with participant information.
    """
    try:
        # Check if file exists
        if not os.path.exists(PARTICIPANTS_FILE):
            st.error(f"Arquivo de participantes não encontrado: {PARTICIPANTS_FILE}")
            return pd.DataFrame()
        
        # Read CSV with proper encoding for Portuguese characters
        df = pd.read_csv(PARTICIPANTS_FILE, encoding='utf-8')
        
        # Validate required columns
        required_columns = ['full_name', 'age', 'email', 'participant_id']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Colunas faltando no CSV: {missing_columns}")
            return pd.DataFrame()
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar participantes: {str(e)}")
        return pd.DataFrame()

def generate_pix_payload(amount, participant_name, confirmation_id):
    """
    Generate a PIX payment payload following the Brazilian Central Bank standard.
    This creates the actual data that goes into the QR code.
    
    Note: This is a simplified version. For production, use a proper PIX library
    like python-pix or pixqrcodegen.
    """
    # Basic PIX payload structure (simplified for demonstration)
    payload_parts = [
        "00020126",  # Payload Format Indicator
        f"0014BR.GOV.BCB.PIX",  # GUI
        f"01{len(PIX_KEY):02d}{PIX_KEY}",  # PIX Key
        f"52040000",  # Merchant Category Code
        f"5303986",  # Transaction Currency (986 = BRL)
        f"54{len(f'{amount:.2f}'):02d}{amount:.2f}",  # Transaction Amount
        f"5802BR",  # Country Code
        f"59{len(PIX_MERCHANT_NAME):02d}{PIX_MERCHANT_NAME}",  # Merchant Name
        f"60{len(PIX_CITY):02d}{PIX_CITY}",  # Merchant City
        f"62{len(confirmation_id)+4:02d}05{len(confirmation_id):02d}{confirmation_id}"  # Additional Data
    ]
    
    # Join all parts
    payload = "".join(payload_parts)
    
    # Calculate CRC16 checksum (simplified - use proper implementation in production)
    # For now, we'll use a placeholder
    payload += "6304"  # CRC placeholder
    
    return payload

def generate_qr_code(amount, participant_name):
    """
    Generate a QR code image for PIX payment.
    Returns a BytesIO object containing the QR code image.
    """
    # Generate a unique confirmation ID
    confirmation_id = hashlib.md5(
        f"{participant_name}{datetime.now().isoformat()}".encode()
    ).hexdigest()[:8].upper()
    
    # Store confirmation ID in session state for later use
    st.session_state.confirmation_id = confirmation_id
    
    # Generate PIX payload
    pix_payload = generate_pix_payload(amount, participant_name, confirmation_id)
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR code
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(pix_payload)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes for display in Streamlit
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    return buf, confirmation_id

def calculate_total_cost(guest_data, include_participant=True):
    """
    Calculate the total cost based on guest ages and the participant.
    
    Args:
        guest_data: Dictionary with keys 'under_5', '5_to_12', 'above_12'
        include_participant: Whether to include the participant's own cost
    
    Returns:
        Total cost in Brazilian Reais
    """
    total = 0
    
    # Calculate cost for each age group
    total += guest_data.get('under_5', 0) * PRICING['under_5']
    total += guest_data.get('5_to_12', 0) * PRICING['5_to_12']
    total += guest_data.get('above_12', 0) * PRICING['above_12']
    
    # Add participant's cost (assuming they're above 12)
    if include_participant:
        total += PRICING['above_12']
    
    return total

def save_confirmation(participant_data, guest_data, confirmation_id):
    """
    Save confirmation data to a CSV file for record keeping.
    In production, this would save to a database.
    """
    # Create confirmations directory if it doesn't exist
    os.makedirs('data/confirmations', exist_ok=True)
    
    # Prepare confirmation data
    confirmation_data = {
        'confirmation_id': confirmation_id,
        'timestamp': datetime.now().isoformat(),
        'participant_name': participant_data['full_name'],
        'participant_id': participant_data['participant_id'],
        'participant_email': participant_data['email'],
        'guests_under_5': guest_data['under_5'],
        'guests_5_to_12': guest_data['5_to_12'],
        'guests_above_12': guest_data['above_12'],
        'total_amount': calculate_total_cost(guest_data),
        'payment_status': 'pending'
    }
    
    # Convert to DataFrame
    df_confirmation = pd.DataFrame([confirmation_data])
    
    # Append to confirmations file
    confirmations_file = 'data/confirmations/confirmations.csv'
    
    if os.path.exists(confirmations_file):
        # Append to existing file
        df_confirmation.to_csv(confirmations_file, mode='a', header=False, index=False)
    else:
        # Create new file with headers
        df_confirmation.to_csv(confirmations_file, index=False)

# Main application flow
def main():
    """
    Main application logic that controls the user flow.
    """
    # Initialize session state
    initialize_session_state()
    
    # Load participants data
    participants_df = load_participants()
    
    if participants_df.empty:
        st.error("Não foi possível carregar a lista de participantes. Entre em contato com a organização.")
        return
    
    # Display header
    st.title(f"🎉 {EVENT_NAME}")
    st.markdown(f"📅 **Data:** {EVENT_DATE} | 📍 **Local:** {EVENT_LOCATION}")
    st.markdown("---")
    
    # Step 1: Name Input
    if st.session_state.step == 'name_input':
        st.write(MESSAGES['welcome'])
        st.write("Por favor, informe seu nome completo exatamente como consta na lista:")
        
        # Create name input with autocomplete hint
        name_input = st.text_input(
            "Nome completo:",
            key="name_field",
            placeholder="Digite seu nome completo..."
        )
        
        # Add a helper to show similar names if input is provided
        if name_input and len(name_input) >= 3:
            # Find similar names in the list
            similar_names = participants_df[
                participants_df['full_name'].str.contains(name_input, case=False, na=False)
            ]['full_name'].tolist()
            
            if similar_names and name_input not in similar_names:
                st.info(f"💡 Nomes similares encontrados: {', '.join(similar_names[:3])}")
        
        # Submit button
        if st.button("Próximo", type="primary", use_container_width=True):
            if name_input.strip():
                # Check if participant exists (case-sensitive)
                participant_match = participants_df[
                    participants_df['full_name'] == name_input.strip()
                ]
                
                if not participant_match.empty:
                    # Store participant data
                    st.session_state.participant_name = name_input.strip()
                    st.session_state.participant_data = participant_match.iloc[0].to_dict()
                    st.session_state.step = 'attendance_confirmation'
                    st.rerun()
                else:
                    st.error(MESSAGES['not_found'])
            else:
                st.warning("Por favor, digite seu nome completo.")
    
    # Step 2: Attendance Confirmation
    elif st.session_state.step == 'attendance_confirmation':
        st.write(f"Olá, **{st.session_state.participant_name}**! 👋")
        st.write("Ficamos felizes em tê-lo(a) em nossa lista!")
        st.write("")
        st.write("Você poderá comparecer ao evento?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Sim, confirmo presença", type="primary", use_container_width=True):
                st.session_state.will_attend = True
                st.session_state.step = 'guest_form'
                st.rerun()
        
        with col2:
            if st.button("❌ Não poderei comparecer", use_container_width=True):
                st.session_state.will_attend = False
                st.session_state.step = 'thank_you'
                st.rerun()
    
    # Step 3: Guest Form
    elif st.session_state.step == 'guest_form':
        st.write(f"**{st.session_state.participant_name}**, agora precisamos saber sobre seus convidados.")
        st.info("💡 Lembre-se: crianças abaixo de 5 anos não pagam!")
        
        with st.form("guest_form"):
            st.subheader("Quantos convidados você levará em cada faixa etária?")
            
            # Create three columns for the inputs
            col1, col2, col3 = st.columns(3)
            
            with col1:
                under_5 = st.number_input(
                    "👶 Abaixo de 5 anos",
                    min_value=0,
                    max_value=MAX_GUESTS_PER_CATEGORY,
                    value=0,
                    step=1,
                    help="Entrada gratuita"
                )
            
            with col2:
                age_5_to_12 = st.number_input(
                    "🧒 Entre 5 e 12 anos",
                    min_value=0,
                    max_value=MAX_GUESTS_PER_CATEGORY,
                    value=0,
                    step=1,
                    help=f"R$ {PRICING['5_to_12']:.2f} por criança"
                )
            
            with col3:
                above_12 = st.number_input(
                    "👨 Acima de 12 anos",
                    min_value=0,
                    max_value=MAX_GUESTS_PER_CATEGORY,
                    value=0,
                    step=1,
                    help=f"R$ {PRICING['above_12']:.2f} por pessoa"
                )
            
            # Show live cost calculation
            guest_data_preview = {
                'under_5': under_5,
                '5_to_12': age_5_to_12,
                'above_12': above_12
            }
            
            preview_cost = calculate_total_cost(guest_data_preview)
            st.metric("Valor total estimado:", f"R$ {preview_cost:.2f}")
            
            # Submit button
            submitted = st.form_submit_button(
                "Confirmar e gerar pagamento",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                st.session_state.guest_data = guest_data_preview
                st.session_state.step = 'payment'
                st.rerun()
    
    # Step 4: Payment
    elif st.session_state.step == 'payment':
        st.subheader("📋 Resumo da sua confirmação")
        
        # Create summary
        guest_data = st.session_state.guest_data
        total_guests = sum(guest_data.values())
        total_people = total_guests + 1  # Including the participant
        
        # Display participant info
        st.write(f"**Participante:** {st.session_state.participant_name}")
        st.write(f"**Total de pessoas:** {total_people} (você + {total_guests} convidado(s))")
        
        # Create detailed breakdown
        st.subheader("💰 Detalhamento dos valores:")
        
        # Use columns for better layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"Você (participante)")
            if guest_data['under_5'] > 0:
                st.write(f"{guest_data['under_5']} convidado(s) abaixo de 5 anos")
            if guest_data['5_to_12'] > 0:
                st.write(f"{guest_data['5_to_12']} convidado(s) entre 5-12 anos")
            if guest_data['above_12'] > 0:
                st.write(f"{guest_data['above_12']} convidado(s) acima de 12 anos")
        
        with col2:
            st.write(f"R$ {PRICING['above_12']:.2f}")
            if guest_data['under_5'] > 0:
                st.write("Gratuito")
            if guest_data['5_to_12'] > 0:
                st.write(f"R$ {guest_data['5_to_12'] * PRICING['5_to_12']:.2f}")
            if guest_data['above_12'] > 0:
                st.write(f"R$ {guest_data['above_12'] * PRICING['above_12']:.2f}")
        
        # Calculate and display total
        total_cost = calculate_total_cost(guest_data)
        st.markdown("---")
        st.success(f"### Total a pagar: R$ {total_cost:.2f}")
        
        # Generate and display QR code
        if total_cost > 0:
            st.subheader("📱 QR Code para pagamento PIX")
            
            # Generate QR code
            qr_buffer, confirmation_id = generate_qr_code(
                total_cost,
                st.session_state.participant_name
            )
            
            # Display QR code centered
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(qr_buffer, caption=f"Valor: R$ {total_cost:.2f}")
                st.info(f"**Código de confirmação:** {confirmation_id}")
            
            # Payment instructions
            st.markdown(MESSAGES['payment_instructions'])
            
            # Save confirmation
            save_confirmation(
                st.session_state.participant_data,
                guest_data,
                confirmation_id
            )
            
            # Success message
            st.success(f"✅ Confirmação registrada! Código: {confirmation_id}")
            
            # Option to start over
            if st.button("Fazer nova confirmação", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        else:
            # No payment needed (only free guests)
            st.info("Não há valor a pagar - todos os seus convidados têm entrada gratuita!")
            confirmation_id = hashlib.md5(
                f"{st.session_state.participant_name}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:8].upper()
            
            save_confirmation(
                st.session_state.participant_data,
                guest_data,
                confirmation_id
            )
            
            st.success(f"✅ Confirmação registrada! Código: {confirmation_id}")
            
            if st.button("Fazer nova confirmação", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    # Step 5: Thank you (not attending)
    elif st.session_state.step == 'thank_you':
        st.balloons()
        st.info(MESSAGES['thank_you_not_attending'])
        st.write(f"Caso mude de ideia, você pode confirmar sua presença até 48 horas antes do evento.")
        
        if st.button("Voltar ao início", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Add admin section (if enabled in config)
def admin_section():
    """
    Admin dashboard to view confirmations and statistics.
    This is a simple implementation - enhance with authentication in production.
    """
    if FEATURES.get('admin_dashboard', False):
        # Check if user pressed a secret key combination (for demo purposes)
        if st.sidebar.button("🔐 Admin", key="admin_button"):
            password = st.sidebar.text_input("Senha:", type="password")
            
            if password == ADMIN_PASSWORD:
                st.sidebar.success("Acesso autorizado!")
                
                # Show admin options
                if st.sidebar.button("Ver confirmações"):
                    confirmations_file = 'data/confirmations/confirmations.csv'
                    if os.path.exists(confirmations_file):
                        df = pd.read_csv(confirmations_file)
                        st.write("### Confirmações Registradas")
                        st.dataframe(df)
                        
                        # Show statistics
                        st.write("### Estatísticas")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total confirmações", len(df))
                        with col2:
                            total_amount = df['total_amount'].sum()
                            st.metric("Valor total", f"R$ {total_amount:.2f}")
                        with col3:
                            total_people = len(df) + df[['guests_under_5', 'guests_5_to_12', 'guests_above_12']].sum().sum()
                            st.metric("Total de pessoas", int(total_people))
                    else:
                        st.info("Ainda não há confirmações registradas.")

# Run the application
if __name__ == "__main__":
    # Add admin section to sidebar
    admin_section()
    
    # Run main application
    main()
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"Em caso de dúvidas, entre em contato: {st.session_state.get('EMAIL_SENDER', 'festa@exemplo.com')}"
    )