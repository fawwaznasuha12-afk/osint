import hashlib
import re
import aiohttp
import asyncio
import dns.resolver
import whois
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
            'target': email,
            'module': 'email',
            'status': 'success',
            'data': {
                'email': email,
                'valid': False,
                'domain': '',
                'domain_age': None,
                'domain_trust': 0,
                'breaches': [],
                'breach_details': [],
                'leaked_passwords': 0,
                'disposable': False,
                'gravatar': None,
                'gravatar_profile': None,
                'social_accounts': [],
                'spf_record': None,
                'dkim_record': None,
                'dmarc_record': None,
                'reputation_score': 0,
                'risk_score': 0,
                'risk_level': 'low',
                'permutations': [],
                'similar_emails': [],
                'first_seen': None,
                'last_breach': None
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if not self._validate_email(email):
            results['status'] = 'error'
            results['data']['error'] = 'Invalid email format'
            return results
            
        data = results['data']
        data['domain'] = email.split('@')[1]
        
        domain_checks = await self._check_domain(data['domain'])
        data.update(domain_checks)
        
        data['valid'] = await self._verify_email(email)
        data['breaches'] = await self._check_breaches(email)
        data['breach_details'] = await self._get_breach_details(data['breaches'])
        data['leaked_passwords'] = await self._check_leaked_passwords(email)
        data['disposable'] = await self._is_disposable(email)
        data['gravatar'] = await self._get_gravatar(email)
        data['gravatar_profile'] = await self._get_gravatar_profile(email)
        data['social_accounts'] = await self._find_social(email)
        data['permutations'] = self._generate_permutations(email)
        data['similar_emails'] = self._generate_similar_emails(email)
        data['first_seen'] = await self._get_first_seen(email)
        data['last_breach'] = await self._get_last_breach(data['breaches'])
        data['reputation_score'] = self._calculate_reputation(data)
        data['risk_score'] = self._calculate_risk(data)
        data['risk_level'] = self._get_risk_level(data['risk_score'])
        
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
            
    async def _get_breach_details(self, breaches):
        details = []
        for breach in breaches:
            details.append({
                'name': breach.get('Name', 'Unknown'),
                'title': breach.get('Title', 'Unknown'),
                'domain': breach.get('Domain', 'Unknown'),
                'breach_date': breach.get('BreachDate', 'Unknown'),
                'added_date': breach.get('AddedDate', 'Unknown'),
                'pwn_count': breach.get('PwnCount', 0),
                'data_classes': breach.get('DataClasses', []),
                'is_verified': breach.get('IsVerified', False),
                'is_fabricated': breach.get('IsFabricated', False),
                'is_sensitive': breach.get('IsSensitive', False),
                'is_retired': breach.get('IsRetired', False),
                'is_spam_list': breach.get('IsSpamList', False),
                'logo_path': breach.get('LogoPath', '')
            })
        return details
        
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
        
    async def _get_gravatar_profile(self, email):
        hash_md5 = hashlib.md5(email.lower().encode()).hexdigest()
        url = f"https://www.gravatar.com/{hash_md5}.json"
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('entry', [{}])[0] if data.get('entry') else None
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
            'tumblr': 'https://tumblr.com/',
            'medium': 'https://medium.com/@',
            'devto': 'https://dev.to/',
            'keybase': 'https://keybase.io/',
            'hackernews': 'https://news.ycombinator.com/user?id='
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
            permutations.append(f"{parts[0]}.{parts[1][0]}@{domain}")
            permutations.append(f"{parts[0][0]}{parts[1]}@{domain}")
            
        permutations.append(f"{username}1@{domain}")
        permutations.append(f"{username}12@{domain}")
        permutations.append(f"{username}123@{domain}")
        permutations.append(f"{username}2024@{domain}")
        permutations.append(f"{username}@{domain.replace('.com', '.net')}")
        permutations.append(f"{username}@{domain.replace('.com', '.org')}")
        
        return permutations[:15]
        
    def _generate_similar_emails(self, email):
        username, domain = email.split('@')
        similar = []
        
        # Common typos
        common_typos = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'protonmail.com']
        for d in common_typos:
            if d != domain:
                similar.append(f"{username}@{d}")
                
        # Common prefixes/suffixes
        prefixes = ['info', 'admin', 'contact', 'support', 'sales', 'help']
        for p in prefixes:
            similar.append(f"{p}@{domain}")
            
        return similar[:10]
        
    async def _get_first_seen(self, email):
        try:
            # Check breach data for first appearance
            breaches = await self._check_breaches(email)
            if breaches:
                dates = []
                for breach in breaches:
                    if breach.get('BreachDate'):
                        dates.append(breach['BreachDate'])
                if dates:
                    return min(dates)
        except:
            pass
        return None
        
    async def _get_last_breach(self, breaches):
        if not breaches:
            return None
        try:
            dates = []
            for breach in breaches:
                if breach.get('BreachDate'):
                    dates.append(breach['BreachDate'])
            if dates:
                return max(dates)
        except:
            pass
        return None
        
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
