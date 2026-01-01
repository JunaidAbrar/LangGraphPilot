import re

def obfuscate_pii(text: str) -> str:
    """
    Scans the text for emails and phone numbers and replaces them with [REDACTED].
    """
    if not text:
        return ""
    
    # 1. Email Regex (Basic)
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    text = re.sub(email_pattern, "[EMAIL REDACTED]", text)
    
    # 2. Phone Number Regex (Matches formats like 123-456-7890, (123) 456-7890)
    phone_pattern = r'\b(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})\b'
    text = re.sub(phone_pattern, "[PHONE REDACTED]", text)
    
    return text