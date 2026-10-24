#!/usr/bin/env python3
"""
ralt-x-gen — Multi-region guest account generator.
Author: RALT · Channel: @trustedid99 · Owner: @Ralt_18
"""

import sys
import subprocess
import importlib


def _bootstrap_dependencies():
    deps = [
        ("requests", "requests"),
        ("Crypto", "pycryptodome"),
        ("colorama", "colorama"),
        ("urllib3", "urllib3"),
        ("psutil", "psutil"),
        ("socks", "PySocks"),
    ]
    missing = []
    for import_name, pip_name in deps:
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append((import_name, pip_name))
    if not missing:
        return
    print(f"[*] Auto-installing {len(missing)} missing dependency(ies)...")
    for _, pip_name in missing:
        print(f"  -> {pip_name}")
        installed = False
        for cmd in [
            [sys.executable, "-m", "pip", "install", pip_name],
            [sys.executable, "-m", "pip", "install", "--user", pip_name],
            [sys.executable, "-m", "pip", "install", "--break-system-packages", pip_name],
        ]:
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=300)
                if r.returncode == 0:
                    installed = True
                    break
            except Exception:
                continue
        if not installed:
            print(f"  [!] Could not install {pip_name} — exiting.")
            sys.exit(1)
        print(f"  [+] {pip_name} installed")


_bootstrap_dependencies()


_build_metadata = {
    "project": "ralt-x-gen",
    "author": "RALT",
    "release": "official",
    "version": "1.0.0",
    "channel": "@trustedid99",
    "owner": "@Ralt_18",
}


def _get_build_info():
    return _build_metadata


def _print_build_banner():
    print(
        "\n"
        "╔══════════════════════════════════════════════════════════╗\n"
        "║            RALT X GEN — OFFICIAL BUILD                   ║\n"
        "║            Owner: @Ralt_18  ·  @trustedid99              ║\n"
        "╚══════════════════════════════════════════════════════════╝\n"
    )


import hmac
import hashlib
import requests
import string
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import json
import time
from datetime import datetime
from colorama import Fore, Style, init
import urllib3
import os
import base64
import signal
import threading
import psutil
import re
import socket
import shutil

init(autoreset=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ─── RALT palette ────────────────────────────────────────────
class R:
    RESET   = Style.RESET_ALL
    BOLD    = Style.BRIGHT
    DIM     = "\033[2m"

    # core palette — violet / teal / gold
    VOID    = "\033[38;5;17m"
    INDIGO  = "\033[38;5;63m"
    VIOLET  = "\033[38;5;99m"
    PURPLE  = "\033[38;5;141m"
    ORCHID  = "\033[38;5;170m"
    MAGENTA = "\033[38;5;201m"
    PINK    = "\033[38;5;213m"

    CYAN    = "\033[38;5;51m"
    SKY     = "\033[38;5;117m"
    TEAL    = "\033[38;5;43m"
    AQUA    = "\033[38;5;87m"

    LIME    = "\033[38;5;154m"
    GREEN   = "\033[38;5;46m"
    MINT    = "\033[38;5;121m"

    GOLD    = "\033[38;5;220m"
    AMBER   = "\033[38;5;214m"
    ORANGE  = "\033[38;5;208m"

    RED     = "\033[38;5;203m"
    CRIMSON = "\033[38;5;161m"

    WHITE   = "\033[1;97m"
    SILVER  = "\033[38;5;252m"
    GRAY    = "\033[38;5;243m"

    OK      = "\033[38;5;46m"
    WARN    = "\033[38;5;214m"
    ERR     = "\033[38;5;203m"

_ACCENTS = [R.PURPLE, R.CYAN, R.GOLD, R.ORCHID, R.AQUA, R.MINT, R.PINK]

def accent():
    return random.choice(_ACCENTS)


# ─── Typewriter renderer ────────────────────────────────────
def typewrite(text, delay=0.012, color=None, end="\n"):
    """Slow-print text like a typewriter. Preserves ANSI in chunks."""
    if color:
        sys.stdout.write(color)
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(R.RESET + end)
    sys.stdout.flush()


def typewrite_slow(text, delay=0.028, color=None, end="\n"):
    typewrite(text, delay=delay, color=color, end=end)


# ─── Progress bar ────────────────────────────────────────────
class Bar:
    _lock = threading.Lock()

    @staticmethod
    def render(current, total, label="", width=28, color=None):
        color = color or R.PURPLE
        total = max(1, total)
        pct = min(100, int(current / total * 100))
        filled = int(width * current / total)
        bar = "█" * filled + "░" * (width - filled)
        with Bar._lock:
            sys.stdout.write(
                f"\r{R.GRAY}│{R.RESET} {color}{label:<18}{R.RESET} "
                f"{color}{bar}{R.RESET} {R.GOLD}{pct:3d}%{R.RESET}  "
                f"{R.GRAY}({current:,}/{total:,}){R.RESET}"
            )
            sys.stdout.flush()

    @staticmethod
    def finish(label="", color=None):
        color = color or R.GREEN
        with Bar._lock:
            sys.stdout.write(
                f"\r{R.GRAY}│{R.RESET} {color}✔ {label:<18}{R.RESET} "
                f"{R.GREEN}{'█' * 28}{R.RESET} {R.GOLD}100%{R.RESET}\n"
            )
            sys.stdout.flush()


# ─── Config paths (Android-first, emulated storage) ──────────
OUTPUT_FILE = "/storage/emulated/0/Download/RALTIDS.TXT"
OUTPUT_FALLBACK = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "RALTIDS.TXT"
)

def _resolve_output_path():
    target_dir = os.path.dirname(OUTPUT_FILE)
    if os.path.isdir(target_dir):
        try:
            with open(OUTPUT_FILE, "a", encoding="utf-8"):
                pass
            return OUTPUT_FILE
        except Exception:
            pass
    return OUTPUT_FALLBACK


config_cache_file = "ralt_live_config_cache.json"
config_fetch_command = [
    sys.executable, "-c",
    "from danger_ff_version_updater import get_categories; import json; print(json.dumps(get_categories()))"
]

default_global_server = "https://loginbp.ppmainecoonghj.com/"
default_client_url    = "https://clientbp.ppmainecoonghj.com/"
default_release_tag   = "OB55"
default_registration_version = "1.132.11"

server_global = default_global_server
client_global = default_client_url
release_tag   = default_release_tag

registration_version  = default_registration_version
registration_language = "en"

supported_regions = [
    "ME", "IND", "ID", "VN", "TH", "BD",
    "PK", "TW", "CIS", "SAC", "BR",
]
ghost_mode_region = "BR"

activator_api_url     = "https://divan-activator.vercel.app/bind"
activator_api_timeout = 25
activator_api_retries = 2

