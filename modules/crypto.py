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
        
        # Bitcoin
        if len(address) >= 26 and len(address) <= 34 and address[0] in ['1', '3']:
            return await self._scan_bitcoin(address, depth)
        if address.startswith('bc1') and len(address) >= 42:
            return await self._scan_bitcoin(address, depth)
            
        # Ethereum / EVM
        if address.startswith('0x') and len(address) == 42:
            chain = await self._detect_evm_chain(address)
            return await self._scan_evm(address, depth, chain)
            
        # Solana
        if len(address) >= 32 and len(address) <= 44 and address[0] in ['G', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']:
            return await self._scan_solana(address, depth)
            
        # Tron
        if address.startswith('T') and len(address) == 34:
            return await self._scan_tron(address, depth)
            
        # Ripple (XRP)
        if address.startswith('r') and len(address) >= 33:
            return await self._scan_xrp(address, depth)
            
        # Cardano (ADA)
        if address.startswith('addr1') and len(address) >= 42:
            return await self._scan_cardano(address, depth)
            
        # Polkadot (DOT)
        if address.startswith('1') and len(address) >= 47:
            return await self._scan_polkadot(address, depth)
            
        # Cosmos (ATOM)
        if address.startswith('cosmos1') and len(address) >= 39:
            return await self._scan_cosmos(address, depth)
            
        # Near
        if len(address) >= 2 and '.' in address:
            return await self._scan_near(address, depth)
            
        # Algorand
        if len(address) == 58:
            return await self._scan_algorand(address, depth)
            
        # Stellar (XLM)
        if address.startswith('G') and len(address) == 56:
            return await self._scan_stellar(address, depth)
            
        return {'error': 'Unsupported or invalid address format'}
        
    async def _detect_evm_chain(self, address):
        try:
            async with self.session.get(
                f"https://api.etherscan.io/api?module=account&action=balance&address={address}"
            ) as resp:
                data = await resp.json()
                if data.get('status') == '1':
                    return 'ethereum'
        except:
            pass
            
        try:
            async with self.session.get(
                f"https://api.bscscan.com/api?module=account&action=balance&address={address}"
            ) as resp:
                data = await resp.json()
                if data.get('status') == '1':
                    return 'bsc'
        except:
            pass
            
        try:
            async with self.session.get(
                f"https://api.polygonscan.com/api?module=account&action=balance&address={address}"
            ) as resp:
                data = await resp.json()
                if data.get('status') == '1':
                    return 'polygon'
        except:
            pass
            
        return 'ethereum'
        
    async def _scan_bitcoin(self, address: str, depth: int) -> Dict:
        results = {
            'address': address,
            'chain': 'bitcoin',
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
        
    async def _scan_evm(self, address: str, depth: int, chain: str) -> Dict:
        results = {
            'address': address,
            'chain': chain,
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
        
        explorer_urls = {
            'ethereum': 'https://api.etherscan.io/api',
            'bsc': 'https://api.bscscan.com/api',
            'polygon': 'https://api.polygonscan.com/api',
            'avalanche': 'https://api.snowtrace.io/api',
            'arbitrum': 'https://api.arbiscan.io/api',
            'optimism': 'https://api-optimistic.etherscan.io/api',
            'fantom': 'https://api.ftmscan.com/api',
            'cronos': 'https://api.cronoscan.com/api'
        }
        
        base_url = explorer_urls.get(chain, 'https://api.etherscan.io/api')
        
        try:
            async with self.session.get(
                f"{base_url}?module=account&action=txlist&address={address}&sort=asc"
            ) as resp:
                data = await resp.json()
                
                if data.get('status') == '1':
                    txs = data.get('result', [])[:50]
                    results['transaction_count'] = len(txs)
                    
                    balance = 0
                    total_received = 0
                    total_sent = 0
                    for tx in txs:
                        value = int(tx['value']) / 10**18
                        if tx['to'].lower() == address.lower():
                            balance += value
                            total_received += value
                        elif tx['from'].lower() == address.lower():
                            balance -= value
                            total_sent += value
                            
                    results['balance'] = balance
                    results['total_received'] = total_received
                    results['total_sent'] = total_sent
                    
                    children = await self._build_eth_tree(txs, address, depth, 1)
                    results['tree']['root']['children'] = children
                    results['flags'] = await self._detect_flags(results)
                    results['exchange_wallets'] = await self._detect_exchange(results)
                    
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def _scan_solana(self, address: str, depth: int) -> Dict:
        results = {
            'address': address,
            'chain': 'solana',
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
            # Get balance
            async with self.session.post(
                "https://api.mainnet-beta.solana.com",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [address]
                }
            ) as resp:
                data = await resp.json()
                if 'result' in data:
                    results['balance'] = data['result']['value'] / 1000000000
                    
            # Get transactions
            async with self.session.post(
                "https://api.mainnet-beta.solana.com",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSignaturesForAddress",
                    "params": [address, {"limit": 50}]
                }
            ) as resp:
                data = await resp.json()
                if 'result' in data:
                    txs = data['result']
                    results['transaction_count'] = len(txs)
                    
                    # Get transaction details
                    children = []
                    seen = set()
                    for tx in txs[:20]:
                        sig = tx.get('signature', '')
                        if sig:
                            tx_detail = await self._get_solana_tx_detail(sig)
                            if tx_detail:
                                for acc in tx_detail.get('accountKeys', []):
                                    acc_addr = acc.get('pubkey', '')
                                    if acc_addr and acc_addr != address and acc_addr not in seen:
                                        seen.add(acc_addr)
                                        children.append({
                                            'address': acc_addr,
                                            'amount': 0,
                                            'level': 1,
                                            'children': []
                                        })
                                        
                    results['tree']['root']['children'] = children[:20]
                    results['flags'] = await self._detect_flags(results)
                    results['exchange_wallets'] = await self._detect_exchange(results)
                    
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def _get_solana_tx_detail(self, signature):
        try:
            async with self.session.post(
                "https://api.mainnet-beta.solana.com",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [signature, {"encoding": "jsonParsed"}]
                }
            ) as resp:
                data = await resp.json()
                if 'result' in data:
                    return data['result']
        except:
            pass
        return None
        
    async def _scan_tron(self, address: str, depth: int) -> Dict:
        results = {
            'address': address,
            'chain': 'tron',
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
                f"https://api.trongrid.io/v1/accounts/{address}"
            ) as resp:
                data = await resp.json()
                if 'data' in data and data['data']:
                    account = data['data'][0]
                    results['balance'] = account.get('balance', 0) / 1000000
                    results['total_received'] = account.get('total_received', 0) / 1000000
                    results['total_sent'] = account.get('total_sent', 0) / 1000000
                    results['transaction_count'] = account.get('transactions', 0)
                    
            async with self.session.get(
                f"https://api.trongrid.io/v1/accounts/{address}/transactions?limit=50"
            ) as resp:
                data = await resp.json()
                if 'data' in data:
                    children = []
                    seen = set()
                    for tx in data['data'][:20]:
                        raw_data = tx.get('raw_data', {})
                        contract = raw_data.get('contract', [{}])[0]
                        if contract:
                            value = contract.get('parameter', {}).get('value', {})
                            owner = value.get('owner_address', '')
                            to = value.get('to_address', '')
                            if owner and owner != address and owner not in seen:
                                seen.add(owner)
                                children.append({
                                    'address': owner,
                                    'amount': value.get('amount', 0) / 1000000,
                                    'level': 1,
                                    'children': []
                                })
                            if to and to != address and to not in seen:
                                seen.add(to)
                                children.append({
                                    'address': to,
                                    'amount': value.get('amount', 0) / 1000000,
                                    'level': 1,
                                    'children': []
                                })
                    results['tree']['root']['children'] = children[:20]
                    
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def _scan_xrp(self, address: str, depth: int) -> Dict:
        results = {
            'address': address,
            'chain': 'ripple',
            'balance': 0,
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
                f"https://api.xrpscan.com/api/v1/account/{address}"
            ) as resp:
                data = await resp.json()
                results['balance'] = data.get('balance', 0) / 1000000
                results['transaction_count'] = data.get('transactions', 0)
                
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def _scan_cardano(self, address: str, depth: int) -> Dict:
        results = {
            'address': address,
            'chain': 'cardano',
            'balance': 0,
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
                f"https://api.koios.rest/api/v1/address_info?_addresses={address}"
            ) as resp:
                data = await resp.json()
                if data and len(data) > 0:
                    results['balance'] = data[0].get('balance', 0) / 1000000
                    results['transaction_count'] = data[0].get('tx_count', 0)
                    
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def _scan_polkadot(self, address: str, depth: int) -> Dict:
        results = {
            'address': address,
            'chain': 'polkadot',
            'balance': 0,
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
            async with self.session.post(
                "https://api.polkadot.subscan.io/api/v1/scan/account",
                json={"address": address}
            ) as resp:
                data = await resp.json()
                if data.get('code') == 0:
                    results['balance'] = data['data'].get('balance', 0) / 10**10
                    results['transaction_count'] = data['data'].get('count', 0)
                    
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def _scan_cosmos(self, address: str, depth: int) -> Dict:
        results = {
            'address': address,
            'chain': 'cosmos',
            'balance': 0,
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
                f"https://api.cosmos.network/cosmos/bank/v1beta1/balances/{address}"
            ) as resp:
                data = await resp.json()
                if 'balances' in data:
                    for balance in data['balances']:
                        if balance['denom'] == 'uatom':
                            results['balance'] = int(balance['amount']) / 1000000
                            
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def _scan_near(self, address: str, depth: int) -> Dict:
        results = {
            'address': address,
            'chain': 'near',
            'balance': 0,
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
            async with self.session.post(
                "https://rpc.mainnet.near.org",
                json={
                    "jsonrpc": "2.0",
                    "id": "dontcare",
                    "method": "query",
                    "params": {
                        "request_type": "view_account",
                        "finality": "final",
                        "account_id": address
                    }
                }
            ) as resp:
                data = await resp.json()
                if 'result' in data:
                    results['balance'] = data['result'].get('amount', 0) / 10**24
                    
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def _scan_algorand(self, address: str, depth: int) -> Dict:
        results = {
            'address': address,
            'chain': 'algorand',
            'balance': 0,
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
                f"https://algoindexer.algoexplorerapi.io/v2/accounts/{address}"
            ) as resp:
                data = await resp.json()
                if 'account' in data:
                    results['balance'] = data['account'].get('amount', 0) / 1000000
                    results['transaction_count'] = data['account'].get('total-apps-opted-in', 0)
                    
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def _scan_stellar(self, address: str, depth: int) -> Dict:
        results = {
            'address': address,
            'chain': 'stellar',
            'balance': 0,
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
                f"https://horizon.stellar.org/accounts/{address}"
            ) as resp:
                data = await resp.json()
                if 'balances' in data:
                    for balance in data['balances']:
                        if balance['asset_type'] == 'native':
                            results['balance'] = float(balance['balance'])
                            break
                    results['transaction_count'] = data.get('subentry_count', 0)
                    
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
        exchanges = ['binance', 'coinbase', 'kraken', 'bitfinex', 'huobi', 'okex', 'bittrex', 'bybit', 'kucoin', 'gateio']
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
