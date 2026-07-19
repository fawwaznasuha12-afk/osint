import aiohttp
import hashlib
from typing import Dict
from modules.base import BaseModule

class ImageOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        
    async def scan(self, image_url: str) -> Dict:
        results = {
            'url': image_url,
            'hash': None,
            'file_size': 0,
            'format': None
        }
        
        try:
            async with self.session.get(image_url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    results['file_size'] = len(data)
                    results['hash'] = hashlib.md5(data).hexdigest()
                    
                    content_type = resp.headers.get('content-type', '')
                    if 'image' in content_type:
                        results['format'] = content_type.split('/')[-1]
                        
        except:
            results['error'] = 'Failed to fetch image'
            
        return results
