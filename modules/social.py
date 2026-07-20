import aiohttp
import re
from typing import Dict
from datetime import datetime
from modules.base import BaseModule

class SocialOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        
    async def scan(self, target: str) -> Dict:
        results = {
            'target': target,
            'module': 'social',
            'status': 'success',
            'data': {
                'target': target,
                'platforms': {},
                'total_followers': 0,
                'total_following': 0,
                'total_posts': 0,
                'profiles': [],
                'found_count': 0,
                'is_private': [],
                'bio_collected': []
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        platforms = ['instagram', 'facebook', 'twitter', 'linkedin', 'tiktok', 'youtube', 'reddit', 'github']
        
        data = results['data']
        for platform in platforms:
            result = await self._scrape_platform(platform, target)
            data['platforms'][platform] = result
            if result.get('exists'):
                data['found_count'] += 1
                if result.get('followers'):
                    data['total_followers'] += result.get('followers', 0)
                if result.get('following'):
                    data['total_following'] += result.get('following', 0)
                if result.get('posts'):
                    data['total_posts'] += result.get('posts', 0)
                if result.get('profile_url'):
                    data['profiles'].append(result['profile_url'])
                if result.get('is_private'):
                    data['is_private'].append({'platform': platform, 'private': result['is_private']})
                if result.get('bio'):
                    data['bio_collected'].append({'platform': platform, 'bio': result['bio']})
                
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
        elif platform == 'youtube':
            return await self._youtube(target)
        elif platform == 'reddit':
            return await self._reddit(target)
        elif platform == 'github':
            return await self._github(target)
        return {'exists': False}
        
    async def _instagram(self, username):
        try:
            async with self.session.get(
                f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}",
                headers={'User-Agent': 'Mozilla/5.0'}
            ) as resp:
                data = await resp.json()
                user = data.get('data', {}).get('user', {})
                if user:
                    return {
                        'exists': True,
                        'username': user.get('username'),
                        'full_name': user.get('full_name'),
                        'followers': user.get('edge_followed_by', {}).get('count', 0),
                        'following': user.get('edge_follow', {}).get('count', 0),
                        'posts': user.get('edge_owner_to_timeline_media', {}).get('count', 0),
                        'is_private': user.get('is_private', False),
                        'is_verified': user.get('is_verified', False),
                        'bio': user.get('biography', ''),
                        'profile_url': f"https://instagram.com/{username}",
                        'profile_pic': user.get('profile_pic_url', '')
                    }
        except:
            pass
        return {'exists': False}
        
    async def _facebook(self, username):
        try:
            async with self.session.get(
                f"https://graph.facebook.com/v18.0/{username}",
                timeout=10
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        'exists': True,
                        'profile': data,
                        'profile_url': f"https://facebook.com/{username}",
                        'id': data.get('id'),
                        'name': data.get('name')
                    }
        except:
            pass
        return {'exists': False}
        
    async def _twitter(self, username):
        try:
            async with self.session.get(
                f"https://api.twitter.com/2/users/by/username/{username}",
                timeout=10
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
                f"https://linkedin.com/in/{username}",
                timeout=10
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
                f"https://www.tiktok.com/@{username}",
                timeout=10
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    followers_match = re.search(r'"followerCount":(\d+)', html)
                    followers = int(followers_match.group(1)) if followers_match else 0
                    return {
                        'exists': True,
                        'profile_url': f"https://tiktok.com/@{username}",
                        'followers': followers
                    }
        except:
            pass
        return {'exists': False}
        
    async def _youtube(self, username):
        try:
            async with self.session.get(
                f"https://youtube.com/@{username}",
                timeout=10
            ) as resp:
                if resp.status == 200:
                    return {
                        'exists': True,
                        'profile_url': f"https://youtube.com/@{username}"
                    }
        except:
            pass
        return {'exists': False}
        
    async def _reddit(self, username):
        try:
            async with self.session.get(
                f"https://reddit.com/user/{username}",
                timeout=10
            ) as resp:
                if resp.status == 200:
                    return {
                        'exists': True,
                        'profile_url': f"https://reddit.com/user/{username}"
                    }
        except:
            pass
        return {'exists': False}
        
    async def _github(self, username):
        try:
            async with self.session.get(
                f"https://github.com/{username}",
                timeout=10
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    repos_match = re.search(r'(\d+,?\d*)\s+repositories', html)
                    repos = repos_match.group(1).replace(',', '') if repos_match else 0
                    return {
                        'exists': True,
                        'profile_url': f"https://github.com/{username}",
                        'repositories': int(repos) if repos else 0
                    }
        except:
            pass
        return {'exists': False}
