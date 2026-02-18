#!/usr/bin/env python3
"""
nuGAN Web Applet - Development Server Runner
Runs both Flask backend and Vite frontend concurrently.

Usage:
    python run.py          # Run both servers
    python run.py --setup  # Setup environments first, then run
"""

import os
import sys
import subprocess
import signal
import time
import argparse
from pathlib import Path
from shutil import which

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# ===================
# Configuration
# ===================
ROOT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
VENV_DIR = BACKEND_DIR / "venv"


# Environment variables for backend (set dynamically)
BACKEND_ENV = {}


# Ports (set dynamically)
BACKEND_PORT = int(os.environ.get("PORT", 5000))
# Allow overriding the listen host (use HOST or BACKEND_HOST). Default keeps previous behavior
BACKEND_HOST = os.environ.get("HOST", os.environ.get("BACKEND_HOST", "127.0.0.1"))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", 3000))
FRONTEND_HOST = os.environ.get("FRONTEND_HOST", "127.0.0.1")

# ===================
# Utility Functions
# ===================
def print_banner(mode):
    """Print startup banner."""
    print("\n" + "=" * 60)
    print(f"  νGAN Web Applet - {mode.title()} Server")
    print("=" * 60)
    print(f"  Backend:  http://{BACKEND_HOST}:{BACKEND_PORT}")
    print(f"  Frontend: http://{FRONTEND_HOST}:{FRONTEND_PORT}")
    print("=" * 60 + "\n")


def get_python_executable():
    """Get the Python executable from venv or system."""
    if sys.platform == "win32":
        venv_python = VENV_DIR / "Scripts" / "python.exe"
    else:
        venv_python = VENV_DIR / "bin" / "python"
    
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def get_npm_command():
    """Get npm command based on platform."""
    if sys.platform == "win32":
        return "npm.cmd"
    return "npm"


def setup_python_env():
    """Setup Python virtual environment and install dependencies."""
    print("[Python] Setting up virtual environment...")
    
    if not VENV_DIR.exists():
        print(f"[Python] Creating venv at {VENV_DIR}")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    
    python_exe = get_python_executable()
    pip_exe = str(VENV_DIR / ("Scripts" if sys.platform == "win32" else "bin") / "pip")
    
    # Upgrade pip
    print("[Python] Upgrading pip...")
    subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], 
                   check=True, capture_output=True)
    
    # Install requirements
    requirements_file = BACKEND_DIR / "requirements.txt"
    if requirements_file.exists():
        print("[Python] Installing requirements...")
        subprocess.run([pip_exe, "install", "-r", str(requirements_file)], check=True)
    
    print("[Python] ✓ Environment ready\n")


def setup_node_env():
    """Setup Node.js environment and install dependencies."""
    print("[Node.js] Installing dependencies...")
    
    npm = get_npm_command()
    node_modules = FRONTEND_DIR / "node_modules"
    
    if not node_modules.exists():
        subprocess.run([npm, "install"], cwd=FRONTEND_DIR, check=True)
    else:
        print("[Node.js] node_modules exists, skipping install")
    
    print("[Node.js] ✓ Environment ready\n")


