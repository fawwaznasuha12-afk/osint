import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import aiohttp
import re
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
                'raw_phone': phone,
                'formatted': None,
                'valid': False,
                'country': None,
                'country_code': None,
                'national_number': None,
                'carrier': None,
                'carrier_type': None,
                'timezone': None,
                'location': None,
                'location_lat': None,
                'location_lng': None,
                'whatsapp': False,
                'telegram': False,
                'signal': False,
                'line': False,
                'viber': False,
                'risk_score': 0,
                'risk_level': 'low',
                'spam_likelihood': 0
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
        data['formatted'] = parsed['formatted']
        data['country'] = parsed['country']
        data['country_code'] = parsed['country_code']
        data['national_number'] = parsed['national_number']
        data['carrier'] = parsed['carrier']
        data['carrier_type'] = await self._get_carrier_type(parsed['carrier'])
        data['timezone'] = parsed['timezone']
        data['location'] = parsed['location']
        data['location_lat'], data['location_lng'] = await self._get_location_coords(parsed['location'])
        
        data['whatsapp'] = await self._check_whatsapp(phone)
        data['telegram'] = await self._check_telegram(phone)
        data['signal'] = await self._check_signal(phone)
        data['line'] = await self._check_line(phone)
        data['viber'] = await self._check_viber(phone)
        
        data['spam_likelihood'] = await self._check_spam(phone)
        data['risk_score'] = self._calculate_risk(data)
        data['risk_level'] = self._get_risk_level(data['risk_score'])
        
        return results
        
    async def _parse_phone(self, phone):
        try:
            parsed = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed):
                return None
                
            return {
                'formatted': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
                'country': phonenumbers.region_code_for_number(parsed),
                'country_code': parsed.country_code,
                'national_number': parsed.national_number,
                'carrier': carrier.name_for_number(parsed, 'en'),
                'timezone': timezone.time_zones_for_number(parsed),
                'location': geocoder.description_for_number(parsed, 'en')
            }
        except:
            return None
            
    async def _get_carrier_type(self, carrier_name):
        if not carrier_name:
            return None
        carrier_lower = carrier_name.lower()
        if 'mobile' in carrier_lower or 'cell' in carrier_lower:
            return 'mobile'
        elif 'landline' in carrier_lower or 'fixed' in carrier_lower:
            return 'landline'
        elif 'voip' in carrier_lower or 'virtual' in carrier_lower:
            return 'voip'
        else:
            return 'unknown'
            
    async def _get_location_coords(self, location):
        if not location:
            return None, None
        try:
            # Simple location to coordinates mapping (mock)
            location_map = {
                'Jakarta': (-6.2088, 106.8456),
                'Bandung': (-6.9175, 107.6191),
                'Surabaya': (-7.2575, 112.7521),
                'Yogyakarta': (-7.7956, 110.3695),
                'Bali': (-8.3405, 115.0920),
                'Medan': (3.5952, 98.6722),
                'Makassar': (-5.1477, 119.4327),
                'Semarang': (-6.9667, 110.4167),
                'Palembang': (-2.9761, 104.7754),
                'Padang': (-0.9471, 100.4172)
            }
            for key, coords in location_map.items():
                if key.lower() in location.lower():
                    return coords
        except:
            pass
        return None, None
        
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
            
    async def _check_line(self, phone):
        try:
            async with self.session.get(
                f"https://api.line.me/v2/phone/{phone}",
                headers={'Authorization': 'Bearer dummy'}
            ) as resp:
                return resp.status == 200
        except:
            return False
            
    async def _check_viber(self, phone):
        try:
            async with self.session.get(
                f"https://www.viber.com/phone/{phone}"
            ) as resp:
                return resp.status == 200
        except:
            return False
            
    async def _check_spam(self, phone):
        try:
            # Mock spam detection
            spam_keywords = ['scam', 'fraud', 'spam', 'phishing', 'fake']
            score = 0
            for keyword in spam_keywords:
                if keyword in phone.lower():
                    score += 20
            return min(100, score)
        except:
            return 0
            
    def _calculate_risk(self, data):
        risk = 0
        if not data.get('valid'):
            risk += 30
        if data.get('carrier_type') in ['voip', 'virtual']:
            risk += 20
        if data.get('spam_likelihood', 0) > 50:
            risk += 25
        if data.get('whatsapp') or data.get('telegram') or data.get('signal'):
            risk += 10
        return min(100, risk)
        
    def _get_risk_level(self, score):
        if score >= 70:
            return 'critical'
        elif score >= 50:
            return 'high'
        elif score >= 30:
            return 'medium'
        elif score >= 10:
            return 'low'
        else:
            return 'safe'
