from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
required = [
    "app.py",
    "requirements.txt",
    "creatures.csv",
    "correct.wav",
    "wrong.wav",
    "rare.wav",
    "perfect.wav",
]

print("Flat repository check")
print("=====================")
ok = True
for item in required:
    p = BASE_DIR / item
    mark = "OK" if p.exists() else "MISSING"
    print(f"{mark:8} {item}")
    ok = ok and p.exists()

print()
print("All required files found." if ok else "Some required files are missing.")
