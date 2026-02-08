import subprocess
import sys

def install():
    # Force pip to find binary wheels to avoid compilation
    # Kivy 2.3.0+ supports Python 3.12
    cmd = [
        sys.executable, "-m", "pip", "install", 
        "kivy>=2.3.0", "kivymd", 
        "--only-binary", ":all:", 
        "--extra-index-url", "https://kivy.org/downloads/simple/"
    ]
    
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    
    if result.returncode != 0:
        print("First attempt failed. Trying without specific index...")
        cmd = [
            sys.executable, "-m", "pip", "install", 
            "kivy>=2.3.0", "kivymd", 
            "--only-binary", ":all:"
        ]
        print("Running:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        print(result.stderr)

if __name__ == "__main__":
    install()