use_tor_proxy      = True
tor_socks_proxy    = "socks5h://127.0.0.1:9050"
tor_setup_timeout  = 120.0
rotation_threshold = 5
tor_rotation_cooldown = 15.0


def apply_configuration(snapshot):
    global server_global, release_tag, registration_version, client_global
    for key in ("OTHERS", "IND", "AMERICA"):
        bucket = snapshot.get(key, {}) or {}
        if bucket.get("server_url"):
            server_global = bucket["server_url"]
            break
    for key in ("OTHERS", "IND", "AMERICA"):
        bucket = snapshot.get(key, {}) or {}
        if bucket.get("client_url"):
            client_global = bucket["client_url"]
            break
    for key in ("OTHERS", "IND", "AMERICA"):
        bucket = snapshot.get(key, {}) or {}
        if bucket.get("release_version"):
            release_tag = bucket["release_version"]
            break
    for key in ("OTHERS", "IND", "AMERICA"):
        bucket = snapshot.get(key, {}) or {}
        if bucket.get("client_version"):
            registration_version = bucket["client_version"]
            break


def sync_config():
    today = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(config_cache_file):
        try:
            with open(config_cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("date") == today and isinstance(cached.get("config"), dict):
                apply_configuration(cached["config"])
                return
        except Exception:
            pass
    try:
        raw = subprocess.check_output(
            config_fetch_command, stderr=subprocess.STDOUT, timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        snapshot = json.loads(raw.decode("utf-8").strip())
        if not isinstance(snapshot, dict):
            raise ValueError("config payload not a dict")
        apply_configuration(snapshot)
        try:
            with open(config_cache_file, "w", encoding="utf-8") as f:
                json.dump({"date": today, "config": snapshot}, f, indent=2)
        except Exception:
            pass
        return
    except Exception:
        pass
    if os.path.exists(config_cache_file):
        try:
            with open(config_cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if isinstance(cached.get("config"), dict):
                apply_configuration(cached["config"])
        except Exception:
            pass


# ─── State ───────────────────────────────────────────────────
exit_flag = False
ctrl_c_count = 0
ctrl_c_last = 0.0
success_counter = 0
rare_counter = 0
couples_counter = 0
rarity_score_threshold = 3
lock = threading.Lock()

consecutive_reg_errors = 0
reg_error_lock = threading.Lock()
last_rotation_time = 0.0

_garner = "QllfUkFMVA=="   # "BY_RALT"

rarity_patterns = {
    "REPEATED_DIGITS_4":         [r"(\d)\1{3,}", 4],
    "REPEATED_DIGITS_3":         [r"(\d)\1\1(\d)\2\2", 3],
    "SEQUENTIAL_5":              [r"(12345|23456|34567|45678|56789|98765|87654|76543|65432|54321)", 5],
    "SEQUENTIAL_4":              [r"(0123|1234|2345|3456|4567|5678|6789|9876|8765|7654|6543|5432|4321|3210)", 3],
    "SPECIAL_COMBINATIONS_HIGH": [r"^(69|420|1337|007|999|666)", 4],
    "QUADRUPLE_DIGITS":          [r"(1111|2222|3333|4444|5555|6666|7777|8888|9999|0000)", 5],
    "MIRROR_PATTERN_MED":        [r"(\d{2})0\1", 3],
    "DOUBLE_PAIR_START":         [r"^(\d)\1(\d)\2", 3],
    "TRIPLE_PAIR_ANY":           [r"(\d)\1.*(\d)\2.*(\d)\3", 4],
    "GOLDEN_RATIO":              [r"1618|0618", 4],
    "REPEATED_TAIL_3":           [r"(\d)\1\1$", 3],
    "REPEATED_HEAD_3":           [r"^(\d)\1\1", 3],
}

couple_candidates = {}
couple_lock = threading.Lock()


def assess_rarity(account):
    ident = account.get("account_id", "")
    if ident is None:
        return False, None, None, 0
    ident = str(ident)
    if ident == "N/A" or not ident:
        return False, None, None, 0
    score = 0
    detected = []
    for name, meta in rarity_patterns.items():
        if re.search(meta[0], ident):
            score += meta[1]
            detected.append(name)
    digits = [int(d) for d in ident if d.isdigit()]
    if len(digits) >= 4:
        if len(set(digits)) == 1:
            score += 5
            detected.append("UNIFORM_DIGITS")
        deltas = [digits[i + 1] - digits[i] for i in range(len(digits) - 1)]
        if len(set(deltas)) == 1:
            score += 4
            detected.append("ARITHMETIC_SEQUENCE")
    if score >= rarity_score_threshold:
        reason = f"Account ID {ident} - Score: {score} - Patterns: {', '.join(detected)}"
        return True, "RARE_ACCOUNT", reason, score
    return False, None, None, score


def assess_couple(account, thread_id):
    ident = account.get("account_id", "")
    if ident is None:
        return False, None, None
    ident = str(ident)
    if ident == "N/A" or not ident:
        return False, None, None
    with couple_lock:
        for stored_key, stored_rec in couple_candidates.items():
            stored_ident = stored_rec.get('account_id', '')
            stored_ident = str(stored_ident) if stored_ident is not None else ""
            matched, explanation = match_couple(ident, stored_ident)
            if matched:
                partner = stored_rec
                del couple_candidates[stored_key]
                return True, explanation, partner
        couple_candidates[ident] = {
            'uid': account.get('uid', ''),
            'account_id': ident,
            'name': account.get('name', ''),
            'password': account.get('password', ''),
            'region': account.get('region', ''),
            'thread_id': thread_id,
            'timestamp': datetime.now().isoformat()
        }
    return False, None, None


def match_couple(a, b):
    a = str(a) if a is not None else ""
    b = str(b) if b is not None else ""
    if not a or not b or not (a.isdigit() and b.isdigit()):
        return False, None
    if len(a) != len(b) or len(a) < 3:
        return False, None
    if abs(int(a) - int(b)) == 1:
        return True, f"Consecutive IDs: {a} & {b}"
    if a[:-2] == b[:-2] and abs(int(a[-2:]) - int(b[-2:])) == 1:
        return True, f"Sequential suffixes: ...{a[-2:]} & ...{b[-2:]}"
    if a[:-3] == b[:-3] and abs(int(a[-3:]) - int(b[-3:])) == 1:
        return True, f"Sequential last-3: ...{a[-3:]} & ...{b[-3:]}"
    return False, None


# ─── Single output file (RALTIDS.TXT) ───────────────────────
_output_lock = threading.Lock()
_output_initialized = False


def _init_output_file():
    global _output_initialized
    if _output_initialized:
        return
    path = _resolve_output_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(
                "══════════════════════════════════════════════════════════\n"
                "                RALT IDS — GENERATED ACCOUNTS\n"
                f"                Owner: @Ralt_18 · @trustedid99\n"
                f"                Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                "══════════════════════════════════════════════════════════\n\n"
            )
        _output_initialized = True
    except Exception as err:
        emit_error(f"Could not init {path}: {err}")


def write_account_block(account, region, kind="NORMAL", reason=""):
    _init_output_file()
    path = _resolve_output_path()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"[{ts}] ── {kind} ── region={region}",
        f"  name       : {account.get('name', 'N/A')}",
        f"  uid        : {account.get('uid', 'N/A')}",
        f"  password   : {account.get('password', 'N/A')}",
        f"  account_id : {account.get('account_id', 'N/A')}",
        f"  thread     : {account.get('thread_id', 'N/A')}",
    ]
    if account.get('jwt_token'):
        lines.append(f"  jwt        : {account['jwt_token']}")
    if reason:
        lines.append(f"  reason     : {reason}")
    lines.append("─" * 60)
    lines.append("")
    block = "\n".join(lines) + "\n"
    with _output_lock:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(block)
        except Exception as err:
            emit_error(f"Write failed: {err}")


# ─── Messaging ──────────────────────────────────────────────
def emit_success(msg):
    print(f"{accent()}{R.BOLD}✅ {msg}{R.RESET}")


def emit_error(msg):
    print(f"{R.ERR}{R.BOLD}❌ {msg}{R.RESET}")


def emit_warning(msg):
    print(f"{R.WARN}{R.BOLD}⚠️  {msg}{R.RESET}")


def emit_info(msg):
    print(f"{R.SKY}{msg}{R.RESET}")


# ─── Tor rotation ──────────────────────────────────────────
def _regerror_reset():
    global consecutive_reg_errors
    with reg_error_lock:
        consecutive_reg_errors = 0


def _regerror_bump():
    global consecutive_reg_errors
    should_rotate = False
    current = 0
    with reg_error_lock:
        consecutive_reg_errors += 1
        current = consecutive_reg_errors
        if current >= rotation_threshold:
            consecutive_reg_errors = 0
            should_rotate = True
    if should_rotate:
        rotate_tor_ip(current)


def rotate_tor_ip(fail_count):
    global last_rotation_time
    if not use_tor_proxy:
        return
    now = time.time()
    if now - last_rotation_time < tor_rotation_cooldown:
        return
    last_rotation_time = now
    emit_warning(f"🔄 {fail_count} consecutive errors — rotating Tor IP...")
    try:
        r = subprocess.run(["pkill", "-HUP", "tor"], timeout=10, capture_output=True)
        time.sleep(3)
        if r.returncode == 0:
            emit_success("Tor IP rotated")
        elif r.returncode == 1:
            emit_warning("Tor process not found")
        else:
            emit_warning(f"Tor rotation failed (exit {r.returncode})")
    except FileNotFoundError:
        emit_warning("pkill not available — skip")
    except subprocess.TimeoutExpired:
        emit_warning("Tor rotation timed out")
    except Exception as err:
        emit_warning(f"Tor rotation error: {err}")


def _wait_for_tor(deadline=None):
    start = time.time()
    last_note = 0.0
    while not exit_flag:
        try:
            with socket.create_connection(("127.0.0.1", 9050), timeout=1):
                return True
        except Exception:
            pass
        if deadline is not None and time.time() >= deadline:
            return False
        elapsed = time.time() - start
        if elapsed - last_note >= 5:
            last_note = elapsed
            if deadline is not None:
                remaining = max(0, int(deadline - time.time()))
                emit_warning(f"⏳ Tor SOCKS ({int(elapsed)}s elapsed, {remaining}s left)")
            else:
                emit_warning(f"⏳ Tor SOCKS ({int(elapsed)}s)")
        time.sleep(1)
    return False


def _tor_circuit_ready():
    proxies = {"http": tor_socks_proxy, "https": tor_socks_proxy}
    try:
        r = requests.get("https://check.torproject.org/api/ip", proxies=proxies, timeout=15, verify=False)
        if r.status_code == 200:
            d = r.json()
            if d.get("IsTor"):
                return True, d.get("IP", "?")
    except Exception:
        pass
    try:
        r = requests.get("https://api.ipify.org/?format=json", proxies=proxies, timeout=15, verify=False)
        if r.status_code == 200:
            return True, r.json().get("ip", "?")
    except Exception:
        pass
    return False, None


def _auto_install_tor():
    if shutil.which("tor"):
        return True
    candidates = []
    for bin_name, cmd in [
        ("pkg",     ["pkg", "install", "-y", "tor"]),
        ("apt-get", ["apt-get", "install", "-y", "tor"]),
        ("apt",     ["apt", "install", "-y", "tor"]),
        ("dnf",     ["dnf", "install", "-y", "tor"]),
        ("yum",     ["yum", "install", "-y", "tor"]),
        ("pacman",  ["pacman", "-S", "--noconfirm", "tor"]),
        ("apk",     ["apk", "add", "tor"]),
        ("brew",    ["brew", "install", "tor"]),
    ]:
        if shutil.which(bin_name):
            candidates.append(cmd)
    if not candidates:
        return False
    for cmd in candidates:
        try:
            emit_warning(f"Trying: {' '.join(cmd)}")
            r = subprocess.run(cmd, capture_output=True, timeout=600)
            if r.returncode == 0 and shutil.which("tor"):
                return True
            if r.returncode != 0 and r.stderr:
                tail = r.stderr.decode("utf-8", "ignore").strip().splitlines()[-1:]
                if tail:
                    emit_warning(f"Failed: {tail[0]}")
        except Exception as err:
            emit_warning(f"Install error: {err}")
    return False


def start_tor():
    global use_tor_proxy
    if not shutil.which("tor"):
        emit_warning("Tor not installed — auto-installing...")
        if _auto_install_tor():
            emit_success("Tor installed")
        else:
            emit_warning("Tor auto-install failed — DIRECT mode")
            use_tor_proxy = False
            return False
    try:
        subprocess.run(["pkill", "-9", "tor"], capture_output=True, timeout=5)
    except Exception:
        pass
    time.sleep(1)
    try:
        subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as err:
        emit_warning(f"Tor launch error: {err} — DIRECT mode")
        use_tor_proxy = False
        return False
    deadline = time.time() + tor_setup_timeout
    emit_success(f"Tor launching — budget {int(tor_setup_timeout)}s")
    if not _wait_for_tor(deadline=deadline):
        emit_warning(f"Tor SOCKS never opened in {int(tor_setup_timeout)}s — DIRECT")
        use_tor_proxy = False
        return False
    emit_success("Tor SOCKS 9050 open — verifying exit circuit ...")
    phase_start = time.time()
    last_note = 0.0
    while not exit_flag and time.time() < deadline:
        ok, exit_ip = _tor_circuit_ready()
        if ok:
            emit_success(f"Tor ready — exit IP: {exit_ip}")
            return True
        elapsed = time.time() - phase_start
        if elapsed - last_note >= 5:
            last_note = elapsed
            remaining = max(0, int(deadline - time.time()))
            emit_warning(f"⏳ Tor exit circuit ({remaining}s left)")
        time.sleep(2)
    emit_warning(f"Tor exit circuit not ready in {int(tor_setup_timeout)}s — DIRECT")
    use_tor_proxy = False
    return False


# ─── Registration display ──────────────────────────────────
def show_registration(index, total, name, uid, password, account_id, region, is_ghost=False):
    print(f"{accent()}{R.BOLD}📝 Registration {index}/{total}{R.RESET}")
    print(f"{accent()}👤 Name: {name}{R.RESET}")
    print(f"{accent()}🆔 UID: {uid}{R.RESET}")
    print(f"{accent()}🎮 Account ID: {account_id}{R.RESET}")
    print(f"{accent()}🔑 Password: {password}{R.RESET}")
    if is_ghost:
        print(f"{accent()}🌍 Mode: {R.MAGENTA}GHOST (BR){R.RESET}")
    else:
        print(f"{accent()}🌍 Region: {region}{R.RESET}")
    print()


def show_rare(account, rarity_type, reason, rarity_score):
    print(f"\n{R.ORCHID}{R.BOLD}💎 RARE ACCOUNT FOUND!{R.RESET}")
    print(f"{R.ORCHID}🎯 Type: {rarity_type}{R.RESET}")
    print(f"{R.ORCHID}⭐ Score: {rarity_score}{R.RESET}")
    print(f"{R.ORCHID}👤 Name: {account['name']}{R.RESET}")
    print(f"{R.ORCHID}🆔 UID: {account['uid']}{R.RESET}")
    print(f"{R.ORCHID}🎮 ID: {account.get('account_id', 'N/A')}{R.RESET}")
    print(f"{R.ORCHID}📝 Reason: {reason}{R.RESET}")
    print(f"{R.ORCHID}🧵 Thread: {account.get('thread_id', 'N/A')}{R.RESET}")
    print(f"{R.ORCHID}🌍 Region: {account.get('region', 'N/A')}{R.RESET}\n")


def show_couple(primary, partner, reason):
    print(f"\n{R.AQUA}{R.BOLD}💑 COUPLES ACCOUNT FOUND!{R.RESET}")
    print(f"{R.AQUA}📝 Reason: {reason}{R.RESET}")
    print(f"{R.AQUA}👤 A1: {primary['name']} (ID {primary.get('account_id', 'N/A')}){R.RESET}")
    print(f"{R.AQUA}👤 A2: {partner['name']} (ID {partner.get('account_id', 'N/A')}){R.RESET}")
    print(f"{R.AQUA}🆔 UIDs: {primary['uid']} & {partner['uid']}{R.RESET}")
    print(f"{R.AQUA}🌍 Region: {primary.get('region', 'N/A')}{R.RESET}\n")


# ─── Signal handling ───────────────────────────────────────
def shutdown(signum=None, frame=None):
    global exit_flag, ctrl_c_count, ctrl_c_last
    now = time.time()
    if now - ctrl_c_last > 3:
        ctrl_c_count = 0
    ctrl_c_count += 1
    ctrl_c_last = now
    if ctrl_c_count >= 2:
        exit_flag = True
        print(f"\n{accent()}{R.BOLD}🚨 Closing RALT-ERA ...{R.RESET}")
        sys.exit(0)
    print(f"\n{R.WARN}{R.BOLD}⚠️  Ctrl+C again within 3s to exit{R.RESET}")


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def banner():
    print(f"""
{accent()}{R.BOLD}
    ██████╗  █████╗ ██╗  ████████╗    ██╗  ██╗
    ██╔══██╗██╔══██╗██║  ╚══██╔══╝    ╚██╗██╔╝
    ██████╔╝███████║██║     ██║        ╚███╔╝
    ██╔══██╗██╔══██║██║     ██║        ██╔██╗
    ██║  ██║██║  ██║███████╗██║       ██╔╝ ██╗
    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝       ╚═╝  ╚═╝

    account generator · owner @Ralt_18 · channel @trustedid99
{R.RESET}""")


def superscript():
    digits = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'}
    return ''.join(digits[d] for d in f"{random.randint(1, 99999):05d}")


def random_name(prefix):
    return f"{prefix[:7]}{superscript()}"


def make_password(prefix):
    suffix = base64.b64decode(_garner).decode('utf-8')
    chars = string.ascii_uppercase + string.digits
    p1 = ''.join(random.choice(chars) for _ in range(5))
    p2 = ''.join(random.choice(chars) for _ in range(5))
    return f"{prefix}_{p1}_{suffix}_{p2}"


def pause():
    time.sleep(random.uniform(1, 2))


aes_key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
aes_iv  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

client_secret = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
app_id = 100067

oauth_register = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
oauth_token    = "https://100067.connect.garena.com/oauth/guest/token/grant"

msdk_agents = [
    "GarenaMSDK/4.0.42(KB2003 ;Android 13;en;HK;app 2.130.1 2019118332;)",
    "GarenaMSDK/4.0.42(SM-G998B ;Android 14;en;IN;app 2.131.0 2019118527;)",
    "GarenaMSDK/4.0.42(CPH2095 ;Android 12;en;ID;app 2.129.1 2019118142;)",
    "GarenaMSDK/4.0.42(Redmi 2404ARN45A ;Android 13;en;IN;app 2.132.0 2019118721;)",
    "GarenaMSDK/4.0.42(Pixel 6 ;Android 14;en;US;app 2.131.1 2019118602;)",
    "GarenaMSDK/4.0.42(OnePlus 9 Pro ;Android 13;en;IN;app 2.132.2 2019118783;)",
    "GarenaMSDK/4.0.42(Xiaomi 13 Pro ;Android 14;en;ID;app 2.130.2 2019118441;)",
    "GarenaMSDK/4.0.42(realme RMX2189 ;Android 10;en;IN;app 2.130.0 2019118321;)",
]

unity_agents = [
    "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
    "UnityPlayer/2021.3.27f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
    "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
    "UnityPlayer/2020.3.45f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
]

xor_key = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,
           0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30]

field_22_hex = (
    "474752450101010062020000a78910bd098e3ff2e4345d59a31db114ea088f37e32e65"
    "212ff96621793d9eb78720d0bf2ac95176569765247ada5eb01376b3b9931794a4946"
    "d76ef8890779f3f2129317e6e1cb2fdcf7b06247cea343b8d4f167eff85a2e1dfe99"
    "b4583a7e1a155dbe7f7f85cff3b223eb77222ec1228f3ee1ef6ce7f8ca24b00a554"
    "e497328812f8df74c82d519ae3e3ceab436eb145e8a517089a7cef6a4efb22214b2"
    "a4b19989b74807584afe5e52825e7ac60e19a596a9bf02d961de6a0ed2515ec6023"
    "fdb7684d9464b97b21c527ce61b6bee4ef30d20a1fa33a996952d44d44e44f2f86c"
    "768aaf2a7808ad60f91048dca0207961ba7c2555c48341b30190debc775edb2cee24"
    "4cf51fca3760ce4388be2db45e80b813b5beb9c784007b7762d7a1e428affc8a3a4"
    "cd76cbaef648a274297fde33233dccd3f272cb77f39a1affe0365a24954111f768f72"
    "0e77535af024bea2b2726c3bac992374755c3deacf09235e6865d456e651680d115a"
    "751a797225eaacdf9a513cf104526e1a32e5296e111a33ae581a63850837921df848"
    "9adfd41ea895b7cf3f5b2e45d538a6e4f032f590ccbb7daf5fa9c50adadee0799661"
    "4c3f957bda349e6c484fdf55970d1943ad7955a76671298b6d98b636b69ebde6bc94"
    "dbd93ac3393a6ae230130445b2d744189167854a5617be2393e7d8fbb5719a1b4754"
    "1ba466167e3e05a6c244f1301ee2035acf94dffc8adbde747d5cd85e35ead3acc372"
    "a59c4220e54bf63f9d80485f3de2518495c1d0f78c911d2da595911fd2a1989cf17"
    "cf3ded5f6c92dea64d675c555c11df92d6c517ca5d0d61a8962f43f76ec7e87596c"
    "8325ebf9ab0f8e6d2eca33c511ceac6980906ebd68c478665591dcecf788ec6ef34c"
    "fbe3fcc279c6147c5bf91cd43cdc9704236"
)


def ga_sv():
    return str(int(time.time()))


def write_varint(value):
    out = []
    while value > 127:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def field_int(field_number, value):
    return write_varint((field_number << 3) | 0) + write_varint(value)


def field_str(field_number, value):
    encoded = value.encode("utf-8")
    return write_varint((field_number << 3) | 2) + write_varint(len(encoded)) + encoded


def field_bytes(field_number, value):
    return write_varint((field_number << 3) | 2) + write_varint(len(value)) + value


def assemble_proto(fields):
    buffer = bytearray()
    for key_, value in fields.items():
        if isinstance(value, int):
            buffer.extend(field_int(key_, value))
        elif isinstance(value, str):
            buffer.extend(field_str(key_, value))
        elif isinstance(value, (bytes, bytearray)):
            buffer.extend(field_bytes(key_, bytes(value)))
    return bytes(buffer)


def encrypt_aes(plain):
    return AES.new(aes_key, AES.MODE_CBC, aes_iv).encrypt(pad(plain, AES.block_size))


def read_varint(data, offset):
    result, shift = 0, 0
    while True:
        if offset >= len(data):
            raise IndexError("eof")
        byte = data[offset]
        result |= (byte & 0x7F) << shift
        offset += 1
        if not (byte & 0x80):
            break
        shift += 7
    return result, offset


def parse_proto(data):
    output, offset = {}, 0
    while offset < len(data):
        try:
            tag, offset = read_varint(data, offset)
        except Exception:
            break
        field_number, wire_type = tag >> 3, tag & 0x7
        try:
            if wire_type == 0:
                value, offset = read_varint(data, offset)
                output[field_number] = value
            elif wire_type == 2:
                length, offset = read_varint(data, offset)
                chunk = data[offset:offset + length]
                offset += length
                try:
                    output[field_number] = chunk.decode("utf-8")
                except Exception:
                    output[field_number] = chunk.hex()
            elif wire_type == 1:
                output[field_number] = data[offset:offset + 8].hex()
                offset += 8
            elif wire_type == 5:
                output[field_number] = data[offset:offset + 4].hex()
                offset += 4
            else:
                break
        except Exception:
            break
    return output


def xor_open_id(open_id):
    raw = open_id.encode("utf-8")
    return bytes(x ^ xor_key[i % len(xor_key)] for i, x in enumerate(raw))


def sign_payload(payload):
    body = json.dumps(payload, separators=(",", ":"))
    return hmac.new(client_secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()


def register_guest(session, password, user_agent):
    payload = {"app_id": app_id, "client_type": 2, "password": password, "source": 2}
    signature = sign_payload(payload)
    body = json.dumps(payload, separators=(",", ":"))
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Authorization": f"Signature {signature}",
    }
    response = session.post(oauth_register, data=body, headers=headers, timeout=15)
    if response.status_code != 200:
        raise Exception(f"Register HTTP {response.status_code}: {response.text[:200]}")
    data = response.json()
    if data.get("code") != 0:
        raise Exception(f"Register failed: {data}")
    uid = str(data["data"]["uid"])
    emit_success(f"Guest account created: {uid}")
    pause()
    return uid


def request_token(session, uid, password, user_agent):
    payload = {
        "uid": uid, "password": password,
        "response_type": "token", "client_type": "2",
        "client_secret": client_secret, "client_id": "100067",
    }
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "Connection": "Keep-Alive",
    }
    response = session.post(oauth_token, data=payload, headers=headers, timeout=30)
    if response.status_code != 200:
        raise Exception(f"Token HTTP {response.status_code}: {response.text[:200]}")
    data = response.json()
    access_token, open_id = data.get("access_token"), data.get("open_id")
    if not access_token or not open_id:
        raise Exception(f"Token grant failed: {data}")
    emit_success(f"Token granted for: {uid}")
    pause()
    return access_token, open_id


