#!/usr/bin/env python3
"""
PUZZLE-CAM Local HTTPS Server
=============================
Serves the PUZZLE-CAM application over local HTTPS with self-signed SSL certificates.
Optimized for Windows Mobile Hotspot and local Wi-Fi offline setups.

Features:
- Auto-generates self-signed SSL certificate (cert.pem & key.pem) with SAN for all local IPs.
- Auto-detects local network IP (prioritizing Windows Mobile Hotspot 192.168.137.x).
- Displays terminal ASCII QR code for fast mobile connection.
- Serves MediaPipe WASM and TFLite files with correct MIME types & CORS headers.
"""

import os
import sys
import socket
import ssl
import subprocess
import re
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import datetime
import ipaddress

# Ensure terminal stdout handles UTF-8 (crucial on Windows for QR code display)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def find_local_ips():
    """Detect non-loopback IPv4 addresses on the host machine.
    Prioritizes Windows Mobile Hotspot (192.168.137.x), followed by standard Wi-Fi/LAN.
    """
    detected_ips = []
    
    # 1. Try socket.gethostbyname_ex
    try:
        hostname = socket.gethostname()
        _, _, ip_list = socket.gethostbyname_ex(hostname)
        for ip in ip_list:
            if ip not in detected_ips and not ip.startswith("127.") and not ip.startswith("169.254."):
                detected_ips.append(ip)
    except Exception:
        pass

    # 2. Try parsing ipconfig on Windows
    if sys.platform == "win32":
        try:
            output = subprocess.check_output("ipconfig", text=True, stderr=subprocess.DEVNULL)
            matches = re.findall(r"IPv4 Address[ .]+: ([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", output)
            for ip in matches:
                if ip not in detected_ips and not ip.startswith("127.") and not ip.startswith("169.254."):
                    detected_ips.append(ip)
        except Exception:
            pass

    # 3. Fallback: UDP connect dummy socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Doesn't actually send packets
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip not in detected_ips and not ip.startswith("127.") and not ip.startswith("169.254."):
            detected_ips.append(ip)
    except Exception:
        pass

    if not detected_ips:
        detected_ips = ["127.0.0.1"]

    # Sort IPs by priority:
    # 1. 192.168.137.x (Windows Mobile Hotspot default)
    # 2. Common LAN / Wi-Fi subnets (192.168.1.x, 192.168.0.x, 10.x.x.x, 172.16-31.x.x)
    # 3. Virtual adapters (192.168.56.x VirtualBox, etc.)
    def ip_priority(ip):
        if ip.startswith("192.168.137."):
            return 0
        if ip.startswith("192.168.") and not ip.startswith("192.168.56."):
            return 1
        if ip.startswith("10.") or ip.startswith("172."):
            return 2
        if ip.startswith("192.168.56."):
            return 4
        return 3

    detected_ips.sort(key=ip_priority)
    return detected_ips


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CERT_FILE = os.path.join(BASE_DIR, "cert.pem")
DEFAULT_KEY_FILE = os.path.join(BASE_DIR, "key.pem")


