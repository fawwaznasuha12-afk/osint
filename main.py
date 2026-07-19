#!/usr/bin/env python3

import sys
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.table import Table
from rich.tree import Tree
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn

from core.engine import Engine

console = Console()

def show_banner():
    banner = """
    ██████╗ ███████╗██╗███╗   ██╗████████╗
    ██╔══██╗██╔════╝██║████╗  ██║╚══██╔══╝
    ██████╔╝███████╗██║██╔██╗ ██║   ██║
    ██╔══██╗╚════██║██║██║╚██╗██║   ██║
    ██║  ██║███████║██║██║ ╚████║   ██║
    ╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝
    
    OSINT FRAMEWORK
    Developed by VORTEX22
    """
    console.print(Panel(banner, border_style="cyan", width=60))

def show_menu():
    console.print("\n[1] Single Target Scan")
    console.print("[2] Batch Scan")
    console.print("[3] Interactive Mode")
    console.print("[4] View Reports")
    console.print("[5] Proxy Settings")
    console.print("[6] Exit")
    console.print("")

async def single_scan():
    console.clear()
    show_banner()
    
    console.print(Panel("SINGLE TARGET SCAN", border_style="cyan"))
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
            
        table = Table(title=f"{module.upper()} OSINT", box=box.ROUNDED)
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
        
    table = Table(title="CRYPTO OSINT - ADDRESS SUMMARY", box=box.ROUNDED)
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
        console.print(Panel("TRANSACTION TREE", border_style="green"))
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

async def interactive_mode():
    console.clear()
    show_banner()
    console.print(Panel("INTERACTIVE MODE", border_style="cyan"))
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
                import os
                reports = os.listdir('reports') if os.path.exists('reports') else []
                if reports:
                    console.print("[green]Reports:[/green]")
                    for r in reports:
                        console.print(f"  - {r}")
                else:
                    console.print("[yellow]No reports found[/yellow]")
            elif cmd.lower() == 'clear':
                console.clear()
                show_banner()
            else:
                console.print("[red]Unknown command. Type 'help' for list.[/red]")

async def main():
    while True:
        console.clear()
        show_banner()
        show_menu()
        
        choice = IntPrompt.ask("Select option", choices=["1","2","3","4","5","6"])
        
        if choice == 1:
            await single_scan()
            Prompt.ask("\nPress Enter to continue")
        elif choice == 2:
            console.print("[yellow]Batch scan coming soon[/yellow]")
            Prompt.ask("\nPress Enter to continue")
        elif choice == 3:
            await interactive_mode()
        elif choice == 4:
            import os
            reports = os.listdir('reports') if os.path.exists('reports') else []
            if reports:
                console.print("[green]Reports:[/green]")
                for r in reports:
                    console.print(f"  - {r}")
            else:
                console.print("[yellow]No reports found[/yellow]")
            Prompt.ask("\nPress Enter to continue")
        elif choice == 5:
            console.print("[yellow]Proxy settings coming soon[/yellow]")
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
