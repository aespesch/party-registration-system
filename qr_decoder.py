import streamlit as st
from pyzbar.pyzbar import decode
from PIL import Image
import io

def decode_qr_code(uploaded_file):
    """Decodifica o conteúdo de uma imagem de QR Code"""
    try:
        # Carrega a imagem
        image = Image.open(io.BytesIO(uploaded_file.read()))
        
        # Decodifica o QR Code
        decoded_objects = decode(image)
        
        if decoded_objects:
            return decoded_objects[0].data.decode('utf-8')
        else:
            return "Nenhum QR Code encontrado na imagem."
    except Exception as e:
        return f"Erro ao decodificar: {str(e)}"

# Interface Streamlit
st.title("🔍 Decodificador de QR Code PIX")

uploaded_file = st.file_uploader(
    "Carregue uma imagem contendo QR Code PIX", 
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    # Exibe a imagem carregada
    st.image(uploaded_file, caption="QR Code Carregado", width=300)
    
    # Decodifica o QR Code
    decoded_text = decode_qr_code(uploaded_file)
    
    st.subheader("Conteúdo Decodificado:")
    st.code(decoded_text, language="text")
    
    st.subheader("Análise do QR Code:")
    
    # Verifica se é um QR Code PIX válido
    if decoded_text.startswith("000201"):
        st.success("✅ Estrutura básica de QR Code PIX válida detectada")
        
        # Análise dos campos
        if "br.gov.bcb.pix" in decoded_text:
            st.success("✅ Identificador PIX correto (br.gov.bcb.pix)")
        else:
            st.error("❌ Identificador PIX não encontrado")
        
        if "54" in decoded_text:  # Campo de valor
            st.success("✅ Campo de valor monetário presente")
        else:
            st.warning("⚠️ Campo de valor monetário ausente")
        
        if "6304" in decoded_text:  # Campo CRC
            st.success("✅ Campo CRC presente")
        else:
            st.error("❌ Campo CRC ausente")
    else:
        st.error("❌ Não parece ser um QR Code PIX válido")