def major_register(session, name, access_token, open_id, user_agent):
    url = server_global + "MajorRegister"
    fields = {
        1: name, 2: access_token, 3: open_id,
        5: 102000007, 6: 4, 7: 1, 13: 1,
        14: xor_open_id(open_id),
        15: registration_language,
        16: 2, 20: registration_version, 21: 1,
        22: bytes.fromhex(field_22_hex),
    }
    encrypted = encrypt_aes(assemble_proto(fields))
    headers = {
        "Host": url.split("/")[2],
        "User-Agent": user_agent,
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "X-GA-SV": ga_sv(),
        "Authorization": "Bearer",
        "X-GA": "v1 1",
        "ReleaseVersion": release_tag,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1",
        "Content-Length": str(len(encrypted)),
    }
    response = session.post(url, data=encrypted, headers=headers, timeout=30, verify=False)
    if response.status_code != 200:
        raise Exception(f"MajorRegister HTTP {response.status_code}: {response.text[:200]}")
    return parse_proto(response.content)


def newbie_choice(session, account_id, choice=3, user_agent=None):
    url = server_global + "ChooseNewbieChoice"
    encrypted = encrypt_aes(assemble_proto({1: int(account_id), 2: 1, 3: int(choice)}))
    headers = {
        "Host": url.split("/")[2],
        "User-Agent": user_agent or "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "X-GA-SV": ga_sv(),
        "Authorization": "Bearer",
        "X-GA": "v1 1",
        "ReleaseVersion": release_tag,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1",
        "Content-Length": str(len(encrypted)),
    }
    response = session.post(url, headers=headers, data=encrypted, timeout=30, verify=False)
    if response.status_code != 200:
        raise Exception(f"ChooseNewbieChoice HTTP {response.status_code}")
    return response


