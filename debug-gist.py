import os

print("🔍 Dumping environment variables containing 'GIST' or 'TOKEN'...\n")
for key, value in os.environ.items():
    if "GIST" in key or "TOKEN" in key:
        print(f"{key} = {value[:6]}... (truncated)")
