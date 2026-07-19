import random

class ProxyManager:
    def __init__(self, config):
        self.config = config
        self.proxies = []
        self.current_index = 0
        
    def get_proxy(self):
        if not self.config.get('proxy', {}).get('enabled', False):
            return None
            
        if not self.proxies:
            self.proxies = self._load_proxies()
            
        if not self.proxies:
            return None
            
        if self.config['proxy']['rotation'] == 'random':
            return random.choice(self.proxies)
        else:
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            return proxy
            
    def _load_proxies(self):
        try:
            with open('data/proxies.txt', 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except:
            return []
            
    def refresh(self):
        self.proxies = self._load_proxies()
