from pathlib import Path
import os

env_path = Path(__file__).parent / '.env'
print(f"Looking for .env at: {env_path}")
print(f"Exists: {env_path.exists()}")

if env_path.exists():
    with open(env_path, 'r') as f:
        lines = f.readlines()
        print(f"Lines in file: {len(lines)}")
        for i, line in enumerate(lines):
            print(f"Line {i}: {repr(line)}")
            if line.startswith('DISCORD_TOKEN='):
                token = line.strip().split('=', 1)[1]
                print(f"Found token: {token}")
