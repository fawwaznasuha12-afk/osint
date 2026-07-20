import dns.resolver
import whois
import ssl
import socket
import asyncio
import aiohttp
from typing import Dict, List
from datetime import datetime
from modules.base import BaseModule

class DomainOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        
    async def scan(self, domain: str) -> Dict:
        results = {
            'target': domain,
            'module': 'domain',
            'status': 'success',
            'data': {
                'domain': domain,
                'whois': None,
                'dns_records': {},
                'subdomains': [],
                'subdomain_count': 0,
                'ssl_cert': None,
                'ssl_valid': False,
                'ssl_days_left': 0,
                'cloudflare': False,
                'tech_stack': [],
                'tech_stack_detected': [],
                'ip_addresses': [],
                'server_location': None,
                'hosting_provider': None,
                'website_title': None,
                'website_description': None,
                'risk_score': 0
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        data = results['data']
        data['whois'] = await self._get_whois(domain)
        data['dns_records'] = await self._get_dns(domain)
        data['subdomains'] = await self._find_subdomains(domain)
        data['subdomain_count'] = len(data['subdomains'])
        data['ssl_cert'] = await self._get_ssl(domain)
        data['ssl_valid'] = await self._check_ssl_valid(data['ssl_cert'])
        data['ssl_days_left'] = await self._get_ssl_days_left(data['ssl_cert'])
        data['cloudflare'] = await self._check_cloudflare(domain)
        data['tech_stack'] = await self._detect_tech(domain)
        data['ip_addresses'] = await self._get_ip_addresses(domain)
        data['hosting_provider'] = await self._get_hosting_provider(data['ip_addresses'])
        data['website_title'], data['website_description'] = await self._get_website_info(domain)
        data['risk_score'] = self._calculate_risk(data)
        
        return results
        
    async def _get_whois(self, domain):
        try:
            w = whois.whois(domain)
            return {
                'registrar': w.registrar,
                'creation_date': str(w.creation_date) if w.creation_date else None,
                'expiration_date': str(w.expiration_date) if w.expiration_date else None,
                'updated_date': str(w.updated_date) if w.updated_date else None,
                'name_servers': w.name_servers,
                'emails': w.emails,
                'country': w.country,
                'org': w.org
            }
        except:
            return None
            
    async def _get_dns(self, domain):
        records = {}
        record_types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'CNAME', 'SOA', 'PTR', 'SRV']
        
        for rtype in record_types:
            try:
                answers = dns.resolver.resolve(domain, rtype)
                records[rtype] = [str(r) for r in answers]
            except:
                records[rtype] = []
                
        return records
        
    async def _find_subdomains(self, domain):
        subdomains = [
            'www', 'mail', 'ftp', 'webmail', 'smtp', 'pop', 'ns1', 'ns2', 'ns3', 'ns4',
            'cpanel', 'whm', 'autodiscover', 'autoconfig', 'm', 'imap', 'test',
            'ns', 'blog', 'pop3', 'dev', 'www2', 'admin', 'forum', 'news',
            'vpn', 'mail2', 'new', 'mysql', 'old', 'lists', 'support',
            'mobile', 'mx', 'static', 'docs', 'beta', 'shop', 'sql', 'secure',
            'demo', 'cp', 'calendar', 'wiki', 'web', 'media', 'email', 'images',
            'img', 'download', 'dns', 'stats', 'apps', 'server', 'remote', 'api',
            'staging', 'cdn', 'assets', 'files', 'video', 'audio', 'stream', 'chat', 'live',
            'ftp2', 'mail1', 'mail3', 'pop3', 'smtp2', 'web2', 'web3', 'www3',
            'corp', 'internal', 'devops', 'test2', 'stage', 'prod', 'production',
            'backup', 'storage', 'db', 'database', 'redis', 'memcache', 'elastic',
            'kibana', 'grafana', 'prometheus', 'jenkins', 'gitlab', 'jira', 'confluence',
            'sonar', 'nexus', 'artifactory', 'docker', 'k8s', 'kubernetes', 'openshift',
            'aws', 'azure', 'gcp', 'cloud', 'compute', 'lambda', 'ec2', 's3', 'rds',
            'dynamo', 'elasticache', 'redshift', 'glacier', 'route53', 'cloudfront',
            'waf', 'shield', 'inspector', 'guardduty', 'macie', 'detective', 'securityhub'
        ]
        
        found = []
        tasks = []
        for sub in subdomains:
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
                        'notAfter': cert['notAfter'],
                        'serialNumber': cert.get('serialNumber', ''),
                        'version': cert.get('version', 0),
                        'subjectAltName': cert.get('subjectAltName', [])
                    }
        except:
            return None
            
    async def _check_ssl_valid(self, cert):
        if not cert:
            return False
        try:
            not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            return not_after > datetime.now()
        except:
            return False
            
    async def _get_ssl_days_left(self, cert):
        if not cert:
            return 0
        try:
            not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            delta = not_after - datetime.now()
            return delta.days
        except:
            return 0
            
    async def _check_cloudflare(self, domain):
        try:
            answers = dns.resolver.resolve(domain, 'A')
            for r in answers:
                if 'cloudflare' in str(r).lower():
                    return True
            return False
        except:
            return False
            
    async def _detect_tech(self, domain):
        tech = []
        try:
            async with self.session.get(f"https://{domain}", timeout=10) as resp:
                headers = resp.headers
                if 'server' in headers:
                    tech.append(f"Server: {headers['server']}")
                if 'x-powered-by' in headers:
                    tech.append(f"Powered by: {headers['x-powered-by']}")
                if 'x-generator' in headers:
                    tech.append(f"Generator: {headers['x-generator']}")
                if 'x-ua-compatible' in headers:
                    tech.append(f"UA Compatible: {headers['x-ua-compatible']}")
                    
                # Detect CMS from meta tags
                html = await resp.text()
                if 'wp-content' in html or 'wp-includes' in html:
                    tech.append('WordPress')
                if 'drupal' in html.lower():
                    tech.append('Drupal')
                if 'joomla' in html.lower():
                    tech.append('Joomla')
                if 'laravel' in html.lower():
                    tech.append('Laravel')
                if 'react' in html.lower():
                    tech.append('React')
                if 'vue' in html.lower():
                    tech.append('Vue.js')
                if 'angular' in html.lower():
                    tech.append('Angular')
        except:
            pass
        return tech
        
    async def _get_ip_addresses(self, domain):
        ips = []
        try:
            answers = dns.resolver.resolve(domain, 'A')
            for r in answers:
                ips.append(str(r))
        except:
            pass
        return ips
        
    async def _get_hosting_provider(self, ips):
        if not ips:
            return None
        try:
            # Simple provider detection based on IP ranges
            providers = {
                'aws': ['54.', '52.', '18.', '3.', '13.', '35.', '44.', '99.', '100.', '104.', '107.', '108.', '112.', '113.', '114.', '115.', '116.', '117.', '118.', '119.', '120.', '121.', '122.', '123.', '124.', '125.', '126.', '127.', '128.', '129.', '130.', '131.', '132.', '133.', '134.', '135.', '136.', '137.', '138.', '139.', '140.', '141.', '142.', '143.', '144.', '145.', '146.', '147.', '148.', '149.', '150.', '151.', '152.', '153.', '154.', '155.', '156.', '157.', '158.', '159.', '160.', '161.', '162.', '163.', '164.', '165.', '166.', '167.', '168.', '169.', '170.', '171.', '172.', '173.', '174.', '175.', '176.', '177.', '178.', '179.', '180.', '181.', '182.', '183.', '184.', '185.', '186.', '187.', '188.', '189.', '190.', '191.', '192.', '193.', '194.', '195.', '196.', '197.', '198.', '199.', '200.', '201.', '202.', '203.', '204.', '205.', '206.', '207.', '208.', '209.', '210.', '211.', '212.', '213.', '214.', '215.', '216.', '217.', '218.', '219.', '220.', '221.', '222.', '223.', '224.', '225.', '226.', '227.', '228.', '229.', '230.', '231.', '232.', '233.', '234.', '235.', '236.', '237.', '238.', '239.', '240.', '241.', '242.', '243.', '244.', '245.', '246.', '247.', '248.', '249.', '250.', '251.', '252.', '253.', '254.'],
                'azure': ['13.', '20.', '40.', '51.', '52.', '65.', '70.', '104.', '138.', '168.', '191.', '207.', '209.', '213.', '214.', '215.', '216.', '217.', '218.', '219.', '220.', '221.', '222.', '223.', '224.', '225.', '226.', '227.', '228.', '229.', '230.', '231.', '232.', '233.', '234.', '235.', '236.', '237.', '238.', '239.', '240.', '241.', '242.', '243.', '244.', '245.', '246.', '247.', '248.', '249.', '250.', '251.', '252.', '253.', '254.'],
                'google': ['8.8.', '34.', '35.', '104.', '107.', '108.', '130.', '142.', '146.', '148.', '172.', '173.', '174.', '175.', '176.', '177.', '178.', '179.', '180.', '181.', '182.', '183.', '184.', '185.', '186.', '187.', '188.', '189.', '190.', '191.', '192.', '193.', '194.', '195.', '196.', '197.', '198.', '199.', '200.', '201.', '202.', '203.', '204.', '205.', '206.', '207.', '208.', '209.', '210.', '211.', '212.', '213.', '214.', '215.', '216.', '217.', '218.', '219.', '220.', '221.', '222.', '223.', '224.', '225.', '226.', '227.', '228.', '229.', '230.', '231.', '232.', '233.', '234.', '235.', '236.', '237.', '238.', '239.', '240.', '241.', '242.', '243.', '244.', '245.', '246.', '247.', '248.', '249.', '250.', '251.', '252.', '253.', '254.'],
                'cloudflare': ['104.16.', '104.17.', '104.18.', '104.19.', '104.20.', '104.21.', '104.22.', '104.23.', '104.24.', '104.25.', '104.26.', '104.27.', '104.28.', '104.29.', '104.30.', '104.31.', '172.64.', '172.65.', '172.66.', '172.67.', '172.68.', '172.69.', '172.70.', '172.71.', '172.72.', '172.73.', '172.74.', '172.75.', '172.76.', '172.77.', '172.78.', '172.79.', '172.80.', '172.81.', '172.82.', '172.83.', '172.84.', '172.85.', '172.86.', '172.87.', '172.88.', '172.89.', '172.90.', '172.91.', '172.92.', '172.93.', '172.94.', '172.95.', '172.96.', '172.97.', '172.98.', '172.99.', '172.100.', '172.101.', '172.102.', '172.103.', '172.104.', '172.105.', '172.106.', '172.107.', '172.108.', '172.109.', '172.110.', '172.111.', '172.112.', '172.113.', '172.114.', '172.115.', '172.116.', '172.117.', '172.118.', '172.119.', '172.120.', '172.121.', '172.122.', '172.123.', '172.124.', '172.125.', '172.126.', '172.127.']
            }
            
            for ip in ips:
                for provider, prefixes in providers.items():
                    for prefix in prefixes:
                        if ip.startswith(prefix):
                            return provider.upper()
        except:
            pass
        return None
        
    async def _get_website_info(self, domain):
        title = None
        description = None
        try:
            async with self.session.get(f"https://{domain}", timeout=10) as resp:
                html = await resp.text()
                import re
                title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1)
                desc_match = re.search(r'<meta name="description" content="(.*?)"', html, re.IGNORECASE)
                if desc_match:
                    description = desc_match.group(1)
        except:
            pass
        return title, description
        
    def _calculate_risk(self, data):
        risk = 0
        if not data.get('ssl_valid'):
            risk += 20
        if data.get('ssl_days_left', 0) < 30 and data.get('ssl_days_left', 0) > 0:
            risk += 15
        if not data.get('whois'):
            risk += 10
        if data.get('cloudflare'):
            risk += 5
        if len(data.get('subdomains', [])) > 50:
            risk += 10
        return min(100, risk)
