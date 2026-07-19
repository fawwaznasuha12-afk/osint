import dns.resolver
import whois
import ssl
import socket
import asyncio
from typing import Dict, List
from modules.base import BaseModule

class DomainOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        
    async def scan(self, domain: str) -> Dict:
        results = {
            'domain': domain,
            'whois': None,
            'dns_records': {},
            'subdomains': [],
            'ssl_cert': None,
            'cloudflare': False
        }
        
        results['whois'] = await self._get_whois(domain)
        results['dns_records'] = await self._get_dns(domain)
        results['subdomains'] = await self._find_subdomains(domain)
        results['ssl_cert'] = await self._get_ssl(domain)
        results['cloudflare'] = await self._check_cloudflare(domain)
        
        return results
        
    async def _get_whois(self, domain):
        try:
            w = whois.whois(domain)
            return {
                'registrar': w.registrar,
                'creation_date': str(w.creation_date) if w.creation_date else None,
                'expiration_date': str(w.expiration_date) if w.expiration_date else None,
                'name_servers': w.name_servers
            }
        except:
            return None
            
    async def _get_dns(self, domain):
        records = {}
        record_types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'CNAME', 'SOA']
        
        for rtype in record_types:
            try:
                answers = dns.resolver.resolve(domain, rtype)
                records[rtype] = [str(r) for r in answers]
            except:
                records[rtype] = []
                
        return records
        
    async def _find_subdomains(self, domain):
        common_subdomains = [
            'www', 'mail', 'ftp', 'localhost', 'webmail', 'smtp',
            'pop', 'ns1', 'webdisk', 'ns2', 'cpanel', 'whm',
            'autodiscover', 'autoconfig', 'm', 'imap', 'test',
            'ns', 'blog', 'pop3', 'dev', 'www2', 'admin',
            'forum', 'news', 'vpn', 'ns3', 'mail2', 'new',
            'mysql', 'old', 'lists', 'support', 'mobile',
            'mx', 'static', 'docs', 'beta', 'shop', 'sql',
            'secure', 'demo', 'cp', 'calendar', 'wiki',
            'web', 'media', 'email', 'images', 'img',
            'download', 'dns', 'piwik', 'stats', 'dns2',
            'apps', 'server', 'mssql', 'remote', 'api',
            'dev-api', 'staging', 'cdn', 'assets', 'files',
            'video', 'audio', 'stream', 'chat', 'live'
        ]
        
        found = []
        tasks = []
        for sub in common_subdomains:
            full = f"{sub}.{domain}"
            tasks.append(self._check_subdomain(full))
            
        results = await asyncio.gather(*tasks)
        
        for full, exists in results:
            if exists:
                found.append(full)
                
        return found
        
    async def _check_subdomain(self, domain):
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, socket.gethostbyname, domain
            )
            return (domain, True)
        except:
            return (domain, False)
            
    async def _get_ssl(self, domain):
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'notBefore': cert['notBefore'],
                        'notAfter': cert['notAfter']
                    }
        except:
            return None
            
    async def _check_cloudflare(self, domain):
        try:
            answers = dns.resolver.resolve(domain, 'A')
            for r in answers:
                if 'cloudflare' in str(r).lower():
                    return True
            return False
        except:
            return False
