import aiohttp
import hashlib
from typing import Dict
from datetime import datetime
from modules.base import BaseModule

class ImageOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        
    async def scan(self, image_url: str) -> Dict:
        results = {
            'target': image_url,
            'module': 'image',
            'status': 'success',
            'data': {
                'url': image_url,
                'hash': None,
                'file_size': 0,
                'format': None
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            async with self.session.get(image_url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    results['data']['file_size'] = len(data)
                    results['data']['hash'] = hashlib.md5(data).hexdigest()
                    
                    content_type = resp.headers.get('content-type', '')
                    if 'image' in content_type:
                        results['data']['format'] = content_type.split('/')[-1]
                        
        except:
            results['status'] = 'error'
            results['data']['error'] = 'Failed to fetch image'
            
        return results
