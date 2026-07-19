import aiohttp
from typing import Dict, List
from modules.base import BaseModule

class UsernameOSINT(BaseModule):
    SITES = [
        {'name': 'GitHub', 'url': 'https://github.com/{username}'},
        {'name': 'Twitter', 'url': 'https://twitter.com/{username}'},
        {'name': 'Instagram', 'url': 'https://instagram.com/{username}'},
        {'name': 'Reddit', 'url': 'https://reddit.com/user/{username}'},
        {'name': 'YouTube', 'url': 'https://youtube.com/@{username}'},
        {'name': 'TikTok', 'url': 'https://tiktok.com/@{username}'},
        {'name': 'Pinterest', 'url': 'https://pinterest.com/{username}'},
        {'name': 'Flickr', 'url': 'https://flickr.com/people/{username}'},
        {'name': 'DeviantArt', 'url': 'https://deviantart.com/{username}'},
        {'name': 'Vimeo', 'url': 'https://vimeo.com/{username}'},
        {'name': 'SoundCloud', 'url': 'https://soundcloud.com/{username}'},
        {'name': 'Medium', 'url': 'https://medium.com/@{username}'},
        {'name': 'Quora', 'url': 'https://quora.com/profile/{username}'},
        {'name': 'Pastebin', 'url': 'https://pastebin.com/u/{username}'},
        {'name': 'Keybase', 'url': 'https://keybase.io/{username}'},
        {'name': 'HackerNews', 'url': 'https://news.ycombinator.com/user?id={username}'},
        {'name': 'BitBucket', 'url': 'https://bitbucket.org/{username}'},
        {'name': 'GitLab', 'url': 'https://gitlab.com/{username}'},
        {'name': 'VK', 'url': 'https://vk.com/{username}'},
        {'name': 'Ok.ru', 'url': 'https://ok.ru/profile/{username}'},
        {'name': 'Tumblr', 'url': 'https://{username}.tumblr.com'},
        {'name': 'Dribbble', 'url': 'https://dribbble.com/{username}'},
        {'name': 'Behance', 'url': 'https://behance.net/{username}'},
        {'name': 'Giters', 'url': 'https://giters.com/{username}'},
        {'name': 'Codepen', 'url': 'https://codepen.io/{username}'},
        {'name': 'Replit', 'url': 'https://replit.com/@{username}'},
        {'name': 'Dev.to', 'url': 'https://dev.to/{username}'},
        {'name': 'HackTheBox', 'url': 'https://hackthebox.eu/home/users/profile/{username}'},
        {'name': 'TryHackMe', 'url': 'https://tryhackme.com/p/{username}'},
        {'name': 'LeetCode', 'url': 'https://leetcode.com/{username}'},
        {'name': 'StackOverflow', 'url': 'https://stackoverflow.com/users/{username}'}
    ]
    
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        
    async def scan(self, username: str) -> Dict:
        results = {
            'username': username,
            'found': [],
            'not_found': [],
            'total': 0
        }
        
        tasks = []
        for site in self.SITES:
            url = site['url'].format(username=username)
            tasks.append(self._check_site(site['name'], url))
            
        responses = await asyncio.gather(*tasks)
        
        for name, url, exists in responses:
            if exists:
                results['found'].append({'name': name, 'url': url})
            else:
                results['not_found'].append(name)
                
        results['total'] = len(results['found'])
        return results
        
    async def _check_site(self, name, url):
        try:
            proxy = self._get_proxy()
            async with self.session.head(
                url,
                allow_redirects=False,
                timeout=10,
                proxy=proxy
            ) as resp:
                if name in ['GitHub', 'Twitter', 'Instagram', 'Reddit', 'YouTube']:
                    exists = resp.status == 200
                else:
                    exists = resp.status < 400
                return (name, url, exists)
        except:
            return (name, url, False)
