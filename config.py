"""
Configuration file for the party registration system.
This centralizes all settings that might need to be changed without modifying the main code.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file (for sensitive data)
load_dotenv()

# Event Information
EVENT_NAME = "T90 - 35 Anos - Almoço Comemorativo"
EVENT_DATE = "29 de novembro de 2025 13:00"
EVENT_LOCATION = "Churrascaria Boigalê São José dos Campos"

# Pricing Configuration (in Brazilian Reais)
# These values determine how much each age group pays
PRICING = {
    "under_5": 0,      # Kids under 5 enter for free
    "5_to_12": 37.50,  # Children between 5-12 pay half price
    "above_12": 75.00  # Adults and teens pay full price
}

# PIX Payment Configuration
# IMPORTANT: Never commit your actual PIX key to GitHub!
# Use environment variables for production
PIX_KEY = os.getenv("PIX_KEY", "toni@ita90.com.br")  # Your PIX key
PIX_MERCHANT_NAME = os.getenv("PIX_MERCHANT_NAME", "Antônio Magno Lima Espeschit")
PIX_CITY = os.getenv("PIX_CITY", "São José dos Campos-SP")

# Email Configuration (for sending confirmations)
# These should also come from environment variables in production
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "toni@ita90.com.br")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")  # Keep empty if not using email

# Data Source Configuration
# Path to the CSV file containing participant information
PARTICIPANTS_FILE = "participants.csv"

# User Interface Messages
# Customize these messages to match your event's tone
MESSAGES = {
    "welcome": f"Bem-vindo ao sistema de confirmação para {EVENT_NAME}!",
    "not_found": "Nome não encontrado na lista. Verifique se digitou corretamente ou entre em contato com a organização.",
    "thank_you_not_attending": "Obrigado por nos avisar! Sentiremos sua falta.",
    "payment_instructions": """
    **Instruções para pagamento:**
    1. Abra o aplicativo do seu banco
    2. Acesse a opção PIX
    3. Escaneie o QR Code acima
    4. Confirme o pagamento
    
    IMPORTANTE: Não precisa mandar o comprovante via whatsapp!
    """,
    "confirmation_email_subject": f"Confirmação de presença - {EVENT_NAME}"
}

# Guest Limits
# Maximum number of guests allowed per age category
MAX_GUESTS_PER_CATEGORY = 100

# Application Settings
# Page configuration for Streamlit
PAGE_CONFIG = {
    "page_title": f"Confirmação - {EVENT_NAME}",
    "page_icon": "🎉",
    "layout": "centered",
    "initial_sidebar_state": "collapsed"
}

# Admin Configuration
# Password for accessing the admin dashboard
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Change this!

# Feature Flags
# Enable or disable features during development
FEATURES = {
    "send_emails": False,  # Set to True when email is configured
    "validate_payment": False,  # Set to True when payment API is integrated
    "admin_dashboard": True,  # Enable admin view
    "export_data": True  # Allow data export to CSV
}