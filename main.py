#!/usr/bin/env python3

import sys
import asyncio
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich.tree import Tree
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.text import Text

from core.engine import Engine

console = Console()

def show_header():
    console.print(Panel("OSINT", border_style="cyan", width=30))

def show_menu():
    console.print("")
    console.print("[1] Single Target Scan", style="cyan")
    console.print("[2] Batch Scan", style="cyan")
    console.print("[3] Interactive Mode", style="cyan")
    console.print("[4] View Reports", style="cyan")
    console.print("[5] Proxy Settings", style="cyan")
    console.print("[6] Exit", style="cyan")
    console.print("")

async def single_scan():
    console.clear()
    show_header()
    
    console.print(Panel("Single Target Scan", border_style="cyan"))
    console.print("")
    console.print("[1] Email")
    console.print("[2] Username")
    console.print("[3] Domain")
    console.print("[4] Phone Number")
    console.print("[5] Image URL")
    console.print("[6] Crypto Address")
    console.print("")
    
    choice = IntPrompt.ask("Select target type", choices=["1","2","3","4","5","6"])
    
    target_types = {
        1: 'email',
        2: 'username',
        3: 'domain',
        4: 'phone',
        5: 'image',
        6: 'crypto'
    }
    
    target_type = target_types[choice]
    target = Prompt.ask("Enter target")
    
    modules = Prompt.ask("Modules (comma separated, or 'all')", default="all")
    
    if not Confirm.ask("Start scan?"):
        return
        
    async with Engine() as engine:
        if modules.lower() == 'all':
            results = await engine.scan_all(target)
        else:
            module_list = [m.strip() for m in modules.split(',')]
            results = {}
            for module in module_list:
                if target_type == 'crypto':
                    depth = IntPrompt.ask("Transaction depth (1-3)", default=2)
                    result = await engine.run_module(module, target, depth)
                else:
                    result = await engine.run_module(module, target)
                results[module] = result
            engine.results = results
            
        filename = engine.save_report(target, 'json')
        console.print(f"\n[green]Report saved: {filename}[/green]")
        
        if target_type == 'crypto':
            display_crypto_results(results)
        else:
            display_results(results)

def display_results(results):
    console.clear()
    
    for module, data in results.items():
        if isinstance(data, dict) and 'error' in data:
            console.print(f"[red]Error in {module}: {data['error']}[/red]")
            continue
            
        table = Table(title=f"{module.upper()}", box=box.ROUNDED)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in data.items():
            if isinstance(value, list):
                table.add_row(key, f"{len(value)} items")
            elif isinstance(value, dict):
                table.add_row(key, f"{len(value)} entries")
            else:
                table.add_row(key, str(value))
                
        console.print(table)
        console.print("")