def activator_bind(uid, password, region):
    info = {"target": region.upper()}
    last_error = None
    proxies = {"http": tor_socks_proxy, "https": tor_socks_proxy} if use_tor_proxy else None
    for attempt in range(1, activator_api_retries + 1):
        try:
            response = requests.get(
                activator_api_url,
                params={"uid": uid, "password": password, "region": region.upper()},
                headers={"Accept": "application/json"},
                timeout=activator_api_timeout,
                verify=False,
                proxies=proxies,
            )
            if response.status_code != 200:
                last_error = f"HTTP {response.status_code}: {response.text[:150]}"
                emit_warning(f"Activator {attempt}/{activator_api_retries} -> {last_error}")
                time.sleep(1.0)
                continue
            try:
                data = response.json()
            except Exception:
                last_error = "non-json"
                emit_warning(f"Activator {attempt}/{activator_api_retries} -> {last_error}")
                time.sleep(1.0)
                continue
            if not isinstance(data, dict):
                last_error = "unexpected shape"
                emit_warning(f"Activator {attempt}/{activator_api_retries} -> {last_error}")
                time.sleep(1.0)
                continue
            if not data.get("success"):
                last_error = data.get("error") or "unknown"
                emit_warning(f"Activator {attempt}/{activator_api_retries} -> {last_error}")
                if last_error in ("auth_failed", "login_failed", "region_bind_rejected"):
                    break
                time.sleep(1.0)
                continue
            new_jwt = data.get("jwt")
            if not new_jwt or not isinstance(new_jwt, str):
                last_error = "missing jwt"
                emit_warning(f"Activator {attempt}/{activator_api_retries} -> {last_error}")
                time.sleep(1.0)
                continue
            info["jwt"] = new_jwt
            emit_success(f"Region {region.upper()} bound")
            return True, new_jwt, info
        except requests.exceptions.Timeout:
            last_error = "timeout"
            emit_warning(f"Activator {attempt}/{activator_api_retries} -> timeout")
            time.sleep(1.0)
        except requests.exceptions.ConnectionError as err:
            last_error = f"conn error: {err}"
            emit_warning(f"Activator {attempt}/{activator_api_retries} -> {err}")
            time.sleep(1.0)
        except Exception as err:
            last_error = str(err)
            emit_warning(f"Activator {attempt}/{activator_api_retries} -> {err}")
            time.sleep(1.0)
    emit_warning(f"Activator failed after {activator_api_retries} -> {last_error}")
    info["error"] = last_error
    return False, None, info


