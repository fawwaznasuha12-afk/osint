import aiohttp
from typing import Dict
from modules.base import BaseModule

class SocialOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        
    async def scan(self, target: str) -> Dict:
        results = {
            'target': target,
            'platforms': {},
            'total_followers': 0,
            'profiles': []
        }
        
        platforms = ['instagram', 'facebook', 'twitter', 'linkedin', 'tiktok']
        
        for platform in platforms:
            result = await self._scrape_platform(platform, target)
            results['platforms'][platform] = result
            if result.get('followers'):
                results['total_followers'] += result.get('followers', 0)
            if result.get('profile'):
                results['profiles'].append(result['profile'])
                
        return results
        
    async def _scrape_platform(self, platform, target):
        if platform == 'instagram':
            return await self._instagram(target)
        elif platform == 'facebook':
            return await self._facebook(target)
        elif platform == 'twitter':
            return await self._twitter(target)
        elif platform == 'linkedin':
            return await self._linkedin(target)
        elif platform == 'tiktok':
            return await self._tiktok(target)
            
    async def _instagram(self, username):
        try:
            async with self.session.get(
                f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            ) as resp:
                data = await resp.json()
                user = data.get('data', {}).get('user', {})
                return {
                    'exists': bool(user),
                    'username': user.get('username'),
                    'followers': user.get('edge_followed_by', {}).get('count', 0),
                    'following': user.get('edge_follow', {}).get('count', 0),
                    'posts': user.get('edge_owner_to_timeline_media', {}).get('count', 0),
                    'is_private': user.get('is_private', False),
                    'profile_url': f"https://instagram.com/{username}"
                }
        except:
            return {'exists': False}
            
    async def _facebook(self, username):
        try:
            async with self.session.get(
                f"https://graph.facebook.com/v18.0/{username}"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        'exists': True,
                        'profile': data,
                        'profile_url': f"https://facebook.com/{username}"
                    }
        except:
            pass
        return {'exists': False}
        
    async def _twitter(self, username):
        try:
            async with self.session.get(
                f"https://api.twitter.com/2/users/by/username/{username}"
            ) as resp:
                data = await resp.json()
                if 'data' in data:
                    user = data['data']
                    return {
                        'exists': True,
                        'id': user.get('id'),
                        'name': user.get('name'),
                        'username': user.get('username'),
                        'profile_url': f"https://twitter.com/{username}"
                    }
        except:
            pass
        return {'exists': False}
        
    async def _linkedin(self, username):
        try:
            async with self.session.get(
                f"https://linkedin.com/in/{username}"
            ) as resp:
                if resp.status == 200:
                    return {
                        'exists': True,
                        'profile_url': f"https://linkedin.com/in/{username}"
                    }
        except:
            pass
        return {'exists': False}
        
    async def _tiktok(self, username):
        try:
            async with self.session.get(
                f"https://www.tiktok.com/@{username}"
            ) as resp:
                if resp.status == 200:
                    return {
                        'exists': True,
                        'profile_url': f"https://tiktok.com/@{username}"
                    }
        except:
            pass
        return {'exists': False}
