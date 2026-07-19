import hashlib
import re
import aiohttp
import asyncio
import dns.resolver
from typing import Dict, List
from datetime import datetime
from modules.base import BaseModule

class EmailOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        self.disposable_domains = set()
        self._load_disposable()
        
    def _load_disposable(self):
        try:
            with open('data/disposable_domains.txt', 'r') as f:
                self.disposable_domains = set(line.strip() for line in f)
        except:
            pass
            
    async def scan(self, email: str) -> Dict:
        results = {
            'email': email,
            'valid': False,
            'domain': '',
            'domain_age': None,
            'domain_trust': 0,
            'breaches': [],
            'leaked_passwords': 0,
            'disposable': False,
            'gravatar': None,
            'social_accounts': [],
            'spf_record': None,
            'dkim_record': None,
            'dmarc_record': None,
            'reputation_score': 0,
            'risk_score': 0,
            'first_seen': None,
            'permutations': [],
            'confidence': 0
        }
        
        if not self._validate_email(email):
            results['error'] = 'Invalid email format'
            return results
            
        results['domain'] = email.split('@')[1]
        
        domain_checks = await self._check_domain(results['domain'])
        results.update(domain_checks)
        
        results['valid'] = await self._verify_email(email)
        results['breaches'] = await self._check_breaches(email)
        results['leaked_passwords'] = await self._check_leaked_passwords(email)
        results['disposable'] = await self._is_disposable(email)
        results['gravatar'] = await self._get_gravatar(email)
        results['social_accounts'] = await self._find_social(email)
        results['permutations'] = self._generate_permutations(email)
        results['reputation_score'] = self._calculate_reputation(results)
        results['risk_score'] = self._calculate_risk(results)
        results['confidence'] = self._calculate_confidence(
            len([v for v in results.values() if v]), 12
        )
        
        return results
        
    def _validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
        
    async def _check_domain(self, domain):
        results = {
            'domain_age': None,
            'domain_trust': 0,
            'spf_record': None,
            'dkim_record': None,
            'dmarc_record': None
        }
        
        try:
            import whois
            w = whois.whois(domain)
            if w.creation_date:
                if isinstance(w.creation_date, list):
                    creation = w.creation_date[0]
                else:
                    creation = w.creation_date
                age = (datetime.now() - creation).days
                results['domain_age'] = age
                results['domain_trust'] = min(100, age // 30)
        except:
            pass
            
        try:
            spf = dns.resolver.resolve(domain, 'TXT')
            for record in spf:
                if 'v=spf1' in str(record):
                    results['spf_record'] = str(record)
        except:
            pass
            
        try:
            dmarc = dns.resolver.resolve(f'_dmarc.{domain}', 'TXT')
            for record in dmarc:
                if 'v=DMARC1' in str(record):
                    results['dmarc_record'] = str(record)
        except:
            pass
            
        return results
        
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
            
    async def _check_leaked_passwords(self, email):
        try:
            import requests
            hash_md5 = hashlib.md5(email.encode()).hexdigest()
            response = requests.get(
                f"https://api.pwnedpasswords.com/range/{hash_md5[:5]}"
            )
            if response.status_code == 200:
                for line in response.text.splitlines():
                    suffix, count = line.split(':')
                    if hash_md5[5:].upper() == suffix:
                        return int(count)
            return 0
        except:
            return 0
            
    async def _is_disposable(self, email):
        domain = email.split('@')[1]
        if domain in self.disposable_domains:
            return True
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
            'tiktok': 'https://tiktok.com/@',
            'youtube': 'https://youtube.com/@',
            'reddit': 'https://reddit.com/user/',
            'pinterest': 'https://pinterest.com/',
            'tumblr': 'https://tumblr.com/'
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
                            'url': f"{base_url}{username}",
                            'status': 'active'
                        })
            except:
                pass
                
        return found
        
    def _generate_permutations(self, email):
        username, domain = email.split('@')
        permutations = []
        
        if '.' in username:
            parts = username.split('.')
            permutations.append(f"{parts[0]}{parts[1]}@{domain}")
            permutations.append(f"{parts[0]}_{parts[1]}@{domain}")
            permutations.append(f"{parts[0]}-{parts[1]}@{domain}")
            
        permutations.append(f"{username}1@{domain}")
        permutations.append(f"{username}12@{domain}")
        permutations.append(f"{username}123@{domain}")
        
        return permutations[:10]
        
    def _calculate_reputation(self, data):
        score = 0
        if data.get('valid'):
            score += 20
        if not data.get('breaches'):
            score += 25
        if data.get('domain_trust', 0) > 50:
            score += 20
        if data.get('spf_record'):
            score += 15
        if data.get('dmarc_record'):
            score += 10
        if data.get('gravatar'):
            score += 10
        return min(100, score)
        
    def _calculate_risk(self, data):
        risk = 0
        if data.get('breaches'):
            risk += len(data['breaches']) * 15
        if data.get('leaked_passwords', 0) > 0:
            risk += min(30, data['leaked_passwords'] // 10)
        if data.get('disposable'):
            risk += 20
        if not data.get('valid'):
            risk += 15
        if data.get('domain_trust', 100) < 30:
            risk += 10
        return min(100, risk)