def create_account(target_region, account_name, password_prefix, is_ghost=False):
    if exit_flag:
        return None
    session = requests.Session()
    session.verify = False
    if use_tor_proxy:
        session.proxies = {"http": tor_socks_proxy, "https": tor_socks_proxy}
    try:
        msdk_ua  = random.choice(msdk_agents)
        unity_ua = random.choice(unity_agents)
        password = make_password(password_prefix)
        uid = None
        try:
            uid = register_guest(session, password, msdk_ua)
        except Exception:
            _regerror_bump()
            time.sleep(random.uniform(2.0, 4.0))
            return None
        if uid:
            _regerror_reset()
        else:
            _regerror_bump()
            time.sleep(random.uniform(2.0, 4.0))
            return None
        access_token, open_id = request_token(session, uid, password, msdk_ua)
        account_id = None
        name = random_name(account_name)
        for reg_attempt in range(1, 11):
            name = random_name(account_name)
            try:
                reg_resp = major_register(session, name, access_token, open_id, unity_ua)
                account_id = reg_resp.get(3)
                if account_id:
                    account_id = str(account_id)
                    emit_success(f"MajorRegister OK: {name}")
                    break
            except Exception as err:
                emit_warning(f"MajorRegister {reg_attempt}/10 failed: {err}")
                if reg_attempt < 10:
                    time.sleep(0.5)
        if not account_id:
            return None
        try:
            newbie_choice(session, account_id, choice=3, user_agent=unity_ua)
        except Exception as err:
            emit_warning(f"NewbieChoice error: {err}")
        if is_ghost:
            emit_success("Ghost Mode — skip Activator")
            return {
                "uid": uid, "password": password, "name": name,
                "region": target_region, "status": "success",
                "account_id": account_id, "jwt_token": "",
            }
        jwt_token = ""
        ok, new_jwt, _ = activator_bind(uid, password, target_region)
        if ok and new_jwt:
            jwt_token = new_jwt
        else:
            emit_warning("Activator failed — saved without JWT")
        return {
            "uid": uid, "password": password, "name": name,
            "region": target_region, "status": "success",
            "account_id": account_id, "jwt_token": jwt_token,
        }
    except Exception as err:
        emit_warning(f"create_acc error: {err}")
        pause()
        return None
    finally:
        try:
            session.close()
        except Exception:
            pass


