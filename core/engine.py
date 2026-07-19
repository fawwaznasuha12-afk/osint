import asyncio
import aiohttp
import json
import yaml
import os
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich import box
from concurrent.futures import ThreadPoolExecutor

from core.validator import Validator
from core.output import OutputFormatter
from core.proxy import ProxyManager
from core.logger import Logger

from modules.email import EmailOSINT
from modules.username import UsernameOSINT
from modules.domain import DomainOSINT
from modules.social import SocialOSINT
from modules.phone import PhoneOSINT
from modules.image import ImageOSINT
from modules.crypto import CryptoOSINT

console = Console()

class Engine:
    def __init__(self, config_path='config/config.yaml'):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.results = {}
        self.executor = ThreadPoolExecutor(max_workers=self.config['scan']['max_concurrent'])
        self.session = None
        self.proxy_manager = ProxyManager(self.config)
        self.logger = Logger()
        self.validator = Validator()
        self.output = OutputFormatter()
        
    async def __aenter__(self):
        headers = {'User-Agent': self.config.get('user_agent', 'Mozilla/5.0')}
        timeout = aiohttp.ClientTimeout(total=self.config['scan']['timeout'])
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self
        
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
            
    async def run_module(self, module_name, target, depth=None):
        module_map = {
            'email': EmailOSINT,
            'username': UsernameOSINT,
            'domain': DomainOSINT,
            'social': SocialOSINT,
            'phone': PhoneOSINT,
            'image': ImageOSINT,
            'crypto': CryptoOSINT
        }
        
        module_class = module_map.get(module_name.lower())
        if not module_class:
            return {'error': f'Module {module_name} not found'}
            
        module = module_class(self.session, self.config, self.proxy_manager)
        
        if module_name.lower() == 'crypto' and depth:
            result = await module.scan(target, depth)
        else:
            result = await module.scan(target)
            
        self.results[module_name] = result
        return result
        
    async def scan_all(self, target):
        modules = ['email', 'username', 'domain', 'social', 'phone', 'crypto']
        results = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Running all modules...", total=len(modules))
            
            for module_name in modules:
                progress.update(task, description=f"[cyan]Running {module_name} module...")
                result = await self.run_module(module_name, target)
                results[module_name] = result
                progress.advance(task)
                
        self.results = results
        return results
        
    def generate_report(self, format='json'):
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'results': self.results
        }
        
        if format == 'json':
            return json.dumps(report, indent=2)
        elif format == 'txt':
            return self.output.to_text(report)
        elif format == 'csv':
            return self.output.to_csv(report)
        else:
            return json.dumps(report, indent=2)
            
    def save_report(self, target, format='json'):
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        target_clean = target.replace('@', '_').replace('.', '_').replace('/', '_')
        filename = f"reports/{target_clean}_{timestamp}.{format}"
        os.makedirs('reports', exist_ok=True)
        
        content = self.generate_report(format)
        with open(filename, 'w') as f:
            f.write(content)
            
        return filename
