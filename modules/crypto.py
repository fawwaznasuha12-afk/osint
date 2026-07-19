import aiohttp
import asyncio
from typing import Dict, List
from modules.base import BaseModule

class CryptoOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        self.tx_cache = {}
        
    async def scan(self, address: str, depth: int = 2) -> Dict:
        address = address.strip()
        
        if len(address) >= 26 and len(address) <= 34 and address[0] in ['1', '3']:
            return await self._scan_bitcoin(address, depth)
        elif address.startswith('0x') and len(address) == 42:
            return await self._scan_ethereum(address, depth)
        else:
            return {'error': 'Unsupported or invalid address format'}
            
    async def _scan_bitcoin(self, address: str, depth: int) -> Dict:
        results = {
            'address': address,
            'type': 'bitcoin',
            'balance': 0,
            'total_received': 0,
            'total_sent': 0,
            'transaction_count': 0,
            'tree': {
                'depth': depth,
                'root': {
                    'address': address,
                    'level': 0,
                    'children': []
                }
            },
            'flags': [],
            'exchange_wallets': []
        }
        
        try:
            async with self.session.get(
                f"https://blockchain.info/rawaddr/{address}"
            ) as resp:
                data = await resp.json()
                
                results['balance'] = data.get('final_balance', 0) / 100000000
                results['total_received'] = data.get('total_received', 0) / 100000000
                results['total_sent'] = data.get('total_sent', 0) / 100000000
                results['transaction_count'] = data.get('n_tx', 0)
                
                txs = data.get('txs', [])[:50]
                
                children = await self._build_tree(txs, address, depth, 1)
                results['tree']['root']['children'] = children
                
                results['flags'] = await self._detect_flags(results)
                results['exchange_wallets'] = await self._detect_exchange(results)
                
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def _scan_ethereum(self, address: str, depth: int) -> Dict:
        results = {
            'address': address,
            'type': 'ethereum',
            'balance': 0,
            'total_received': 0,
            'total_sent': 0,
            'transaction_count': 0,
            'tree': {
                'depth': depth,
                'root': {
                    'address': address,
                    'level': 0,
                    'children': []
                }
            },
            'flags': [],
            'exchange_wallets': []
        }
        
        try:
            async with self.session.get(
                f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&sort=asc"
            ) as resp:
                data = await resp.json()
                
                if data.get('status') == '1':
                    txs = data.get('result', [])[:50]
                    results['transaction_count'] = len(txs)
                    
                    balance = 0
                    for tx in txs:
                        if tx['to'].lower() == address.lower():
                            balance += int(tx['value']) / 10**18
                        elif tx['from'].lower() == address.lower():
                            balance -= int(tx['value']) / 10**18
                            
                    results['balance'] = balance
                    results['total_received'] = sum(int(tx['value']) for tx in txs if tx['to'].lower() == address.lower()) / 10**18
                    results['total_sent'] = sum(int(tx['value']) for tx in txs if tx['from'].lower() == address.lower()) / 10**18
                    
                    children = await self._build_eth_tree(txs, address, depth, 1)
                    results['tree']['root']['children'] = children
                    
                    results['flags'] = await self._detect_flags(results)
                    results['exchange_wallets'] = await self._detect_exchange(results)
                    
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def _build_tree(self, txs, root_address, depth, current_level):
        if current_level > depth:
            return []
            
        children = []
        seen = set()
        
        for tx in txs:
            inputs = tx.get('inputs', [])
            outputs = tx.get('out', [])
            
            for inp in inputs:
                prev_addr = inp.get('prev_out', {}).get('addr', '')
                if prev_addr and prev_addr != root_address and prev_addr not in seen:
                    seen.add(prev_addr)
                    child = {
                        'address': prev_addr,
                        'amount': inp.get('prev_out', {}).get('value', 0) / 100000000,
                        'level': current_level,
                        'children': []
                    }
                    if current_level < depth:
                        child['children'] = await self._fetch_tx_for_address(prev_addr, depth, current_level + 1, root_address)
                    children.append(child)
                    
            for out in outputs:
                addr = out.get('addr', '')
                if addr and addr != root_address and addr not in seen:
                    seen.add(addr)
                    child = {
                        'address': addr,
                        'amount': out.get('value', 0) / 100000000,
                        'level': current_level,
                        'children': []
                    }
                    if current_level < depth:
                        child['children'] = await self._fetch_tx_for_address(addr, depth, current_level + 1, root_address)
                    children.append(child)
                    
        return children
        
    async def _fetch_tx_for_address(self, address, depth, current_level, root_address):
        if current_level > depth:
            return []
            
        if address in self.tx_cache:
            txs = self.tx_cache[address]
        else:
            try:
                async with self.session.get(
                    f"https://blockchain.info/rawaddr/{address}"
                ) as resp:
                    data = await resp.json()
                    txs = data.get('txs', [])[:10]
                    self.tx_cache[address] = txs
            except:
                return []
                
        return await self._build_tree(txs, root_address, depth, current_level)
        
    async def _build_eth_tree(self, txs, root_address, depth, current_level):
        if current_level > depth:
            return []
            
        children = []
        seen = set()
        
        for tx in txs:
            from_addr = tx.get('from', '')
            to_addr = tx.get('to', '')
            value = int(tx.get('value', 0)) / 10**18
            
            if from_addr and from_addr != root_address and from_addr not in seen:
                seen.add(from_addr)
                child = {
                    'address': from_addr,
                    'amount': value,
                    'level': current_level,
                    'children': []
                }
                if current_level < depth:
                    child['children'] = await self._fetch_eth_tx_for_address(from_addr, depth, current_level + 1, root_address)
                children.append(child)
                
            if to_addr and to_addr != root_address and to_addr not in seen:
                seen.add(to_addr)
                child = {
                    'address': to_addr,
                    'amount': value,
                    'level': current_level,
                    'children': []
                }
                if current_level < depth:
                    child['children'] = await self._fetch_eth_tx_for_address(to_addr, depth, current_level + 1, root_address)
                children.append(child)
                
        return children
        
    async def _fetch_eth_tx_for_address(self, address, depth, current_level, root_address):
        if current_level > depth:
            return []
            
        try:
            async with self.session.get(
                f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&sort=asc"
            ) as resp:
                data = await resp.json()
                if data.get('status') == '1':
                    txs = data.get('result', [])[:10]
                    return await self._build_eth_tree(txs, root_address, depth, current_level)
        except:
            pass
        return []
        
    async def _detect_flags(self, data):
        flags = []
        
        if data.get('balance', 0) > 100:
            flags.append({
                'address': data['address'],
                'risk': 'High Balance',
                'confidence': 70
            })
            
        if data.get('transaction_count', 0) > 1000:
            flags.append({
                'address': data['address'],
                'risk': 'High Transaction Volume',
                'confidence': 85
            })
            
        return flags
        
    async def _detect_exchange(self, data):
        exchanges = ['binance', 'coinbase', 'kraken', 'bitfinex', 'huobi', 'okex', 'bittrex']
        found = []
        
        def check_address(addr):
            addr_lower = addr.lower()
            for exchange in exchanges:
                if exchange in addr_lower:
                    return exchange
            return None
            
        for child in data.get('tree', {}).get('root', {}).get('children', []):
            addr = child.get('address', '')
            exchange = check_address(addr)
            if exchange and addr not in found:
                found.append(addr)
                
        return found