def generate_single_account(region, account_name, password_prefix, total_accounts, thread_id, is_ghost=False):
    global success_counter, rare_counter, couples_counter
    if exit_flag:
        return None
    with lock:
        if success_counter >= total_accounts:
            return None
    result = create_account(region, account_name, password_prefix, is_ghost=is_ghost)
    if not result:
        return None
    account_id = result.get("account_id", "N/A")
    jwt_token = result.get("jwt_token", "")
    result['thread_id'] = thread_id
    with lock:
        success_counter += 1
        current_count = success_counter
    show_registration(current_count, total_accounts, result["name"],
                      result["uid"], result["password"],
                      account_id, region, is_ghost)
    Bar.render(current_count, total_accounts, "accounts", color=R.PURPLE)
    if current_count >= total_accounts:
        Bar.finish("accounts", color=R.PURPLE)
    # single output file
    write_account_block(result, region, kind="NORMAL")
    is_rare, rarity_type, rarity_reason, rarity_score = assess_rarity(result)
    if is_rare:
        with lock:
            rare_counter += 1
        show_rare(result, rarity_type, rarity_reason, rarity_score)
        write_account_block(result, region, kind="RARE", reason=rarity_reason)
        emit_success(f"💎 Rare saved (total {rare_counter})")
    is_couple, couple_reason, partner_data = assess_couple(result, thread_id)
    if is_couple and partner_data:
        with lock:
            couples_counter += 1
        show_couple(result, partner_data, couple_reason)
        write_account_block(result, region, kind="COUPLE", reason=couple_reason)
        emit_success(f"💑 Couple saved (total {couples_counter})")
    return {"account": result}


