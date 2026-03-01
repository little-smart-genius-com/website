"""Test Pollinations API with BACKUP keys specifically."""
import asyncio, os, sys, time, urllib.parse, aiohttp
from io import BytesIO
from dotenv import load_dotenv

# Load .env from project root
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(env_path)
print(f"Loading .env from: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")

# Load BACKUP keys specifically
bck_keys = []
for i in range(1, 6):
    k = os.getenv(f"POLLINATIONS_API_KEY_BCK_{i}")
    if k and len(k) > 5:
        bck_keys.append(k)
        print(f"  BCK_{i}: {k[:8]}...{k[-4:]}")

# Also load primary keys for comparison
pri_keys = []
for i in range(1, 6):
    k = os.getenv(f"POLLINATIONS_API_KEY_{i}")
    if k and len(k) > 5:
        pri_keys.append(k)
        print(f"  PRI_{i}: {k[:8]}...{k[-4:]}")

print(f"\nBackup keys: {len(bck_keys)}")
print(f"Primary keys: {len(pri_keys)}")

prompt = "happy diverse children learning with colorful educational puzzle"
encoded = urllib.parse.quote(prompt)
seed = int(time.time())

async def test():
    async with aiohttp.ClientSession() as session:
        # Test each backup key individually
        for i, key in enumerate(bck_keys, 1):
            print(f"\n--- Testing BACKUP KEY {i}: {key[:8]}...{key[-4:]} ---")
            
            # Try gen.pollinations.ai
            url = f"https://gen.pollinations.ai/image/{encoded}"
            params = {
                "width": 512, "height": 288, 
                "model": "flux", "nologo": "true", 
                "enhance": "true", "seed": seed + i
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Authorization": f"Bearer {key}"
            }
            
            try:
                async with session.get(url, params=params, headers=headers,
                                        timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    print(f"  gen.pollinations.ai: HTTP {resp.status}")
                    if resp.status == 200:
                        data = await resp.read()
                        print(f"  Data: {len(data)} bytes")
                        if len(data) > 1024:
                            out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images', f'test_bck_{i}.webp')
                            from PIL import Image
                            img = Image.open(BytesIO(data)).convert("RGB")
                            img.save(out, "WEBP", quality=85)
                            print(f"  SAVED! {out}")
                            print(f"  >>> BACKUP KEY {i} WORKS! <<<")
                    else:
                        body = await resp.text()
                        print(f"  Response: {body[:200]}")
            except Exception as e:
                print(f"  Error: {e}")
            
            await asyncio.sleep(2)
            
            # Also try image.pollinations.ai with this key
            url2 = f"https://image.pollinations.ai/prompt/{encoded}"
            params2 = {"width": 512, "height": 288, "nologo": "true", "seed": seed + i + 10}
            headers2 = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Authorization": f"Bearer {key}"
            }
            
            try:
                async with session.get(url2, params=params2, headers=headers2,
                                        timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    print(f"  image.pollinations.ai: HTTP {resp.status}")
                    if resp.status == 200:
                        data = await resp.read()
                        print(f"  Data: {len(data)} bytes")
                        if len(data) > 1024:
                            out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images', f'test_bck_{i}_v2.webp')
                            from PIL import Image
                            img = Image.open(BytesIO(data)).convert("RGB")
                            img.save(out, "WEBP", quality=85)
                            print(f"  SAVED! {out}")
                            print(f"  >>> BACKUP KEY {i} on image.pollinations WORKS! <<<")
                    else:
                        body = await resp.text()
                        print(f"  Response: {body[:150]}")
            except Exception as e:
                print(f"  Error: {e}")
            
            await asyncio.sleep(2)

asyncio.run(test())
