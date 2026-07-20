import asyncio
import aiohttp
import hashlib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

class BaseModule:
    def __init__(self, session, config, proxy_manager):
        self.session = session
        self.config = config
        self.proxy_manager = proxy_manager
        self.cache = {}
        self.retry_count = 3
        self.timeout = 30
        
    async def scan(self, target):
        raise NotImplementedError("Each module must implement scan()")
        
    def _get_proxy(self):
        if hasattr(self.proxy_manager, 'get_proxy'):
            return self.proxy_manager.get_proxy()
        return None
        
    async def _fetch_with_retry(self, url, method='GET', headers=None, params=None, json_data=None):
        for attempt in range(self.retry_count):
            try:
                proxy = self._get_proxy()
                async with self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                    proxy=proxy,
                    timeout=self.timeout
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 429:
                        await asyncio.sleep(2 ** attempt)
                        continue
            except:
                await asyncio.sleep(1)
                continue
        return None
