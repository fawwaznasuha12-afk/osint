import aiohttp
import asyncio
from typing import Dict, List
from modules.base import BaseModule

class UsernameOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        
    async def scan(self, username: str) -> Dict:
        results = {
            'username': username,
            'found': [],
            'not_found': [],
            'total': 0,
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
                'dating': []
            }
        }
        
        sites = self._get_social_platforms()
        tasks = []
        for site in sites:
            url = site['url'].format(username=username)
            tasks.append(self._check_site(site['name'], url, site.get('type', 'social')))
            
        responses = await asyncio.gather(*tasks)
        
        for name, url, exists, platform_type in responses:
            if exists:
                entry = {'name': name, 'url': url, 'type': platform_type}
                results['found'].append(entry)
                if platform_type in results['platforms']:
                    results['platforms'][platform_type].append(name)
            else:
                results['not_found'].append(name)
                
        results['total'] = len(results['found'])
        return results
        
    def _get_social_platforms(self):
        return [
            # Social Media Utama
            {'name': 'Instagram', 'url': 'https://instagram.com/{username}', 'type': 'social'},
            {'name': 'Twitter', 'url': 'https://twitter.com/{username}', 'type': 'social'},
            {'name': 'Facebook', 'url': 'https://facebook.com/{username}', 'type': 'social'},
            {'name': 'TikTok', 'url': 'https://tiktok.com/@{username}', 'type': 'social'},
            {'name': 'Snapchat', 'url': 'https://snapchat.com/add/{username}', 'type': 'social'},
            {'name': 'Pinterest', 'url': 'https://pinterest.com/{username}', 'type': 'social'},
            {'name': 'Tumblr', 'url': 'https://{username}.tumblr.com', 'type': 'social'},
            {'name': 'LinkedIn', 'url': 'https://linkedin.com/in/{username}', 'type': 'social'},
            {'name': 'VK', 'url': 'https://vk.com/{username}', 'type': 'social'},
            {'name': 'Odnoklassniki', 'url': 'https://ok.ru/{username}', 'type': 'social'},
            {'name': 'Myspace', 'url': 'https://myspace.com/{username}', 'type': 'social'},
            {'name': 'Badoo', 'url': 'https://badoo.com/{username}', 'type': 'dating'},
            {'name': 'Tinder', 'url': 'https://tinder.com/@{username}', 'type': 'dating'},
            
            # Video
            {'name': 'YouTube', 'url': 'https://youtube.com/@{username}', 'type': 'video'},
            {'name': 'Twitch', 'url': 'https://twitch.tv/{username}', 'type': 'video'},
            {'name': 'Vimeo', 'url': 'https://vimeo.com/{username}', 'type': 'video'},
            {'name': 'DailyMotion', 'url': 'https://dailymotion.com/{username}', 'type': 'video'},
            {'name': 'Vine', 'url': 'https://vine.co/{username}', 'type': 'video'},
            
            # Forum & Discussion
            {'name': 'Reddit', 'url': 'https://reddit.com/user/{username}', 'type': 'forum'},
            {'name': 'Quora', 'url': 'https://quora.com/profile/{username}', 'type': 'forum'},
            {'name': 'StackOverflow', 'url': 'https://stackoverflow.com/users/{username}', 'type': 'forum'},
            {'name': 'HackerNews', 'url': 'https://news.ycombinator.com/user?id={username}', 'type': 'forum'},
            {'name': 'Pastebin', 'url': 'https://pastebin.com/u/{username}', 'type': 'forum'},
            {'name': 'XDA', 'url': 'https://xdaforums.com/member/{username}', 'type': 'forum'},
            
            # Blog
            {'name': 'Medium', 'url': 'https://medium.com/@{username}', 'type': 'blog'},
            {'name': 'Substack', 'url': 'https://substack.com/@{username}', 'type': 'blog'},
            {'name': 'WordPress', 'url': 'https://wordpress.com/{username}', 'type': 'blog'},
            {'name': 'Blogger', 'url': 'https://blogger.com/{username}', 'type': 'blog'},
            {'name': 'Ghost', 'url': 'https://ghost.org/{username}', 'type': 'blog'},
            {'name': 'Dev.to', 'url': 'https://dev.to/{username}', 'type': 'blog'},
            {'name': 'Hashnode', 'url': 'https://hashnode.com/@{username}', 'type': 'blog'},
            
            # Audio
            {'name': 'Spotify', 'url': 'https://open.spotify.com/user/{username}', 'type': 'audio'},
            {'name': 'SoundCloud', 'url': 'https://soundcloud.com/{username}', 'type': 'audio'},
            {'name': 'Mixcloud', 'url': 'https://mixcloud.com/{username}', 'type': 'audio'},
            {'name': 'Audiomack', 'url': 'https://audiomack.com/{username}', 'type': 'audio'},
            {'name': 'Bandcamp', 'url': 'https://bandcamp.com/{username}', 'type': 'audio'},
            
            # Photo & Art
            {'name': 'Flickr', 'url': 'https://flickr.com/people/{username}', 'type': 'photo'},
            {'name': '500px', 'url': 'https://500px.com/{username}', 'type': 'photo'},
            {'name': 'Unsplash', 'url': 'https://unsplash.com/@{username}', 'type': 'photo'},
            {'name': 'DeviantArt', 'url': 'https://deviantart.com/{username}', 'type': 'photo'},
            {'name': 'ArtStation', 'url': 'https://artstation.com/{username}', 'type': 'photo'},
            {'name': 'Dribbble', 'url': 'https://dribbble.com/{username}', 'type': 'photo'},
            {'name': 'Behance', 'url': 'https://behance.net/{username}', 'type': 'photo'},
            
            # Gaming
            {'name': 'Steam', 'url': 'https://steamcommunity.com/id/{username}', 'type': 'gaming'},
            {'name': 'PlayStation', 'url': 'https://playstation.com/{username}', 'type': 'gaming'},
            {'name': 'Xbox', 'url': 'https://xbox.com/{username}', 'type': 'gaming'},
            {'name': 'Nintendo', 'url': 'https://nintendo.com/{username}', 'type': 'gaming'},
            {'name': 'EpicGames', 'url': 'https://epicgames.com/{username}', 'type': 'gaming'},
            {'name': 'RiotGames', 'url': 'https://riotgames.com/{username}', 'type': 'gaming'},
            {'name': 'BattleNet', 'url': 'https://battlenet.com/{username}', 'type': 'gaming'},
            {'name': 'Origin', 'url': 'https://origin.com/{username}', 'type': 'gaming'},
            
            # Chat & Messaging
            {'name': 'Telegram', 'url': 'https://t.me/{username}', 'type': 'chat'},
            {'name': 'Discord', 'url': 'https://discord.com/users/{username}', 'type': 'chat'},
            {'name': 'WhatsApp', 'url': 'https://wa.me/{username}', 'type': 'chat'},
            {'name': 'Line', 'url': 'https://line.me/{username}', 'type': 'chat'},
            {'name': 'KakaoTalk', 'url': 'https://kakao.com/{username}', 'type': 'chat'},
            {'name': 'WeChat', 'url': 'https://wechat.com/{username}', 'type': 'chat'},
            {'name': 'Signal', 'url': 'https://signal.org/{username}', 'type': 'chat'},
            {'name': 'Kik', 'url': 'https://kik.com/{username}', 'type': 'chat'},
            {'name': 'Viber', 'url': 'https://viber.com/{username}', 'type': 'chat'},
            
            # Coding & Developer
            {'name': 'GitHub', 'url': 'https://github.com/{username}', 'type': 'coding'},
            {'name': 'GitLab', 'url': 'https://gitlab.com/{username}', 'type': 'coding'},
            {'name': 'Bitbucket', 'url': 'https://bitbucket.org/{username}', 'type': 'coding'},
            {'name': 'CodePen', 'url': 'https://codepen.io/{username}', 'type': 'coding'},
            {'name': 'Replit', 'url': 'https://replit.com/@{username}', 'type': 'coding'},
            {'name': 'LeetCode', 'url': 'https://leetcode.com/{username}', 'type': 'coding'},
            {'name': 'HackerRank', 'url': 'https://hackerrank.com/{username}', 'type': 'coding'},
            {'name': 'Codeforces', 'url': 'https://codeforces.com/profile/{username}', 'type': 'coding'},
            
            # Professional
            {'name': 'Keybase', 'url': 'https://keybase.io/{username}', 'type': 'coding'},
            {'name': 'HackTheBox', 'url': 'https://hackthebox.eu/home/users/profile/{username}', 'type': 'coding'},
            {'name': 'TryHackMe', 'url': 'https://tryhackme.com/p/{username}', 'type': 'coding'},
            
            # Email
            {'name': 'ProtonMail', 'url': 'https://protonmail.com/{username}', 'type': 'email'},
            {'name': 'GMX', 'url': 'https://gmx.com/{username}', 'type': 'email'},
            {'name': 'Yandex', 'url': 'https://yandex.ru/{username}', 'type': 'email'},
            {'name': 'MailRu', 'url': 'https://mail.ru/{username}', 'type': 'email'},
            
            # Cloud
            {'name': 'GoogleDrive', 'url': 'https://drive.google.com/{username}', 'type': 'storage'},
            {'name': 'Dropbox', 'url': 'https://dropbox.com/{username}', 'type': 'storage'},
            {'name': 'OneDrive', 'url': 'https://onedrive.com/{username}', 'type': 'storage'},
            {'name': 'Mega', 'url': 'https://mega.nz/{username}', 'type': 'storage'}
        ]
        
    async def _check_site(self, name, url, platform_type):
        try:
            async with self.session.head(
                url,
                allow_redirects=False,
                timeout=10
            ) as resp:
                exists = resp.status < 400
                return (name, url, exists, platform_type)
        except:
            return (name, url, False, platform_type)
