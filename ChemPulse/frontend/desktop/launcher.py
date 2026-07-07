from __future__ import annotations

import argparse
import atexit
import importlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import webview
from backend.core.paths import platform_app_data_dir

try:
    import psutil
except ImportError:  # pragma: no cover - psutil is installed with Reflex, but keep launcher defensive.
    psutil = None


DEFAULT_FRONTEND_PORT = 3000
DEFAULT_BACKEND_PORT = 8000
LOOPBACK_HOST = "127.0.0.1"
LAN_BIND_HOST = "0.0.0.0"


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        exe_parent = Path(sys.executable).resolve().parent
        source_repo_root = exe_parent.parent.parent
        if (source_repo_root / "rxconfig.py").exists() and (source_repo_root / "frontend").exists():
            return source_repo_root
        if (exe_parent / "runtime" / "python.exe").exists() or (exe_parent / "rxconfig.py").exists():
            return exe_parent
        internal_root = Path(getattr(sys, "_MEIPASS", exe_parent)).resolve()
        if (internal_root / "rxconfig.py").exists():
            return internal_root
        return exe_parent
    return Path(__file__).resolve().parents[2]


def wait_for_url(url: str, timeout_seconds: int = 300, processes: list[subprocess.Popen] | None = None) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if processes and all(process.poll() is not None for process in processes):
            codes = ", ".join(str(process.returncode) for process in processes)
            raise RuntimeError(f"Timed out waiting for {url}; app processes exited with codes: {codes}")
        try:
            with urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except URLError as exc:
            last_error = exc
        except OSError as exc:
            last_error = exc
        time.sleep(0.75)

    message = f"Timed out waiting for {url}"
    if last_error:
        message = f"{message}: {last_error}"
    raise RuntimeError(message)


def is_url_ready(url: str) -> bool:
    try:
        with urlopen(url, timeout=2) as response:
            return response.status < 500
    except (URLError, OSError):
        return False


def find_free_port(preferred_port: int) -> int:
    if is_port_free(preferred_port):
        return preferred_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def release_stale_reflex_port(port: int, health_url: str) -> None:
    if is_port_free(port) or is_url_ready(health_url) or psutil is None:
        return

    root = str(project_root()).lower()
    for connection in psutil.net_connections(kind="tcp"):
        if connection.laddr and connection.laddr.port == port and connection.status == psutil.CONN_LISTEN and connection.pid:
            try:
                process = psutil.Process(connection.pid)
                command_line = " ".join(process.cmdline()).lower()
                if root in command_line and ("reflex" in command_line or "chempulse" in command_line):
                    process.terminate()
                    try:
                        process.wait(timeout=8)
                    except psutil.TimeoutExpired:
                        process.kill()
            except (psutil.Error, OSError):
                continue


def stop_existing_runtime_processes() -> None:
    if psutil is None:
        return

    root = str(project_root()).lower()
    current_pid = os.getpid()
    for process in psutil.process_iter(["pid", "name", "cmdline"]):
        if process.pid == current_pid:
            continue
        try:
            command_line = " ".join(process.info.get("cmdline") or []).lower()
            name = (process.info.get("name") or "").lower()
            if root not in command_line:
                continue
            is_runtime = (
                "reflex" in command_line
                or "react-router" in command_line
                or "@react-router" in command_line
                or name == "react-router.exe"
            )
            if not is_runtime:
                continue
            process.terminate()
            try:
                process.wait(timeout=8)
            except psutil.TimeoutExpired:
                process.kill()
        except (psutil.Error, OSError):
            continue


def app_url(frontend_port: int) -> str:
    return f"http://{LOOPBACK_HOST}:{frontend_port}"


def backend_url(backend_port: int) -> str:
    return f"http://{LOOPBACK_HOST}:{backend_port}/api/status.js"


