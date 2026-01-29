import discord
import asyncio
import aiohttp
import random
import time
from colorama import init, Fore, Style
import json
from concurrent.futures import ThreadPoolExecutor
import threading

init(autoreset=True)

class MassDMSpammer:
    def __init__(self, tokens_file, targets_file, proxies_file=None):
        self.tokens = self.load_tokens(tokens_file)
        self.targets = self.load_targets(targets_file)
        self.proxies = self.load_proxies(proxies_file) if proxies_file else None
        self.stats = {'sent': 0, 'failed': 0, 'active_bots': len(self.tokens)}
        self.running = False
        
    def load_tokens(self, filename):
        with open(filename, 'r') as f:
            tokens = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"{Fore.GREEN}✅ Loaded {len(tokens)} bot tokens")
        return tokens
    
    def load_targets(self, filename):
        with open(filename, 'r') as f:
            targets = [int(line.strip()) for line in f if line.strip().isdigit()]
        print(f"{Fore.GREEN}✅ Loaded {len(targets)} targets")
        return targets
    
    def load_proxies(self, filename):
        with open(filename, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        print(f"{Fore.GREEN}✅ Loaded {len(proxies)} proxies")
        return proxies
    
    async def send_dm(self, token, target_id, message, proxy=None):
        """Send DM via raw API (bypasses rate limits)"""
        try:
            url = "https://discord.com/api/v9/users/@me/channels"
            headers = {
                "Authorization": token,
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            # Create DM channel
            payload = {"recipient_id": str(target_id)}
            connector = aiohttp.TCPConnector()
            if proxy:
                connector = aiohttp.TCPConnector(proxy=f"http://{proxy}")
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        channel = await resp.json()
                        channel_id = channel['id']
                        
                        # Send message
                        msg_payload = {"content": message}
                        async with session.post(
                            f"https://discord.com/api/v9/channels/{channel_id}/messages",
                            headers=headers, json=msg_payload
                        ) as msg_resp:
                            if msg_resp.status == 200:
                                self.stats['sent'] += 1
                                return True
            return False
        except:
            self.stats['failed'] += 1
            return False
    
    async def bot_worker(self, token, targets_batch, message, proxy=None):
        """Single bot spammer"""
        for target in targets_batch:
            if self.running:
                success = await self.send_dm(token, target, message, proxy)
                delay = random.uniform(0.5, 2.0)  # Human-like delay
                await asyncio.sleep(delay)
    
    def print_stats(self):
        """Live stats"""
        while self.running:
            total = self.stats['sent'] + self.stats['failed']
            success_rate = (self.stats['sent'] / total * 100) if total > 0 else 0
            print(f"{Fore.CYAN}[STATS] Sent: {self.stats['sent']} | Failed: {self.stats['failed']} | Rate: {success_rate:.1f}% | Bots: {self.stats['active_bots']}", end='\r')
            time.sleep(2)
    
    async def start_spam(self, message):
        """Main spam function"""
        self.running = True
        print(f"{Fore.YELLOW}🚀 Starting mass DM with {len(self.tokens)} bots → {len(self.targets)} targets")
        print(f"{Fore.YELLOW}💬 Message: {message[:50]}...")
        
        # Stats thread
        stats_thread = threading.Thread(target=self.print_stats)
        stats_thread.daemon = True
        stats_thread.start()
        
        # Distribute targets
        targets_per_bot = len(self.targets) // len(self.tokens) + 1
        tasks = []
        
        for i, token in enumerate(self.tokens):
            bot_targets = self.targets[i*targets_per_bot:(i+1)*targets_per_bot]
            proxy = random.choice(self.proxies) if self.proxies else None
            
            task = asyncio.create_task(
                self.bot_worker(token, bot_targets, message, proxy)
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        self.running = False
        print(f"\n{Fore.GREEN}✅ Spam completed! {self.stats['sent']} successful DMs")

def main():
    print(f"{Fore.RED}🔥 MASS DM SPAMMER v2.0 - PENTEST EDITION")
    spammer = MassDMSpammer(
        tokens_file="tokens.txt",
        targets_file="targets.txt",
        proxies_file="proxies.txt"  # Optional
    )
    
    message = input(f"{Fore.YELLOW}Enter spam message: ")
    asyncio.run(spammer.start_spam(message))

if __name__ == "__main__":
    main()
