import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

keys = []
for k, v in os.environ.items():
    if k.startswith("POLLINATIONS_API_KEY") and v and len(v) > 5:
        keys.append(v)

if not keys:
    print("❌ No Pollinations API keys found in .env")
    exit(1)

print(f"🔑 Found {len(keys)} Pollinations API keys. Testing until success...\n")

success_gpt = False
success_zimage = False

for i, key in enumerate(keys):
    print(f"\n--- Testing Key {i+1}/{len(keys)}: {key[:10]}... ---")
    headers = {"Authorization": f"Bearer {key}"}
    
    # 1. Test Balance
    balance_url = "https://gen.pollinations.ai/account/balance"
    try:
        res = requests.get(balance_url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            balance = data.get("balance", 0)
            print(f"💰 Balance: {balance}")
            if balance <= 0:
                print("⚠️ Balance is 0 or negative. Skipping models test for this key.")
                continue
        else:
            print(f"⚠️ Balance Check Failed: HTTP {res.status_code}")
            continue
    except Exception as e:
        print(f"❌ Error checking balance: {e}")
        continue

    # 2. Test flux model
    if not success_gpt:
        print("🎨 Testing model: flux...")
        gpt_url = "https://gen.pollinations.ai/image/a%20beautiful%20landscape?model=flux&width=512&height=512&nologo=true"
        try:
            res_gpt = requests.get(gpt_url, headers=headers, timeout=20)
            if res_gpt.status_code == 200 and len(res_gpt.content) > 1024:
                with open("test_flux.webp", "wb") as f:
                    f.write(res_gpt.content)
                print(f"✅ flux Success! ({len(res_gpt.content)} bytes)")
                success_gpt = True
            else:
                print(f"❌ flux Failed: HTTP {res_gpt.status_code}")
        except Exception as e:
            print(f"❌ Error testing flux: {e}")
            
    # 3. Test zimage model
    if not success_zimage:
        print("🎨 Testing model: zimage...")
        zimage_url = "https://gen.pollinations.ai/image/a%20beautiful%20portrait?model=zimage&width=512&height=512&nologo=true"
        try:
            res_z = requests.get(zimage_url, headers=headers, timeout=20)
            if res_z.status_code == 200 and len(res_z.content) > 1024:
                with open("test_zimage.webp", "wb") as f:
                    f.write(res_z.content)
                print(f"✅ zimage Success! ({len(res_z.content)} bytes)")
                success_zimage = True
            else:
                print(f"❌ zimage Failed: HTTP {res_z.status_code}")
        except Exception as e:
            print(f"❌ Error testing zimage: {e}")
            
    if success_gpt and success_zimage:
        print("\n🎉 Both models tested successfully!")
        break
        
    time.sleep(1)

if not success_gpt or not success_zimage:
    print("\n⚠️ Finished testing all keys, but did not get success for both models.")