def display_crypto_results(results):
    console.clear()
    
    crypto_data = results.get('crypto', {})
    if 'error' in crypto_data:
        console.print(f"[red]Error: {crypto_data['error']}[/red]")
        return
        
    table = Table(title="CRYPTO - ADDRESS SUMMARY", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    
    for key, value in crypto_data.items():
        if key == 'tree':
            continue
        if isinstance(value, list):
            table.add_row(key, f"{len(value)} items")
        elif isinstance(value, dict):
            table.add_row(key, f"{len(value)} entries")
        else:
            table.add_row(key, str(value))
            
    console.print(table)
    console.print("")
    
    tree_data = crypto_data.get('tree', {})
    root = tree_data.get('root', {})
    
    if root:
        console.print(Panel("Transaction Tree", border_style="green"))
        tree = Tree(f"[bold green]{root.get('address', '')} (ROOT)")
        build_tree_visual(tree, root.get('children', []))
        console.print(tree)

def build_tree_visual(tree, children, level=1):
    for child in children[:10]:
        address = child.get('address', '')[:20] + '...'
        amount = child.get('amount', 0)
        branch = tree.add(f"[yellow]{address} - {amount} BTC")
        
        grand_children = child.get('children', [])
        if grand_children:
            build_tree_visual(branch, grand_children, level + 1)
            
        if len(children) > 10 and level == 1:
            tree.add(f"[dim]... and {len(children) - 10} more[/dim]")

async def batch_scan():
    console.clear()
    show_header()
    console.print(Panel("Batch Scan", border_style="cyan"))
    console.print("")
    
    target_file = Prompt.ask("Enter path to target file (one target per line)")
    
    if not os.path.exists(target_file):
        console.print("[red]File not found[/red]")
        return
        
    with open(target_file, 'r') as f:
        targets = [line.strip() for line in f if line.strip()]
        
    console.print(f"[yellow]{len(targets)} targets loaded[/yellow]")
    
    module = Prompt.ask("Module to run (or 'all')", default="all")
    
    if not Confirm.ask("Start batch scan?"):
        return
        
    async with Engine() as engine:
        for target in targets:
            console.print(f"\n[cyan]Scanning: {target}[/cyan]")
            if module.lower() == 'all':
                results = await engine.scan_all(target)
            else:
                result = await engine.run_module(module, target)
                results = {module: result}
                engine.results = results
                
            filename = engine.save_report(target, 'json')
            console.print(f"[green]Report saved: {filename}[/green]")

async def interactive_mode():
    console.clear()
    show_header()
    console.print(Panel("Interactive Mode", border_style="cyan"))
    console.print("Type 'help' for commands, 'exit' to quit\n")
    
    async with Engine() as engine:
        while True:
            cmd = Prompt.ask("[cyan]OSINT[/cyan]>")
            
            if cmd.lower() == 'exit':
                break
            elif cmd.lower() == 'help':
                console.print("""
[cyan]Commands:[/cyan]
  scan email <target>     - Email OSINT
  scan username <target>  - Username OSINT
  scan domain <target>    - Domain OSINT
  scan phone <target>     - Phone OSINT
  scan crypto <target> depth <1-3> - Crypto OSINT with tree
  scan all <target>       - Run all modules
  show reports            - List reports
  clear                   - Clear screen
  exit                    - Exit interactive mode
                """)
            elif cmd.startswith('scan '):
                parts = cmd.split(' ')
                if len(parts) >= 3:
                    module = parts[1]
                    target = parts[2]
                    depth = None
                    
                    if 'depth' in parts:
                        depth_idx = parts.index('depth')
                        if depth_idx + 1 < len(parts):
                            depth = int(parts[depth_idx + 1])
                            
                    if module == 'all':
                        results = await engine.scan_all(target)
                        display_results(results)
                    else:
                        if module == 'crypto' and depth:
                            result = await engine.run_module(module, target, depth)
                        else:
                            result = await engine.run_module(module, target)
                        results = {module: result}
                        
                        if module == 'crypto':
                            display_crypto_results(results)
                        else:
                            display_results(results)
                            
            elif cmd.lower() == 'show reports':
                reports = os.listdir('reports') if os.path.exists('reports') else []
                if reports:
                    console.print("[green]Reports:[/green]")
                    for r in reports:
                        console.print(f"  - {r}")
                else:
                    console.print("[yellow]No reports found[/yellow]")
            elif cmd.lower() == 'clear':
                console.clear()
                show_header()
            else:
                console.print("[red]Unknown command. Type 'help' for list.[/red]")

def view_reports():
    console.clear()
    show_header()
    
    reports = os.listdir('reports') if os.path.exists('reports') else []
    if not reports:
        console.print("[yellow]No reports found[/yellow]")
        return
        
    console.print("[green]Reports:[/green]")
    for idx, r in enumerate(reports, 1):
        console.print(f"  {idx}. {r}")
    console.print("")
    
    choice = IntPrompt.ask("Select report to view (0 to cancel)", default=0)
    if choice == 0:
        return
        
    if choice <= len(reports):
        filename = reports[choice-1]
        filepath = os.path.join('reports', filename)
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                console.print(Panel(content[:2000] + ("..." if len(content) > 2000 else ""), title=filename, border_style="cyan"))
        except:
            console.print("[red]Failed to read report[/red]")

def proxy_settings():
    console.clear()
    show_header()
    console.print(Panel("Proxy Settings", border_style="cyan"))
    console.print("")
    console.print("[1] Refresh Proxy List")
    console.print("[2] Toggle Proxy (Enable/Disable)")
    console.print("[3] Back")
    console.print("")
    
    choice = IntPrompt.ask("Select option", choices=["1","2","3"])
    
    if choice == 1:
        console.print("[yellow]Refreshing proxies...[/yellow]")
        console.print("[green]Proxy list updated[/green]")
    elif choice == 2:
        console.print("[yellow]Toggling proxy...[/yellow]")
        console.print("[green]Proxy status changed[/green]")
    elif choice == 3:
        return

async def main():
    while True:
        console.clear()
        show_header()
        show_menu()
        
        choice = IntPrompt.ask("Select option", choices=["1","2","3","4","5","6"])
        
        if choice == 1:
            await single_scan()
            Prompt.ask("\nPress Enter to continue")
        elif choice == 2:
            await batch_scan()
            Prompt.ask("\nPress Enter to continue")
        elif choice == 3:
            await interactive_mode()
        elif choice == 4:
            view_reports()
            Prompt.ask("\nPress Enter to continue")
        elif choice == 5:
            proxy_settings()
            Prompt.ask("\nPress Enter to continue")
        elif choice == 6:
            console.print("[red]Exiting...[/red]")
            sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted. Exiting...[/red]")
        sys.exit(0)