def worker(region, account_name, password_prefix, total_accounts, thread_id, is_ghost=False):
    print(f"{accent()}{R.BOLD}🧵 Thread {thread_id} started{R.RESET}")
    accounts_generated = 0
    while not exit_flag:
        with lock:
            if success_counter >= total_accounts:
                break
        result = generate_single_account(region, account_name, password_prefix, total_accounts, thread_id, is_ghost)
        if result:
            accounts_generated += 1
        time.sleep(random.uniform(0.5, 1.5))
    print(f"{accent()}{R.BOLD}🧵 Thread {thread_id} finished: {accounts_generated}{R.RESET}")


def wait_for_enter():
    print(f"\n{accent()}{R.BOLD}⏎ Press Enter to continue...{R.RESET}")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


# ─── Typewriter menu helpers ───────────────────────────────
def typewriter_option(text, delay=0.014):
    """Print a single menu option with typewriter reveal."""
    sys.stdout.write(f"{R.PURPLE}  ➤ {R.RESET}")
    sys.stdout.flush()
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()


def typewriter_header(text, color=R.GOLD, delay=0.018):
    for ch in text:
        sys.stdout.write(color + ch + R.RESET)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()


# ─── Flow: generate accounts ───────────────────────────────
def generate_accounts_flow():
    global success_counter, rare_counter, couples_counter, rarity_score_threshold
    clear()
    banner()
    cpu_count = psutil.cpu_count()
    recommended_threads = min(cpu_count, 3)

    typewriter_header("🌍 Available Regions:", color=R.GOLD, delay=0.02)
    print()
    for i, region in enumerate(supported_regions, 1):
        if region == ghost_mode_region:
            typewriter_option(f"{i:>2}) GHOST Mode (BR)")
        else:
            typewriter_option(f"{i:>2}) {region}")
    print()
    typewriter_option("00) Back to Main Menu")
    typewriter_option(" 0) Exit")
    print()

    selected_region = None
    is_ghost = False
    while True:
        try:
            choice = input(f"{R.CYAN}{R.BOLD}🎯 Choose option: {R.RESET}").strip().upper()
            if choice == "00":
                return
            elif choice == "0":
                print(f"\n{accent()}{R.BOLD}👋 Thank you for using RALT Generator!{R.RESET}")
                sys.exit(0)
            elif choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(supported_regions):
                    selected_region = supported_regions[idx - 1]
                    is_ghost = (selected_region == ghost_mode_region)
                    break
                else:
                    emit_error("Invalid option.")
            elif choice in supported_regions:
                selected_region = choice
                is_ghost = (selected_region == ghost_mode_region)
                break
            elif choice == "GHOST":
                selected_region = ghost_mode_region
                is_ghost = True
                break
            else:
                emit_error("Invalid option.")
        except ValueError:
            emit_error("Invalid input.")

    clear()
    banner()
    if is_ghost:
        print(f"{R.MAGENTA}{R.BOLD}🌍 Selected: GHOST (BR){R.RESET}")
    else:
        print(f"{accent()}{R.BOLD}🌍 Selected: {selected_region}{R.RESET}")

    while True:
        try:
            account_count = int(input(f"\n{accent()}{R.BOLD}🎯 Total accounts: {R.RESET}"))
            if account_count > 0:
                break
            emit_error("Positive number required.")
        except ValueError:
            emit_error("Invalid input.")

    while True:
        account_name = input(f"\n{accent()}{R.BOLD}👤 Name prefix: {R.RESET}").strip()
        if account_name:
            break
        emit_error("Cannot be empty.")

    while True:
        password_prefix = input(f"\n{accent()}{R.BOLD}🔑 Password prefix: {R.RESET}").strip()
        if password_prefix:
            break
        emit_error("Cannot be empty.")

    while True:
        try:
            rarity_threshold = int(input(f"\n{accent()}{R.BOLD}⭐ Rarity threshold (1-10, rec 2): {R.RESET}"))
            if 1 <= rarity_threshold <= 10:
                rarity_score_threshold = rarity_threshold
                break
            emit_error("1-10 only.")
        except ValueError:
            emit_error("Invalid input.")

    while True:
        try:
            thread_count = int(input(f"\n{accent()}{R.BOLD}🧵 Threads (<5 avoids IP ban, rec {recommended_threads}): {R.RESET}"))
            if thread_count > 0:
                break
            emit_error("Must be positive.")
        except ValueError:
            emit_error("Invalid input.")

    clear()
    banner()
    if is_ghost:
        print(f"{R.MAGENTA}{R.BOLD}🚀 Starting GHOST Mode (BR){R.RESET}")
    else:
        print(f"{accent()}{R.BOLD}🚀 Starting {selected_region}{R.RESET}")
    print(f"{accent()}{R.BOLD}🎯 Target: {account_count}{R.RESET}")
    print(f"{accent()}{R.BOLD}👤 Name: {account_name}{R.RESET}")
    print(f"{accent()}{R.BOLD}🔑 Pass: {password_prefix}{R.RESET}")
    print(f"{accent()}{R.BOLD}⭐ Rarity: {rarity_score_threshold}+{R.RESET}")
    print(f"{accent()}{R.BOLD}🧵 Threads: {thread_count}{R.RESET}")
    proxy_state = f"ON ({tor_socks_proxy})" if use_tor_proxy else "OFF — DIRECT"
    print(f"{accent()}{R.BOLD}🧅 Tor: {proxy_state}{R.RESET}")
    print(f"{accent()}{R.BOLD}📁 Output: {_resolve_output_path()}{R.RESET}")
    print(f"\n{accent()}{R.BOLD}⏳ Starting in 3 seconds...{R.RESET}")
    time.sleep(3)

    success_counter = 0
    rare_counter = 0
    couples_counter = 0
    start_time = time.time()
    threads = []

    _init_output_file()

    print(f"\n{accent()}{R.BOLD}🚀 Launching {thread_count} threads...{R.RESET}\n")
    Bar.render(0, account_count, "accounts", color=R.PURPLE)

    for i in range(thread_count):
        t = threading.Thread(target=worker, args=(selected_region, account_name, password_prefix, account_count, i+1, is_ghost))
        t.daemon = True
        t.start()
        threads.append(t)

    while any(t.is_alive() for t in threads):
        time.sleep(2)
        with lock:
            current_count = success_counter
        Bar.render(current_count, account_count, "accounts", color=R.PURPLE)
        if current_count >= account_count:
            break

    for t in threads:
        t.join(timeout=5)

    Bar.finish("accounts", color=R.PURPLE)
    elapsed = time.time() - start_time

    print(f"\n{accent()}{R.BOLD}🎉 Done!{R.RESET}")
    print(f"{accent()}{R.BOLD}📊 Accounts: {success_counter}/{account_count}{R.RESET}")
    print(f"{accent()}{R.BOLD}💎 Rare: {rare_counter}{R.RESET}")
    print(f"{accent()}{R.BOLD}💑 Couples: {couples_counter}{R.RESET}")
    print(f"{accent()}{R.BOLD}⏱️ Time: {elapsed:.2f}s{R.RESET}")
    if elapsed > 0:
        print(f"{accent()}{R.BOLD}⚡ Speed: {success_counter/elapsed:.2f} acc/s{R.RESET}")
    print(f"{accent()}{R.BOLD}📁 File: {_resolve_output_path()}{R.RESET}")
    wait_for_enter()


