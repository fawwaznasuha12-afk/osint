import re

class Validator:
    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
        
    def validate_username(self, username):
        pattern = r'^[a-zA-Z0-9_.-]{3,30}$'
        return bool(re.match(pattern, username))
        
    def validate_domain(self, domain):
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))
        
    def validate_phone(self, phone):
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        return len(phone) >= 10 and len(phone) <= 15 and phone.isdigit()
        
    def validate_crypto(self, address):
        if len(address) >= 26 and len(address) <= 34 and address[0] in ['1', '3']:
            return True
        if address.startswith('0x') and len(address) == 42:
            return True
        return False
