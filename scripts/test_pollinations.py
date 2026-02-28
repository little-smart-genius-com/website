"""Quick test of Pollinations with exact V6 URL format."""
import asyncio, aiohttp, os, re, sys, time, urllib.parse
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

KEYS = [os.getenv(f"POLLINATIONS_API_KEY_{i}") for i in range(1, 6)]
KEYS = [k for k in KEYS if k and len(k) > 5]
print(f"Keys found: {len(KEYS)}")

async def test():
    prompt = "Happy children learning with colorful puzzle pieces, bright classroom, 3D Pixar style"
    clean = re.sub(r'[^a-zA-Z0-9 ,.-]', '', prompt)
    encoded = urllib.parse.quote(clean)
    url = f"https://gen.pollinations.ai/image/{encoded}"
    params = {"width": 1200, "height": 675, "seed": 42, "model": "klein-large", "nologo": "true", "enhance": "true"}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if KEYS:
        headers["Authorization"] = f"Bearer {KEYS[0]}"

    print(f"URL: {url}")
    print(f"Params: {params}")
    print(f"Auth: {'yes' if KEYS else 'no'}")

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=90)) as resp:
            print(f"Status: {resp.status}")
            if resp.status == 200:
                data = await resp.read()
                print(f"Data size: {len(data)} bytes")
                if len(data) > 1024:
                    img = Image.open(BytesIO(data)).convert("RGB")
                    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images', 'test_pollinations.webp')
                    img.save(out_path, "WEBP", quality=85)
                    print(f"SAVED: {out_path}")
                    print("SUCCESS!")
                else:
                    print("FAIL: data too small")
            else:
                text = await resp.text()
                print(f"FAIL: {text[:200]}")

asyncio.run(test())