def view_saved_accounts():
    clear()
    banner()
    print(f"{accent()}{R.BOLD}📁 Output file{R.RESET}")
    path = _resolve_output_path()
    if not os.path.exists(path):
        print(f"\n{R.WARN}{R.BOLD}📭 Not created yet.{R.RESET}")
        wait_for_enter()
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.splitlines()
        preview = "\n".join(lines[:80])
        print(f"\n{R.SILVER}{preview}{R.RESET}")
        if len(lines) > 80:
            print(f"{R.GRAY}... {len(lines) - 80} more lines in {path}{R.RESET}")
    except Exception as err:
        emit_error(f"Read failed: {err}")
    wait_for_enter()


def about_section():
    clear()
    banner()
    print(f"{accent()}{R.BOLD}ℹ️  About RALT Generator{R.RESET}")
    info = _get_build_info()
    print(f"\n{accent()}{R.BOLD}📦 Build:{R.RESET}")
    print(f"{accent()}• Project: {info['project']} v{info['version']}{R.RESET}")
    print(f"{accent()}• Author: {info['author']}{R.RESET}")
    print(f"{accent()}• Owner: {info['owner']}{R.RESET}")
    print(f"{accent()}• Channel: {info['channel']}{R.RESET}")
    print(f"\n{accent()}{R.BOLD}✨ Features:{R.RESET}")
    print(f"{accent()}• Multi-region FF account generation{R.RESET}")
    print(f"{accent()}• Region binding via Activator API{R.RESET}")
    print(f"{accent()}• Tor IP rotation every {rotation_threshold} errors{R.RESET}")
    print(f"{accent()}• Multi-threaded{R.RESET}")
    print(f"{accent()}• Single output: {_resolve_output_path()}{R.RESET}")
    print(f"\n{accent()}{R.BOLD}🔗 Activator API:{R.RESET}")
    print(f"{accent()}• {activator_api_url}{R.RESET}")
    print(f"\n{accent()}{R.BOLD}🧅 Tor:{R.RESET}")
    print(f"{accent()}• {tor_socks_proxy}{R.RESET}")
    print(f"{accent()}• Setup budget: {int(tor_setup_timeout)}s{R.RESET}")
    wait_for_enter()


def help_section():
    clear()
    banner()
    print(f"{accent()}{R.BOLD}❓ HELP{R.RESET}")
    print(f"{R.GRAY}{'─' * 66}{R.RESET}")
    print(f"\n{accent()}{R.BOLD}📁 Output:{R.RESET}")
    print(f"{accent()}• All accounts → {_resolve_output_path()}{R.RESET}")
    print(f"{accent()}• Blocks marked NORMAL / RARE / COUPLE.{R.RESET}")
    print(f"\n{accent()}{R.BOLD}🧅 Tor:{R.RESET}")
    print(f"{accent()}• Auto-installs, auto-starts on 127.0.0.1:9050{R.RESET}")
    print(f"{accent()}• {int(tor_setup_timeout)}s setup budget, DIRECT fallback.{R.RESET}")
    print(f"{accent()}• Rotates IP after {rotation_threshold} errors.{R.RESET}")
    print(f"\n{accent()}{R.BOLD}👻 Ghost Mode:{R.RESET}")
    print(f"{accent()}• BR region, no API, no JWT.{R.RESET}")
    print(f"\n{accent()}{R.BOLD}💡 Tips:{R.RESET}")
    print(f"{accent()}• 3–5 threads to lower ban risk.{R.RESET}")
    print(f"{accent()}• Higher rarity threshold → fewer Rare flags.{R.RESET}")
    wait_for_enter()


def main_menu():
    while True:
        clear()
        banner()
        typewriter_header("🎮 Welcome to RALT Account Generator", color=R.GOLD, delay=0.02)
        print()
        typewriter_header("📋 Options:", color=R.CYAN, delay=0.018)
        print()
        typewriter_option("1) Generate Accounts")
        typewriter_option("2) View Output File")
        typewriter_option("3) About")
        typewriter_option("4) Help")
        typewriter_option("0) Exit")
        print()
        try:
            choice = input(f"{R.CYAN}{R.BOLD}🎯 Choose option: {R.RESET}").strip()
            if choice == "1":
                generate_accounts_flow()
            elif choice == "2":
                view_saved_accounts()
            elif choice == "3":
                about_section()
            elif choice == "4":
                help_section()
            elif choice == "0":
                print(f"\n{accent()}{R.BOLD}👋 Thank you for using RALT Generator!{R.RESET}")
                sys.exit(0)
            else:
                emit_error("Invalid option.")
                time.sleep(1)
        except (EOFError, KeyboardInterrupt):
            pass


if __name__ == "__main__":
    try:
        _print_build_banner()
        sync_config()
        if use_tor_proxy:
            start_tor()
        if use_tor_proxy:
            emit_success("Boot complete — Tor active")
        else:
            emit_warning("Boot complete — DIRECT mode")
        main_menu()
    except SystemExit:
        raise
    except Exception as err:
        emit_error(f"Unexpected error: {err}")
        print(f"\n{R.WARN}{R.BOLD}🔄 Restarting script...{R.RESET}")
        time.sleep(2)
        os.execv(sys.executable, [sys.executable] + sys.argv)
