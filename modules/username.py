import aiohttp
import asyncio
from typing import Dict, List
from datetime import datetime
from modules.base import BaseModule

class UsernameOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        
    async def scan(self, username: str) -> Dict:
        results = {
            'target': username,
            'module': 'username',
            'status': 'success',
            'data': {
                'username': username,
                'found': [],
                'not_found': [],
                'total': 0,
                'found_count': 0,
                'platforms': {
                    'social': [],
                    'video': [],
                    'forum': [],
                    'blog': [],
                    'audio': [],
                    'photo': [],
                    'gaming': [],
                    'chat': [],
                    'coding': [],
                    'dating': [],
                    'security': [],
                    'email': [],
                    'storage': []
                },
                'platforms_found': [],
                'most_active': None,
                'profile_pictures': [],
                'bio_samples': []
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        sites = self._get_platforms()
        tasks = []
        for site in sites:
            url = site['url'].format(username=username)
            tasks.append(self._check_site(site['name'], url, site.get('type', 'social'), site.get('method', 'head')))
            
        responses = await asyncio.gather(*tasks)
        
        data = results['data']
        found_platforms = []
        
        for name, url, exists, platform_type, status_code in responses:
            if exists:
                entry = {'name': name, 'url': url, 'type': platform_type, 'status': status_code}
                data['found'].append(entry)
                found_platforms.append(name)
                if platform_type in data['platforms']:
                    data['platforms'][platform_type].append(name)
            else:
                data['not_found'].append(name)
                
        data['total'] = len(data['found'])
        data['found_count'] = len(data['found'])
        data['platforms_found'] = found_platforms
        
        if data['found']:
            data['most_active'] = data['found'][0]['name']
            
        return results
        
    def _get_platforms(self):
        return [
            # Social Media
            {'name': 'Instagram', 'url': 'https://instagram.com/{username}', 'type': 'social', 'method': 'head'},
            {'name': 'Twitter', 'url': 'https://twitter.com/{username}', 'type': 'social', 'method': 'head'},
            {'name': 'Facebook', 'url': 'https://facebook.com/{username}', 'type': 'social', 'method': 'head'},
            {'name': 'TikTok', 'url': 'https://tiktok.com/@{username}', 'type': 'social', 'method': 'head'},
            {'name': 'Snapchat', 'url': 'https://snapchat.com/add/{username}', 'type': 'social', 'method': 'head'},
            {'name': 'Pinterest', 'url': 'https://pinterest.com/{username}', 'type': 'social', 'method': 'head'},
            {'name': 'Tumblr', 'url': 'https://{username}.tumblr.com', 'type': 'social', 'method': 'head'},
            {'name': 'LinkedIn', 'url': 'https://linkedin.com/in/{username}', 'type': 'social', 'method': 'head'},
            {'name': 'VK', 'url': 'https://vk.com/{username}', 'type': 'social', 'method': 'head'},
            {'name': 'Odnoklassniki', 'url': 'https://ok.ru/{username}', 'type': 'social', 'method': 'head'},
            {'name': 'Myspace', 'url': 'https://myspace.com/{username}', 'type': 'social', 'method': 'head'},
            {'name': 'WeChat', 'url': 'https://wechat.com/{username}', 'type': 'social', 'method': 'head'},
            {'name': 'Line', 'url': 'https://line.me/{username}', 'type': 'social', 'method': 'head'},
            {'name': 'KakaoTalk', 'url': 'https://kakao.com/{username}', 'type': 'social', 'method': 'head'},
            {'name': 'Telegram', 'url': 'https://t.me/{username}', 'type': 'chat', 'method': 'head'},
            {'name': 'Discord', 'url': 'https://discord.com/users/{username}', 'type': 'chat', 'method': 'head'},
            {'name': 'WhatsApp', 'url': 'https://wa.me/{username}', 'type': 'chat', 'method': 'head'},
            {'name': 'Signal', 'url': 'https://signal.org/{username}', 'type': 'chat', 'method': 'head'},
            {'name': 'Viber', 'url': 'https://viber.com/{username}', 'type': 'chat', 'method': 'head'},
            {'name': 'Kik', 'url': 'https://kik.com/{username}', 'type': 'chat', 'method': 'head'},
            
            # Video
            {'name': 'YouTube', 'url': 'https://youtube.com/@{username}', 'type': 'video', 'method': 'head'},
            {'name': 'Twitch', 'url': 'https://twitch.tv/{username}', 'type': 'video', 'method': 'head'},
            {'name': 'Vimeo', 'url': 'https://vimeo.com/{username}', 'type': 'video', 'method': 'head'},
            {'name': 'DailyMotion', 'url': 'https://dailymotion.com/{username}', 'type': 'video', 'method': 'head'},
            {'name': 'Vine', 'url': 'https://vine.co/{username}', 'type': 'video', 'method': 'head'},
            
            # Forum
            {'name': 'Reddit', 'url': 'https://reddit.com/user/{username}', 'type': 'forum', 'method': 'head'},
            {'name': 'Quora', 'url': 'https://quora.com/profile/{username}', 'type': 'forum', 'method': 'head'},
            {'name': 'StackOverflow', 'url': 'https://stackoverflow.com/users/{username}', 'type': 'forum', 'method': 'head'},
            {'name': 'HackerNews', 'url': 'https://news.ycombinator.com/user?id={username}', 'type': 'forum', 'method': 'head'},
            {'name': 'Pastebin', 'url': 'https://pastebin.com/u/{username}', 'type': 'forum', 'method': 'head'},
            {'name': 'XDA', 'url': 'https://xdaforums.com/member/{username}', 'type': 'forum', 'method': 'head'},
            {'name': '4chan', 'url': 'https://4chan.org/{username}', 'type': 'forum', 'method': 'head'},
            
            # Blog
            {'name': 'Medium', 'url': 'https://medium.com/@{username}', 'type': 'blog', 'method': 'head'},
            {'name': 'Substack', 'url': 'https://substack.com/@{username}', 'type': 'blog', 'method': 'head'},
            {'name': 'WordPress', 'url': 'https://wordpress.com/{username}', 'type': 'blog', 'method': 'head'},
            {'name': 'Blogger', 'url': 'https://blogger.com/{username}', 'type': 'blog', 'method': 'head'},
            {'name': 'Ghost', 'url': 'https://ghost.org/{username}', 'type': 'blog', 'method': 'head'},
            {'name': 'Dev.to', 'url': 'https://dev.to/{username}', 'type': 'blog', 'method': 'head'},
            {'name': 'Hashnode', 'url': 'https://hashnode.com/@{username}', 'type': 'blog', 'method': 'head'},
            
            # Audio
            {'name': 'Spotify', 'url': 'https://open.spotify.com/user/{username}', 'type': 'audio', 'method': 'head'},
            {'name': 'SoundCloud', 'url': 'https://soundcloud.com/{username}', 'type': 'audio', 'method': 'head'},
            {'name': 'Mixcloud', 'url': 'https://mixcloud.com/{username}', 'type': 'audio', 'method': 'head'},
            {'name': 'Audiomack', 'url': 'https://audiomack.com/{username}', 'type': 'audio', 'method': 'head'},
            {'name': 'Bandcamp', 'url': 'https://bandcamp.com/{username}', 'type': 'audio', 'method': 'head'},
            
            # Photo
            {'name': 'Flickr', 'url': 'https://flickr.com/people/{username}', 'type': 'photo', 'method': 'head'},
            {'name': '500px', 'url': 'https://500px.com/{username}', 'type': 'photo', 'method': 'head'},
            {'name': 'Unsplash', 'url': 'https://unsplash.com/@{username}', 'type': 'photo', 'method': 'head'},
            {'name': 'DeviantArt', 'url': 'https://deviantart.com/{username}', 'type': 'photo', 'method': 'head'},
            {'name': 'ArtStation', 'url': 'https://artstation.com/{username}', 'type': 'photo', 'method': 'head'},
            {'name': 'Dribbble', 'url': 'https://dribbble.com/{username}', 'type': 'photo', 'method': 'head'},
            {'name': 'Behance', 'url': 'https://behance.net/{username}', 'type': 'photo', 'method': 'head'},
            
            # Gaming
            {'name': 'Steam', 'url': 'https://steamcommunity.com/id/{username}', 'type': 'gaming', 'method': 'head'},
            {'name': 'PlayStation', 'url': 'https://playstation.com/{username}', 'type': 'gaming', 'method': 'head'},
            {'name': 'Xbox', 'url': 'https://xbox.com/{username}', 'type': 'gaming', 'method': 'head'},
            {'name': 'Nintendo', 'url': 'https://nintendo.com/{username}', 'type': 'gaming', 'method': 'head'},
            {'name': 'EpicGames', 'url': 'https://epicgames.com/{username}', 'type': 'gaming', 'method': 'head'},
            {'name': 'RiotGames', 'url': 'https://riotgames.com/{username}', 'type': 'gaming', 'method': 'head'},
            {'name': 'BattleNet', 'url': 'https://battlenet.com/{username}', 'type': 'gaming', 'method': 'head'},
            {'name': 'Origin', 'url': 'https://origin.com/{username}', 'type': 'gaming', 'method': 'head'},
            {'name': 'GOG', 'url': 'https://gog.com/{username}', 'type': 'gaming', 'method': 'head'},
            
            # Dating
            {'name': 'Badoo', 'url': 'https://badoo.com/{username}', 'type': 'dating', 'method': 'head'},
            {'name': 'Tinder', 'url': 'https://tinder.com/@{username}', 'type': 'dating', 'method': 'head'},
            {'name': 'OkCupid', 'url': 'https://okcupid.com/{username}', 'type': 'dating', 'method': 'head'},
            {'name': 'Match', 'url': 'https://match.com/{username}', 'type': 'dating', 'method': 'head'},
            
            # Coding
            {'name': 'GitHub', 'url': 'https://github.com/{username}', 'type': 'coding', 'method': 'head'},
            {'name': 'GitLab', 'url': 'https://gitlab.com/{username}', 'type': 'coding', 'method': 'head'},
            {'name': 'Bitbucket', 'url': 'https://bitbucket.org/{username}', 'type': 'coding', 'method': 'head'},
            {'name': 'CodePen', 'url': 'https://codepen.io/{username}', 'type': 'coding', 'method': 'head'},
            {'name': 'Replit', 'url': 'https://replit.com/@{username}', 'type': 'coding', 'method': 'head'},
            {'name': 'LeetCode', 'url': 'https://leetcode.com/{username}', 'type': 'coding', 'method': 'head'},
            {'name': 'HackerRank', 'url': 'https://hackerrank.com/{username}', 'type': 'coding', 'method': 'head'},
            {'name': 'Codeforces', 'url': 'https://codeforces.com/profile/{username}', 'type': 'coding', 'method': 'head'},
            {'name': 'SourceForge', 'url': 'https://sourceforge.net/{username}', 'type': 'coding', 'method': 'head'},
            
            # Security
            {'name': 'HackTheBox', 'url': 'https://hackthebox.eu/home/users/profile/{username}', 'type': 'security', 'method': 'head'},
            {'name': 'TryHackMe', 'url': 'https://tryhackme.com/p/{username}', 'type': 'security', 'method': 'head'},
            {'name': 'Keybase', 'url': 'https://keybase.io/{username}', 'type': 'security', 'method': 'head'},
            
            # Email
            {'name': 'ProtonMail', 'url': 'https://protonmail.com/{username}', 'type': 'email', 'method': 'head'},
            {'name': 'GMX', 'url': 'https://gmx.com/{username}', 'type': 'email', 'method': 'head'},
            {'name': 'Yandex', 'url': 'https://yandex.ru/{username}', 'type': 'email', 'method': 'head'},
            {'name': 'MailRu', 'url': 'https://mail.ru/{username}', 'type': 'email', 'method': 'head'},
            
            # Storage
            {'name': 'GoogleDrive', 'url': 'https://drive.google.com/{username}', 'type': 'storage', 'method': 'head'},
            {'name': 'Dropbox', 'url': 'https://dropbox.com/{username}', 'type': 'storage', 'method': 'head'},
            {'name': 'OneDrive', 'url': 'https://onedrive.com/{username}', 'type': 'storage', 'method': 'head'},
            {'name': 'Mega', 'url': 'https://mega.nz/{username}', 'type': 'storage', 'method': 'head'}
        ]
        
    async def _check_site(self, name, url, platform_type, method='head'):
        try:
            if method == 'head':
                async with self.session.head(
                    url,
                    allow_redirects=False,
                    timeout=10
                ) as resp:
                    exists = resp.status < 400
                    return (name, url, exists, platform_type, resp.status)
            else:
                async with self.session.get(
                    url,
                    allow_redirects=False,
                    timeout=10
                ) as resp:
                    exists = resp.status < 400
                    return (name, url, exists, platform_type, resp.status)
        except:
            return (name, url, False, platform_type, 0)