def run_backend(dev_mode=True):
    """Start the backend server (Flask dev or Gunicorn prod)."""
    python_exe = get_python_executable()
    env = os.environ.copy()
    env.update(BACKEND_ENV)
    if dev_mode:
        print(f"[Backend] Starting Flask (dev) on {BACKEND_HOST}:{BACKEND_PORT}...")
        return subprocess.Popen(
            [python_exe, "-m", "flask", "run", f"--host={BACKEND_HOST}", f"--port={BACKEND_PORT}"],
            cwd=BACKEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    else:
        gunicorn_path = which("gunicorn")
        if not gunicorn_path:
            raise RuntimeError("[Backend] Gunicorn is not installed. Run 'pip install gunicorn'.")
        print(f"[Backend] Starting Gunicorn (prod) on {BACKEND_HOST}:{BACKEND_PORT}...")
        return subprocess.Popen(
            [gunicorn_path, "-w", "4", "-b", f"{BACKEND_HOST}:{BACKEND_PORT}", "wsgi:app"],
            cwd=ROOT_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )


def run_frontend(dev_mode=True):
    """Start the frontend dev server or serve static build."""
    npm = get_npm_command()
    env = os.environ.copy()
    env["FORCE_COLOR"] = "1"
    python_exe = get_python_executable()
    if dev_mode:
        print(f"[Frontend] Starting Vite (dev) on port {FRONTEND_PORT}...")
        return subprocess.Popen(
            [npm, "run", "dev"],
            cwd=FRONTEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=(sys.platform == "win32"),
        )
    else:
        # Serve static build using Python's http.server
        build_dir = FRONTEND_DIR / "build"
        if not build_dir.exists():
            print("[Frontend] No build found. Running 'npm run build'...")
            subprocess.run([npm, "run", "build"], cwd=FRONTEND_DIR, check=True)
        print(f"[Frontend] Serving static build on port {FRONTEND_PORT}...")
        return subprocess.Popen(
            [python_exe, "-m", "http.server", str(FRONTEND_PORT), "--directory", str(build_dir)],
            cwd=FRONTEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )


def stream_output(process, prefix, color_code):
    """Stream process output with prefix."""
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"\033[{color_code}m[{prefix}]\033[0m {line}", end='')
    except:
        pass


def main():
    parser = argparse.ArgumentParser(description="Run nuGAN servers (dev/prod)")
    parser.add_argument("--setup", action="store_true", help="Setup environments before running")
    parser.add_argument("--backend-only", action="store_true", help="Run only backend")
    parser.add_argument("--frontend-only", action="store_true", help="Run only frontend")
    parser.add_argument("--prod", action="store_true", help="Run in production mode")
    args = parser.parse_args()

    dev_mode = not args.prod

    # Load .env files
    if load_dotenv:
        env_file = (BACKEND_DIR / (".env.dev" if dev_mode else ".env.prod")).as_posix()
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
        env_file_front = (FRONTEND_DIR / (".env.dev" if dev_mode else ".env.prod")).as_posix()
        if os.path.exists(env_file_front):
            load_dotenv(env_file_front, override=True)

    # Set backend env for subprocess
    global BACKEND_ENV, BACKEND_PORT
    BACKEND_ENV = {
        "FLASK_APP": "app.py",
        "FLASK_ENV": os.environ.get("FLASK_ENV", "development" if dev_mode else "production"),
        "FLASK_DEBUG": os.environ.get("FLASK_DEBUG", "1" if dev_mode else "0"),
        "MODEL_DIR": str(BACKEND_DIR / "weights"),
        "PYTHONUNBUFFERED": "1",
        "PORT": os.environ.get("PORT", "5000"),
        "ALLOWED_ORIGINS": os.environ.get("ALLOWED_ORIGINS", "*"),
        "NUGAN_SEED": os.environ.get("NUGAN_SEED", "42"),
    }
    BACKEND_PORT = int(BACKEND_ENV["PORT"])

    # Setup if requested or if environments don't exist
    if args.setup or not VENV_DIR.exists():
        setup_python_env()
    if args.setup or not (FRONTEND_DIR / "node_modules").exists():
        setup_node_env()

    print_banner("production" if not dev_mode else "development")

    processes = []
    try:
        # Start servers
        if not args.frontend_only:
            backend_proc = run_backend(dev_mode=dev_mode)
            processes.append(("Backend", backend_proc, "34"))  # Blue
        if not args.backend_only:
            frontend_proc = run_frontend(dev_mode=dev_mode)
            processes.append(("Frontend", frontend_proc, "32"))  # Green

        # Stream output from both processes
        import threading
        threads = []
        for name, proc, color in processes:
            t = threading.Thread(target=stream_output, args=(proc, name, color), daemon=True)
            t.start()
            threads.append(t)

        print("\nPress Ctrl+C to stop servers...\n")

        # Wait for processes
        while True:
            for name, proc, _ in processes:
                if proc.poll() is not None:
                    print(f"\n[{name}] Process exited with code {proc.returncode}")
                    raise KeyboardInterrupt
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\nShutting down servers...")
        for name, proc, _ in processes:
            if proc.poll() is None:
                print(f"[{name}] Stopping...")
                if sys.platform == "win32":
                    proc.terminate()
                else:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                proc.wait(timeout=5)
        print("✓ All servers stopped")

if __name__ == "__main__":
    main()