def backend_bind_host() -> str:
    enabled = os.getenv("CHEMPULSE_MOBILE_ACCESS_ENABLED", "").strip().lower()
    return LAN_BIND_HOST if enabled in {"1", "true", "yes", "on"} else LOOPBACK_HOST


def log_dir() -> Path:
    repo_storage = project_root() / "backend" / "storage"
    path = repo_storage if repo_storage.exists() or not getattr(sys, "frozen", False) else platform_app_data_dir() / "storage"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_launcher_log(message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with (log_dir() / "desktop-launcher.log").open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
    except OSError:
        pass


def shared_storage_dir() -> Path:
    configured = os.getenv("CHEMPULSE_STORAGE_DIR")
    if configured:
        path = Path(configured).expanduser()
    else:
        repo_storage = project_root() / "backend" / "storage"
        path = repo_storage if repo_storage.exists() or not getattr(sys, "frozen", False) else platform_app_data_dir() / "storage"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_frontend_env(frontend_port: int, backend_port: int) -> None:
    root = project_root()
    payload = {
        "PING": f"http://{LOOPBACK_HOST}:{backend_port}",
        "EVENT": f"ws://{LOOPBACK_HOST}:{backend_port}/_event",
        "CHEMPULSE_API_BASE_URL": f"http://{LOOPBACK_HOST}:{backend_port}",
        "CHEMPULSE_DEPLOY_URL": f"http://{LOOPBACK_HOST}:{frontend_port}",
    }
    for public_dir in (root / ".web" / "public",):
        public_dir.mkdir(parents=True, exist_ok=True)
        (public_dir / "env.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def clear_generated_web_state() -> None:
    generated_root = project_root() / ".web" / ".react-router"
    shutil.rmtree(generated_root, ignore_errors=True)


def version_key(path: Path) -> tuple[int, ...]:
    parts: list[int] = []
    for part in path.name.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(-1)
    return tuple(parts)


def valid_webview2_runtime_path() -> Path | None:
    configured = os.getenv("CHEMPULSE_WEBVIEW2_RUNTIME_PATH")
    if configured:
        candidate = Path(configured)
        if (candidate / "msedgewebview2.exe").exists():
            return candidate
        write_launcher_log(f"Ignoring invalid CHEMPULSE_WEBVIEW2_RUNTIME_PATH={candidate}")

    roots = [
        Path(os.getenv("ProgramFiles(x86)", "")) / "Microsoft" / "EdgeWebView" / "Application",
        Path(os.getenv("ProgramFiles", "")) / "Microsoft" / "EdgeWebView" / "Application",
        Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "EdgeWebView" / "Application",
        Path("C:/Program Files (x86)/Microsoft/EdgeWebView/Application"),
        Path("C:/Program Files/Microsoft/EdgeWebView/Application"),
        Path(os.getenv("ProgramFiles(x86)", "")) / "Microsoft" / "EdgeCore",
        Path("C:/Program Files (x86)/Microsoft/EdgeCore"),
    ]
    candidates: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        candidates.extend(path for path in root.iterdir() if (path / "msedgewebview2.exe").exists())

    if not candidates:
        return None
    return sorted(candidates, key=version_key, reverse=True)[0]


def configure_webview2_runtime() -> None:
    if os.name != "nt":
        return

    runtime_path = valid_webview2_runtime_path()
    if runtime_path is None:
        write_launcher_log("No valid WebView2 runtime folder found; falling back to WebView2 auto-discovery.")
        return

    webview.settings["WEBVIEW2_RUNTIME_PATH"] = str(runtime_path)
    write_launcher_log(f"Using WebView2 runtime: {runtime_path}")


def start_reflex(frontend_port: int, backend_port: int) -> subprocess.Popen:
    write_frontend_env(frontend_port, backend_port)
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env["FRONTEND_PORT"] = str(frontend_port)
    env["BACKEND_PORT"] = str(backend_port)
    env["CHEMPULSE_API_BASE_URL"] = f"http://{LOOPBACK_HOST}:{backend_port}"
    env["CHEMPULSE_DEPLOY_URL"] = f"http://{LOOPBACK_HOST}:{frontend_port}"
    env["CHEMPULSE_STORAGE_DIR"] = str(shared_storage_dir())
    configure_javascript_runtime_env(env)
    configure_reflex_package_manager_env(env)

    logs = log_dir()
    python_executable = external_python_executable()
    command = [
        python_executable,
        "-m",
        "reflex",
        "run",
        "--env",
        "dev",
        "--frontend-port",
        str(frontend_port),
        "--backend-port",
        str(backend_port),
        "--backend-host",
        backend_bind_host(),
    ]

    return subprocess.Popen(
        command,
        cwd=project_root(),
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        stdout=(logs / "desktop-reflex.log").open("ab"),
        stderr=(logs / "desktop-reflex.err.log").open("ab"),
    )


def external_python_executable() -> str:
    if not getattr(sys, "frozen", False):
        return sys.executable
    configured = os.getenv("CHEMPULSE_PYTHON")
    if configured:
        return configured
    found = shutil.which("python")
    if found:
        return found
    found = shutil.which("py")
    if found:
        return found
    return sys.executable


def start_packaged_runtime(frontend_port: int, backend_port: int) -> list[subprocess.Popen]:
    root = project_root()
    write_frontend_env(frontend_port, backend_port)
    restore_packaged_web_compat()
    logs = shared_storage_dir()
    logs.mkdir(parents=True, exist_ok=True)
    bundled_python = root / "runtime" / "python.exe"
    if not bundled_python.exists():
        return [start_reflex(frontend_port, backend_port)]

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    env["FRONTEND_PORT"] = str(frontend_port)
    env["BACKEND_PORT"] = str(backend_port)
    env["CHEMPULSE_API_BASE_URL"] = f"http://{LOOPBACK_HOST}:{backend_port}"
    env["CHEMPULSE_DEPLOY_URL"] = f"http://{LOOPBACK_HOST}:{frontend_port}"
    env["CHEMPULSE_STORAGE_DIR"] = str(shared_storage_dir())
    configure_javascript_runtime_env(env)
    configure_reflex_package_manager_env(env)

    runtime_process = subprocess.Popen(
        [
            str(bundled_python),
            "-m",
            "reflex",
            "run",
            "--env",
            "dev",
            "--frontend-port",
            str(frontend_port),
            "--backend-port",
            str(backend_port),
            "--backend-host",
            backend_bind_host(),
        ],
        cwd=root,
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        stdout=(logs / "desktop-backend.log").open("ab"),
        stderr=(logs / "desktop-backend.err.log").open("ab"),
    )
    return [runtime_process]


def configure_javascript_runtime_env(env: dict[str, str]) -> None:
    runtime_bins = []
    bundled_node = project_root() / "runtime" / "node"
    if (bundled_node / "node.exe").exists():
        runtime_bins.append(str(bundled_node))
    nodejs = Path("C:/Program Files/nodejs")
    if (nodejs / "node.exe").exists():
        runtime_bins.append(str(nodejs))
    bundled_bun = project_root() / "runtime" / "bun" / "bin"
    if (bundled_bun / "bun.exe").exists():
        runtime_bins.append(str(bundled_bun))

    existing_paths = [
        part
        for part in env.get("PATH", "").split(os.pathsep)
        if part
        and "WindowsApps\\OpenAI.Codex" not in part
        and "app\\resources" not in part
    ]
    env["PATH"] = os.pathsep.join([*runtime_bins, *existing_paths])


def configure_reflex_package_manager_env(env: dict[str, str]) -> None:
    if env.get("REFLEX_USE_NPM") is not None or env.get("REFLEX_BUN_PATH") is not None:
        return

    npm_path = shutil.which("npm", path=env.get("PATH"))
    if os.name == "nt" and npm_path:
        env["REFLEX_USE_NPM"] = "1"
        write_launcher_log(f"Using npm for Reflex package management on Windows: {npm_path}")
        return

    bundled_bun = project_root() / "runtime" / "bun" / "bin" / "bun.exe"
    if bundled_bun.exists():
        env.setdefault("REFLEX_BUN_PATH", str(bundled_bun))


def restore_packaged_web_compat() -> None:
    root = project_root()
    compat = root / "frontend" / "desktop" / "web_compat"
    targets = {
        compat / "radix_themes_color_mode_provider.js": root / ".web" / "components" / "reflex" / "radix_themes_color_mode_provider.js",
        compat / "routes.js": root / ".web" / "app" / "routes.js",
        compat / "entry.client.js": root / ".web" / "app" / "entry.client.js",
    }
    for source, destination in targets.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def stop_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return

    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def run_desktop_window(devtools: bool = False) -> None:
    processes: list[subprocess.Popen] = []
    configure_webview2_runtime()
    stop_existing_runtime_processes()
    release_stale_reflex_port(DEFAULT_BACKEND_PORT, backend_url(DEFAULT_BACKEND_PORT))
    release_stale_reflex_port(DEFAULT_FRONTEND_PORT, app_url(DEFAULT_FRONTEND_PORT))
    clear_generated_web_state()

    frontend_port = find_free_port(DEFAULT_FRONTEND_PORT)
    backend_port = find_free_port(DEFAULT_BACKEND_PORT)

    current_app_url = app_url(frontend_port)
    current_backend_url = backend_url(backend_port)

    if not is_url_ready(current_app_url) or not is_url_ready(current_backend_url):
        processes = (
            start_packaged_runtime(frontend_port, backend_port)
            if getattr(sys, "frozen", False)
            else [start_reflex(frontend_port, backend_port)]
        )
        for process in processes:
            atexit.register(stop_process, process)

    wait_for_url(current_backend_url, processes=processes)
    wait_for_url(current_app_url, processes=processes)
    write_launcher_log(f"Opening desktop window at {current_app_url}")

    window = webview.create_window(
        "ChemPulse",
        current_app_url,
        width=1440,
        height=920,
        min_size=(1100, 720),
        text_select=True,
    )

    def cleanup() -> None:
        for process in processes:
            stop_process(process)

    def refresh_initial_navigation() -> None:
        time.sleep(1.5)
        try:
            window.load_url(current_app_url)
            write_launcher_log(f"Confirmed WebView navigation to {current_app_url}")
        except Exception as exc:
            write_launcher_log(f"WebView navigation refresh failed: {exc}")

    window.events.closed += cleanup
    webview.start(
        refresh_initial_navigation,
        debug=devtools,
        private_mode=False,
        storage_path=str(log_dir() / "webview-profile"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch ChemPulse as a Windows desktop app.")
    parser.add_argument("--reflex-run", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--frontend-port", type=int, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--backend-port", type=int, default=None, help=argparse.SUPPRESS)
    parser.add_argument("--devtools", action="store_true", help="Open the webview with debugging enabled.")
    args = parser.parse_args()
    if args.reflex_run:
        cli = importlib.import_module("reflex.reflex").cli
        reflex_args = ["run", "--env", "dev"]
        if args.frontend_port:
            reflex_args.extend(["--frontend-port", str(args.frontend_port)])
        elif args.backend_port:
            reflex_args.extend(["--frontend-port", str(DEFAULT_FRONTEND_PORT)])
        if args.backend_port:
            reflex_args.extend(["--backend-port", str(args.backend_port)])
        else:
            reflex_args.extend(["--backend-port", str(DEFAULT_BACKEND_PORT)])
        reflex_args.extend(["--backend-host", backend_bind_host()])
        cli.main(args=reflex_args, prog_name="reflex", standalone_mode=False)
        return

    run_desktop_window(devtools=args.devtools)


if __name__ == "__main__":
    main()
