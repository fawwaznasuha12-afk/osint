#!/usr/bin/env python3

import sys
import asyncio
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.tree import Tree
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text

from core.engine import Engine

console = Console()

class OSINTFramework:
    def __init__(self):
        self.engine = None
        self.current_target = None
        self.current_module = None
        self.depth = 2
        self.scan_results = {}
        self.modules = ['email', 'username', 'domain', 'phone', 'image', 'crypto']

    def show_help(self):
        console.print("""
[cyan]Core Commands[/cyan]
  help                 Show this help menu
  exit                 Exit OSINT
  clear                Clear screen
  show modules         List available modules
  show options         Show current module options
  show reports         List saved reports

[cyan]Module Commands[/cyan]
  use <module>         Select module (email, username, domain, phone, image, crypto)
  set TARGET <target>  Set target
  set DEPTH <1-3>      Set crypto depth (default: 2)
  run                  Run scan with current module and target
  info                 Show module information
                """)

    async def start(self):
        console.clear()
        console.print(Panel("OSINT", border_style="cyan", width=30))
        console.print("Type 'help' for commands\n")

        async with Engine() as engine:
            self.engine = engine

            while True:
                try:
                    if self.current_module:
                        prompt = f"osint({self.current_module})> "
                    else:
                        prompt = "osint> "

                    cmd = Prompt.ask(prompt)

                    if not cmd or cmd.strip() == '':
                        continue

                    await self.execute(cmd)

                except KeyboardInterrupt:
                    console.print("\n[red]Interrupted[/red]")
                    continue

    async def execute(self, cmd):
        parts = cmd.split()
        if not parts:
            return

        command = parts[0].lower()

        if command == 'exit':
            console.print("[red]Exiting...[/red]")
            sys.exit(0)

        elif command == 'help':
            self.show_help()

        elif command == 'clear':
            console.clear()
            console.print(Panel("OSINT", border_style="cyan", width=30))

        elif command == 'show':
            if len(parts) < 2:
                console.print("[red]show what? modules, options, reports[/red]")
                return

            sub = parts[1].lower()

            if sub == 'modules':
                console.print("[cyan]Available modules:[/cyan]")
                for m in self.modules:
                    console.print(f"  - {m}")

            elif sub == 'options':
                if not self.current_module:
                    console.print("[red]No module selected. Use: use <module>[/red]")
                    return
                console.print(f"[cyan]Options for {self.current_module}:[/cyan]")
                console.print(f"  TARGET  => {self.current_target or '(not set)'}")
                if self.current_module == 'crypto':
                    console.print(f"  DEPTH   => {self.depth}")

            elif sub == 'reports':
                reports = os.listdir('reports') if os.path.exists('reports') else []
                if reports:
                    console.print("[green]Reports:[/green]")
                    for r in reports:
                        console.print(f"  - {r}")
                else:
                    console.print("[yellow]No reports found[/yellow]")

            else:
                console.print(f"[red]Unknown: show {sub}[/red]")

        elif command == 'use':
            if len(parts) < 2:
                console.print("[red]Usage: use <module>[/red]")
                return

            module = parts[1].lower()

            if module in self.modules:
                self.current_module = module
                console.print(f"[green]Module {module} loaded[/green]")
            else:
                console.print(f"[red]Module {module} not found[/red]")
                console.print(f"[cyan]Available: {', '.join(self.modules)}[/cyan]")

        elif command == 'set':
            if len(parts) < 3:
                console.print("[red]Usage: set <option> <value>[/red]")
                return

            option = parts[1].upper()
            value = ' '.join(parts[2:])

            if option == 'TARGET':
                self.current_target = value
                console.print(f"[green]TARGET => {value}[/green]")

            elif option == 'DEPTH':
                if value.isdigit() and 1 <= int(value) <= 3:
                    self.depth = int(value)
                    console.print(f"[green]DEPTH => {value}[/green]")
                else:
                    console.print("[red]DEPTH must be 1-3[/red]")

            else:
                console.print(f"[red]Unknown option: {option}[/red]")
                console.print("[cyan]Options: TARGET, DEPTH[/cyan]")

        elif command == 'unset':
            if len(parts) < 2:
                console.print("[red]Usage: unset <option>[/red]")
                return

            option = parts[1].upper()

            if option == 'TARGET':
                self.current_target = None
                console.print("[green]TARGET unset[/green]")
            elif option == 'DEPTH':
                self.depth = 2
                console.print("[green]DEPTH reset to 2[/green]")
            else:
                console.print(f"[red]Unknown option: {option}[/red]")

        elif command == 'run':
            if not self.current_target:
                console.print("[red]No target set. Use: set TARGET <target>[/red]")
                return

            if not self.current_module:
                console.print("[red]No module selected. Use: use <module>[/red]")
                return

            await self._run_scan(self.current_module, self.current_target)

        elif command == 'info':
            if not self.current_module:
                console.print("[red]No module selected. Use: use <module>[/red]")
                return

            console.print(f"""
[cyan]Module: {self.current_module}[/cyan]
[cyan]Description:[/cyan]
  {self._get_module_desc(self.current_module)}
[cyan]Options:[/cyan]
  TARGET  - Target to scan (required)
  DEPTH   - Transaction depth for crypto (1-3, default: 2)
            """)

        else:
            console.print(f"[red]Unknown command: {command}. Type 'help' for list.[/red]")

    def _get_module_desc(self, module):
        desc = {
            'email': 'Email OSINT - Validate email, check breaches, find social accounts',
            'username': 'Username OSINT - Check 100+ platforms for username existence',
            'domain': 'Domain OSINT - WHOIS, DNS, subdomain enumeration',
            'phone': 'Phone OSINT - Validate number, carrier, location, WhatsApp/Telegram check',
            'image': 'Image OSINT - Reverse image search, EXIF extraction',
            'crypto': 'Crypto OSINT - 15+ chain support, transaction tree visualization'
        }
        return desc.get(module, 'Module information not available')

    async def _run_scan(self, module, target, depth=None):
        console.print(f"\n[cyan]Scanning {target} with {module} module...[/cyan]")

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Running scan...", total=100)

                if module == 'crypto':
                    if depth is None:
                        depth = self.depth
                    result = await self.engine.run_module(module, target, depth)
                else:
                    result = await self.engine.run_module(module, target)

                progress.update(task, completed=100)

            self.scan_results = {module: result}

            if module == 'crypto':
                self.display_crypto_results(result)
            else:
                self.display_results(result, module)

            filename = self.engine.save_report(target, 'json')
            console.print(f"\n[green]Report saved: {filename}[/green]")

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

    def display_results(self, data, module):
        if isinstance(data, dict) and 'error' in data:
            console.print(f"[red]Error: {data['error']}[/red]")
            return

        table = Table(title=f"{module.upper()} RESULTS", box=box.ROUNDED)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        for key, value in data.items():
            if isinstance(value, list):
                if key == 'breaches' and value:
                    table.add_row(key, f"{len(value)} breaches found")
                elif key == 'social_accounts' and value:
                    accounts = ', '.join([a.get('platform', '') for a in value[:5]])
                    if len(value) > 5:
                        accounts += f" + {len(value)-5} more"
                    table.add_row(key, accounts)
                elif key == 'found' and value:
                    names = ', '.join([a.get('name', '') for a in value[:10]])
                    if len(value) > 10:
                        names += f" + {len(value)-10} more"
                    table.add_row(key, names)
                else:
                    table.add_row(key, f"{len(value)} items")
            elif isinstance(value, dict):
                table.add_row(key, f"{len(value)} entries")
            elif isinstance(value, bool):
                table.add_row(key, "[green]Yes[/green]" if value else "[red]No[/red]")
            else:
                table.add_row(key, str(value))

        console.print(table)

    def display_crypto_results(self, data):
        if isinstance(data, dict) and 'error' in data:
            console.print(f"[red]Error: {data['error']}[/red]")
            return

        table = Table(title="CRYPTO RESULTS", box=box.ROUNDED)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        for key, value in data.items():
            if key == 'tree':
                continue
            if isinstance(value, list):
                table.add_row(key, f"{len(value)} items")
            elif isinstance(value, dict):
                table.add_row(key, f"{len(value)} entries")
            elif isinstance(value, bool):
                table.add_row(key, "[green]Yes[/green]" if value else "[red]No[/red]")
            else:
                table.add_row(key, str(value))

        console.print(table)
        console.print("")

        tree_data = data.get('tree', {})
        root = tree_data.get('root', {})

        if root and root.get('children'):
            console.print(Panel("Transaction Tree", border_style="green"))
            tree = Tree(f"[bold green]{root.get('address', '')} (ROOT)")
            self.build_tree_visual(tree, root.get('children', []))
            console.print(tree)

    def build_tree_visual(self, tree, children, level=1):
        for child in children[:10]:
            address = child.get('address', '')[:20] + '...'
            amount = child.get('amount', 0)
            branch = tree.add(f"[yellow]{address} - {amount}")

            grand_children = child.get('children', [])
            if grand_children:
                self.build_tree_visual(branch, grand_children, level + 1)

            if len(children) > 10 and level == 1:
                tree.add(f"[dim]... and {len(children) - 10} more[/dim]")

async def main():
    framework = OSINTFramework()
    await framework.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted. Exiting...[/red]")
        sys.exit(0)
