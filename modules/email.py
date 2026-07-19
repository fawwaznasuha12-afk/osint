import hashlib
import re
import aiohttp
import asyncio
from typing import Dict, List
from modules.base import BaseModule

class EmailOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        
    async def scan(self, email: str) -> Dict:
        results = {
            'email': email,
            'valid': False,
            'domain': '',
            'breaches': [],
            'disposable': False,
            'gravatar': None,
            'social_accounts': [],
            'risk_score': 0
        }
        
        if not self._validate_email(email):
            results['error'] = 'Invalid email format'
            return results
            
        results['domain'] = email.split('@')[1]
        results['valid'] = await self._verify_email(email)
        results['breaches'] = await self._check_breaches(email)
        results['disposable'] = await self._is_disposable(email)
        results['gravatar'] = await self._get_gravatar(email)
        results['social_accounts'] = await self._find_social(email)
        results['risk_score'] = self._calculate_risk(results)
        
        return results
        
    def _validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
        
    async def _verify_email(self, email):
        try:
            async with self.session.get(
                f"https://api.email-validator.net/api/verify?EmailAddress={email}",
                timeout=10
            ) as resp:
                data = await resp.json()
                return data.get('IsValid', False)
        except:
            return False
            
    async def _check_breaches(self, email):
        try:
            async with self.session.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    return []
        except:
            return []
            
    async def _is_disposable(self, email):
        domain = email.split('@')[1]
        try:
            async with self.session.get(
                f"https://api.disposable.email/disposable?domain={domain}"
            ) as resp:
                data = await resp.json()
                return data.get('disposable', False)
        except:
            return False
            
    async def _get_gravatar(self, email):
        hash_md5 = hashlib.md5(email.lower().encode()).hexdigest()
        url = f"https://www.gravatar.com/avatar/{hash_md5}?d=404&size=200"
        try:
            async with self.session.head(url) as resp:
                if resp.status == 200:
                    return url
        except:
            pass
        return None
        
    async def _find_social(self, email):
        platforms = {
            'twitter': 'https://twitter.com/',
            'github': 'https://github.com/',
            'linkedin': 'https://linkedin.com/in/',
            'facebook': 'https://facebook.com/',
            'instagram': 'https://instagram.com/',
            'tiktok': 'https://tiktok.com/@'
        }
        
        username = email.split('@')[0]
        found = []
        
        for platform, base_url in platforms.items():
            try:
                async with self.session.head(
                    f"{base_url}{username}",
                    allow_redirects=False,
                    timeout=10
                ) as resp:
                    if resp.status in [200, 301, 302]:
                        found.append({
                            'platform': platform,
                            'url': f"{base_url}{username}"
                        })
            except:
                pass
                
        return found
        
    def _calculate_risk(self, data):
        risk = 0
        if data.get('breaches'):
            risk += len(data['breaches']) * 10
        if data.get('disposable'):
            risk += 20
        if not data.get('valid'):
            risk += 15
        return min(risk, 100)