def generate_ssl_certificates(cert_path=None, key_path=None, ip_list=None):
    """Generate self-signed SSL certificate with SAN (Subject Alternative Names)
    covering localhost and all detected IP addresses.
    """
    if cert_path is None:
        cert_path = DEFAULT_CERT_FILE
    elif not os.path.isabs(cert_path):
        cert_path = os.path.join(BASE_DIR, cert_path)

    if key_path is None:
        key_path = DEFAULT_KEY_FILE
    elif not os.path.isabs(key_path):
        key_path = os.path.join(BASE_DIR, key_path)

    if os.path.exists(cert_path) and os.path.exists(key_path):
        print(f"[*] Found existing SSL certificates ({cert_path}, {key_path}).")
        return True

    print("[*] Generating new self-signed SSL certificate...")
    if ip_list is None:
        ip_list = find_local_ips()

    # Try using cryptography package
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        primary_ip = ip_list[0] if ip_list else "127.0.0.1"

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Offline"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Hotspot"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PuzzleCam"),
            x509.NameAttribute(NameOID.COMMON_NAME, primary_ip),
        ])

        san_list = [
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
        ]
        for ip in ip_list:
            try:
                addr = ipaddress.ip_address(ip)
                if addr not in [x.value for x in san_list if isinstance(x, x509.IPAddress)]:
                    san_list.append(x509.IPAddress(addr))
            except Exception:
                pass

        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=3650))  # 10 years validity
            .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
            .sign(key, hashes.SHA256())
        )

        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        print(f"[+] Successfully generated SSL certificates using cryptography:")
        print(f"    - Certificate: {os.path.abspath(cert_path)}")
        print(f"    - Private Key: {os.path.abspath(key_path)}")
        return True

    except ImportError:
        print("[!] 'cryptography' package not found. Attempting OpenSSL fallback...")

    # Fallback to OpenSSL executable if cryptography not available
    openssl_bins = ["openssl", r"C:\Program Files\Git\usr\bin\openssl.exe"]
    openssl_cmd = None
    for b in openssl_bins:
        try:
            res = subprocess.run([b, "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                openssl_cmd = b
                break
        except Exception:
            continue

    if openssl_cmd:
        try:
            cmd = [
                openssl_cmd, "req", "-x509", "-newkey", "rsa:2048",
                "-keyout", key_path, "-out", cert_path,
                "-days", "3650", "-nodes",
                "-subj", f"/C=US/ST=Offline/L=Hotspot/O=PuzzleCam/CN={ip_list[0] if ip_list else 'localhost'}"
            ]
            subprocess.check_call(cmd)
            print(f"[+] Generated SSL certificates via {openssl_cmd}")
            return True
        except Exception as e:
            print(f"[!] OpenSSL command failed: {e}")

    print("[X] Error: Failed to generate SSL certificates. Please install cryptography: pip install cryptography")
    return False


def display_qr_code(url):
    """Render an ASCII QR code in the terminal for fast scanning with phone camera."""
    print("\n" + "=" * 60)
    print(" SCAN WITH YOUR SMARTPHONE CAMERA TO OPEN PUZZLE-CAM:")
    print("=" * 60)
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        # Use ascii representation with invert=True for typical dark terminal backgrounds
        qr.print_ascii(invert=True)
    except Exception as e:
        print(f"[Notice] ASCII QR code display error: {e}")
        print("Please enter the URL directly in your phone browser:")
    print("=" * 60 + "\n")


class PuzzleCamHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP Request Handler with proper MIME types, CORS headers,
    and cache policies for MediaPipe assets and audio.
    """
    extensions_map = SimpleHTTPRequestHandler.extensions_map.copy()
    extensions_map.update({
        ".wasm": "application/wasm",
        ".tflite": "application/octet-stream",
        ".binarypb": "application/octet-stream",
        ".data": "application/octet-stream",
        ".js": "application/javascript",
        ".mjs": "application/javascript",
        ".json": "application/json",
        ".css": "text/css",
        ".html": "text/html",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
    })

    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            directory = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self):
        # Enable CORS for cross-origin asset loading
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        # Do not cache during active development
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format, *args):
        # Clean terminal logging
        sys.stderr.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {self.address_string()} - {format % args}\n")


class ReusableHTTPServer(HTTPServer):
    """HTTPServer with socket reuse enabled to prevent address binding errors."""
    allow_reuse_address = True


def start_server(host="0.0.0.0", port=8443, cert_file=None, key_file=None, show_qr=True):
    """Starts the HTTPS server and prints access links."""
    # Resolve relative cert/key paths relative to caller's cwd before chdir
    if cert_file is not None and not os.path.isabs(cert_file):
        cert_file = os.path.abspath(cert_file)
    elif cert_file is None:
        cert_file = DEFAULT_CERT_FILE

    if key_file is not None and not os.path.isabs(key_file):
        key_file = os.path.abspath(key_file)
    elif key_file is None:
        key_file = DEFAULT_KEY_FILE

    os.chdir(BASE_DIR)

    ip_list = find_local_ips()
    primary_ip = ip_list[0]

    if not generate_ssl_certificates(cert_file, key_file, ip_list):
        sys.exit(1)

    server_address = (host, port)
    httpd = ReusableHTTPServer(server_address, PuzzleCamHTTPRequestHandler)

    # Wrap socket with SSLContext (Python 3.11+ standard)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=cert_file, keyfile=key_file)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    primary_url = f"https://{primary_ip}:{port}/"

    print("\n" + "#" * 60)
    print("  PUZZLE-CAM (Hand-Frame Capture) SERVER IS READY!")
    print("#" * 60)
    print(f"\n[+] Server running locally on: https://localhost:{port}/")
    print(f"[+] PRIMARY MOBILE HOTSPOT URL : {primary_url}")
    
    if len(ip_list) > 1:
        print("\n[+] Other detected network interfaces:")
        for other_ip in ip_list[1:]:
            print(f"    -> https://{other_ip}:{port}/")

    if show_qr:
        display_qr_code(primary_url)

    print("-" * 60)
    print(" IMPORTANT MOBILE CONNECTION INSTRUCTIONS:")
    print(" 1. Connect your smartphone to this PC's Wi-Fi Hotspot or local Wi-Fi.")
    print(f" 2. Open Chrome, Safari, or Brave and go to: {primary_url}")
    print(" 3. SSL WARNING ON PHONE:")
    print('    Tap "Advanced" (or "Details") -> Tap "Proceed to ... (unsafe)".')
    print("    (This is standard for self-signed certificates on local offline networks).")
    print(' 4. Allow Camera permission when prompted.')
    print(" 5. Press Ctrl+C in this terminal to stop the server.")
    print("-" * 60 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down PUZZLE-CAM server gracefully...")
        httpd.server_close()
        print("[+] Server stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PUZZLE-CAM Local HTTPS Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8443, help="Port to bind to (default: 8443)")
    parser.add_argument("--cert", default=None, help="SSL certificate path (default: cert.pem in project folder)")
    parser.add_argument("--key", default=None, help="SSL private key path (default: key.pem in project folder)")
    parser.add_argument("--no-qr", action="store_true", help="Disable terminal QR code")
    args = parser.parse_args()

    start_server(
        host=args.host,
        port=args.port,
        cert_file=args.cert,
        key_file=args.key,
        show_qr=not args.no_qr
    )
