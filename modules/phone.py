import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import aiohttp
from typing import Dict
from datetime import datetime
from modules.base import BaseModule

class PhoneOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        
    async def scan(self, phone: str) -> Dict:
        results = {
            'target': phone,
            'module': 'phone',
            'status': 'success',
            'data': {
                'phone': phone,
                'valid': False,
                'country': None,
                'carrier': None,
                'timezone': None,
                'location': None,
                'whatsapp': False,
                'telegram': False,
                'signal': False,
                'risk_score': 0
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        parsed = await self._parse_phone(phone)
        if not parsed:
            results['status'] = 'error'
            results['data']['error'] = 'Invalid phone number'
            return results
            
        data = results['data']
        data['valid'] = True
        data['country'] = parsed['country']
        data['carrier'] = parsed['carrier']
        data['timezone'] = parsed['timezone']
        data['location'] = parsed['location']
        
        data['whatsapp'] = await self._check_whatsapp(phone)
        data['telegram'] = await self._check_telegram(phone)
        data['signal'] = await self._check_signal(phone)
        
        return results
        
    async def _parse_phone(self, phone):
        try:
            parsed = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed):
                return None
                
            return {
                'country': phonenumbers.region_code_for_number(parsed),
                'carrier': carrier.name_for_number(parsed, 'en'),
                'timezone': timezone.time_zones_for_number(parsed),
                'location': geocoder.description_for_number(parsed, 'en')
            }
        except:
            return None
            
    async def _check_whatsapp(self, phone):
        try:
            async with self.session.get(
                f"https://api.whatsapp.com/v1/phone/{phone}",
                headers={'User-Agent': 'WhatsApp/2.23.2.74'}
            ) as resp:
                return resp.status == 200
        except:
            return False
            
    async def _check_telegram(self, phone):
        try:
            async with self.session.post(
                "https://web.telegram.org/auth/sms",
                json={'phone_number': phone}
            ) as resp:
                return resp.status == 200
        except:
            return False
            
    async def _check_signal(self, phone):
        try:
            async with self.session.get(
                f"https://api.signal.org/v1/accounts/contact/{phone}"
            ) as resp:
                return resp.status == 200
        except:
            return False
