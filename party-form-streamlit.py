import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import base64

# Configure the page
st.set_page_config(
    page_title="Confirmação de Presença - Festa",
    page_icon="🎉",
    layout="centered"
)

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 'name_input'
if 'participant_name' not in st.session_state:
    st.session_state.participant_name = ''
if 'will_attend' not in st.session_state:
    st.session_state.will_attend = None

# Sample participants data (replace with your actual data source)
# In production, this would come from a database or CSV file
PARTICIPANTS = {
    "João Silva": {"age": 35, "id": 1},
    "Maria Santos": {"age": 28, "id": 2},
    "Pedro Oliveira": {"age": 42, "id": 3},
}

# Pricing configuration (in R$)
PRICING = {
    "under_5": 0,      # Free for kids under 5
    "5_to_12": 25,     # Half price for kids 5-12
    "above_12": 50     # Full price for adults and teens
}

def generate_pix_qr_code(amount, pix_key="seu_pix_aqui@email.com"):
    """
    Generate a QR code for PIX payment
    In production, use proper PIX payload generation
    """
    # This is a simplified example - use a proper PIX library in production
    pix_payload = f"PIX_KEY:{pix_key}|AMOUNT:{amount}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(pix_payload)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes for display
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    return buf

def calculate_total_cost(guests_data):
    """
    Calculate total cost based on guest age groups
    """
    total = 0
    total += guests_data['under_5'] * PRICING['under_5']
    total += guests_data['5_to_12'] * PRICING['5_to_12']
    total += guests_data['above_12'] * PRICING['above_12']
    
    # Add the participant's own cost (assuming they're above 12)
    total += PRICING['above_12']
    
    return total

# Main app logic
st.title("🎉 Confirmação de Presença - Festa")

# Step 1: Name input
if st.session_state.step == 'name_input':
    st.write("Por favor, informe seu nome completo:")
    
    name_input = st.text_input("Nome completo:", key="name_field")
    
    if st.button("Próximo", type="primary"):
        if name_input.strip():
            # Check if participant is in the list
            if name_input in PARTICIPANTS:
                st.session_state.participant_name = name_input
                st.session_state.step = 'attendance_confirmation'
                st.rerun()
            else:
                st.error("Nome não encontrado na lista de participantes. Verifique se digitou corretamente.")
        else:
            st.warning("Por favor, digite seu nome completo.")

# Step 2: Attendance confirmation
elif st.session_state.step == 'attendance_confirmation':
    st.write(f"Olá, **{st.session_state.participant_name}**!")
    st.write("Você irá participar da festa?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Sim, irei participar", type="primary", use_container_width=True):
            st.session_state.will_attend = True
            st.session_state.step = 'guest_form'
            st.rerun()
    
    with col2:
        if st.button("❌ Não poderei ir", use_container_width=True):
            st.session_state.will_attend = False
            st.session_state.step = 'thank_you'
            st.rerun()

# Step 3: Guest form (if attending)
elif st.session_state.step == 'guest_form':
    st.write(f"**{st.session_state.participant_name}**, informe quantos convidados você levará:")
    
    # Create the form
    with st.form("guest_form"):
        st.subheader("Quantidade de convidados por faixa etária:")
        
        # Age group inputs
        under_5 = st.number_input(
            "👶 Abaixo de 5 anos (entrada gratuita)",
            min_value=0,
            max_value=10,
            value=0,
            step=1
        )
        
        age_5_to_12 = st.number_input(
            "🧒 Entre 5 e 12 anos (R$ 25,00 por pessoa)",
            min_value=0,
            max_value=10,
            value=0,
            step=1
        )
        
        above_12 = st.number_input(
            "👨 Acima de 12 anos (R$ 50,00 por pessoa)",
            min_value=0,
            max_value=10,
            value=0,
            step=1
        )
        
        # Submit button
        submitted = st.form_submit_button("Calcular valor total", type="primary")
        
        if submitted:
            # Store guest data
            st.session_state.guest_data = {
                'under_5': under_5,
                '5_to_12': age_5_to_12,
                'above_12': above_12
            }
            st.session_state.step = 'payment'
            st.rerun()

# Step 4: Payment (show total and QR code)
elif st.session_state.step == 'payment':
    st.subheader("Resumo da sua confirmação")
    
    # Display summary
    guest_data = st.session_state.guest_data
    total_guests = sum(guest_data.values())
    
    # Create summary dataframe
    summary_data = []
    
    # Add participant
    summary_data.append({
        "Categoria": f"Participante ({st.session_state.participant_name})",
        "Quantidade": 1,
        "Valor unitário": f"R$ {PRICING['above_12']:.2f}",
        "Subtotal": f"R$ {PRICING['above_12']:.2f}"
    })
    
    # Add guests by category
    if guest_data['under_5'] > 0:
        summary_data.append({
            "Categoria": "Convidados abaixo de 5 anos",
            "Quantidade": guest_data['under_5'],
            "Valor unitário": "Gratuito",
            "Subtotal": "R$ 0,00"
        })
    
    if guest_data['5_to_12'] > 0:
        subtotal = guest_data['5_to_12'] * PRICING['5_to_12']
        summary_data.append({
            "Categoria": "Convidados entre 5 e 12 anos",
            "Quantidade": guest_data['5_to_12'],
            "Valor unitário": f"R$ {PRICING['5_to_12']:.2f}",
            "Subtotal": f"R$ {subtotal:.2f}"
        })
    
    if guest_data['above_12'] > 0:
        subtotal = guest_data['above_12'] * PRICING['above_12']
        summary_data.append({
            "Categoria": "Convidados acima de 12 anos",
            "Quantidade": guest_data['above_12'],
            "Valor unitário": f"R$ {PRICING['above_12']:.2f}",
            "Subtotal": f"R$ {subtotal:.2f}"
        })
    
    # Display summary table
    df_summary = pd.DataFrame(summary_data)
    st.table(df_summary)
    
    # Calculate and display total
    total_cost = calculate_total_cost(guest_data)
    st.success(f"**Valor total a pagar: R$ {total_cost:.2f}**")
    
    # Generate and display QR code
    st.subheader("QR Code para pagamento via PIX")
    
    # Generate QR code
    qr_buffer = generate_pix_qr_code(total_cost)
    
    # Display QR code
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(qr_buffer, caption=f"Valor: R$ {total_cost:.2f}")
    
    # Instructions
    st.info("""
    **Instruções para pagamento:**
    1. Abra o aplicativo do seu banco
    2. Acesse a opção PIX
    3. Escaneie o QR Code acima
    4. Confirme o pagamento
    
    Após o pagamento, você receberá um e-mail de confirmação.
    """)
    
    # Option to start over
    if st.button("Fazer nova confirmação"):
        # Reset session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Step 5: Thank you (if not attending)
elif st.session_state.step == 'thank_you':
    st.balloons()
    st.success("Obrigado por nos avisar!")
    st.write("Sentiremos sua falta na festa. Esperamos vê-lo em uma próxima oportunidade!")
    
    if st.button("Voltar ao início"):
        # Reset session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Add footer with contact info
st.markdown("---")
st.markdown("Em caso de dúvidas, entre em contato: festa@exemplo.com")
