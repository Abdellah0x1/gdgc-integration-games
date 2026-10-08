#!/usr/bin/env python3
"""
GDG ENSAF Drawing Cam — Local HTTPS Server
===========================================
Serves the GDG AR Drawing web application over local HTTPS with self-signed SSL certificates.
Optimized for mobile browsers on PC Hotspot and local Wi-Fi offline setups.

Features:
- Auto-generates self-signed SSL certificate (cert.pem & key.pem) with SAN for all local IPs.
- Auto-detects local network IP (prioritizing Windows Mobile Hotspot 192.168.137.x).
- Displays terminal ASCII QR code for fast mobile connection.
- Serves MediaPipe WASM and model files with proper MIME types & CORS headers.
- Default port: 8445 (can run simultaneously alongside puzzle_cam on 8443).
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

    # 2. On Windows: inspect ipconfig for hotspot adapter
    if sys.platform == "win32":
        try:
            output = subprocess.check_output("ipconfig", text=True, encoding="cp437", errors="ignore")
            matches = re.findall(r"IPv4 Address[.\s]+:\s+([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", output)
            for ip in matches:
                if ip not in detected_ips and not ip.startswith("127.") and not ip.startswith("169.254."):
                    detected_ips.append(ip)
        except Exception:
            pass

    # Sort IPs:
    # 1. Windows Mobile Hotspot (192.168.137.x)
    # 2. Common LAN / Wi-Fi subnets
    # 3. Virtual adapters
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
    """Generate self-signed SSL certificate with SAN covering localhost and local IPs."""
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

        # Generate RSA private key
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Build Subject Alternative Names
        san_entries = [
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]
        for ip in ip_list:
            try:
                san_entries.append(x509.IPAddress(ipaddress.IPv4Address(ip)))
            except Exception:
                pass

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Offline"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Hotspot"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "GDG ENSAF"),
            x509.NameAttribute(NameOID.COMMON_NAME, ip_list[0] if ip_list else "localhost"),
        ])

        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=3650))
            .add_extension(
                x509.SubjectAlternativeName(san_entries),
                critical=False,
            )
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .sign(key, hashes.SHA256())
        )

        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))

        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        print(f"[+] Successfully generated SSL certificates using cryptography:")
        print(f"    - Certificate: {cert_path}")
        print(f"    - Private Key: {key_path}")
        return True

    except ImportError:
        print("[!] cryptography package not found. Attempting OpenSSL fallback...")

    # Fallback to OpenSSL CLI
    openssl_candidates = ["openssl", r"C:\Program Files\Git\usr\bin\openssl.exe"]
    openssl_cmd = None
    for cand in openssl_candidates:
        try:
            res = subprocess.run([cand, "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode == 0:
                openssl_cmd = cand
                break
        except Exception:
            continue

    if openssl_cmd:
        try:
            cmd = [
                openssl_cmd, "req", "-x509", "-newkey", "rsa:2048",
                "-keyout", key_path, "-out", cert_path,
                "-days", "3650", "-nodes",
                "-subj", f"/C=US/ST=Offline/L=Hotspot/O=GDGENSAF/CN={ip_list[0] if ip_list else 'localhost'}"
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
    print(" SCAN WITH YOUR SMARTPHONE CAMERA TO OPEN GDG DRAWING CAM:")
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
        qr.print_ascii(invert=True)
    except Exception as e:
        print(f"[Notice] ASCII QR code display error: {e}")
        print("Please enter the URL directly in your phone browser:")
    print("=" * 60 + "\n")


class DrawingCamHTTPRequestHandler(SimpleHTTPRequestHandler):
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

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def start_server(host="0.0.0.0", port=8445, cert_file=None, key_file=None, show_qr=True):
    base_dir = BASE_DIR
    
    if cert_file is not None:
        cert_file = os.path.abspath(cert_file)
    else:
        cert_file = DEFAULT_CERT_FILE

    if key_file is not None:
        key_file = os.path.abspath(key_file)
    else:
        key_file = DEFAULT_KEY_FILE

    os.chdir(base_dir)

    ip_list = find_local_ips()
    primary_ip = ip_list[0] if ip_list else "127.0.0.1"

    if not (os.path.exists(cert_file) and os.path.exists(key_file)):
        ok = generate_ssl_certificates(cert_file, key_file, ip_list)
        if not ok:
            print("[X] Could not establish SSL certificates. Exiting.")
            sys.exit(1)

    server_address = (host, port)
    httpd = ReusableHTTPServer(server_address, DrawingCamHTTPRequestHandler)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=cert_file, keyfile=key_file)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    primary_url = f"https://{primary_ip}:{port}/"
    localhost_url = f"https://localhost:{port}/"

    print("\n" + "=" * 60)
    print(" 🎨 GDG ENSAF DRAWING CAM SERVER RUNNING (HTTPS)")
    print("=" * 60)
    print(f" [*] Local PC URL:       {localhost_url}")
    print(f" [*] Mobile Hotspot URL: {primary_url}")
    if len(ip_list) > 1:
        print("\n [+] Other detected network interfaces:")
        for other_ip in ip_list[1:]:
            print(f"     -> https://{other_ip}:{port}/")

    if show_qr:
        display_qr_code(primary_url)

    print("-" * 60)
    print(" IMPORTANT MOBILE CONNECTION INSTRUCTIONS:")
    print(" 1. Connect your smartphone to this PC's Wi-Fi Hotspot.")
    print(f" 2. Open Chrome, Safari, or Brave and go to: {primary_url}")
    print(" 3. SSL WARNING ON PHONE:")
    print('    Tap "Advanced" (or "Details") -> Tap "Proceed to ... (unsafe)".')
    print(" 4. Allow Camera permission when prompted.")
    print(" 5. Press Ctrl+C in this terminal to stop the server.")
    print("-" * 60 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down GDG Drawing Cam server gracefully...")
        httpd.server_close()
        print("[+] Server stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GDG ENSAF Drawing Cam HTTPS Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8445, help="Port to bind to (default: 8445)")
    parser.add_argument("--cert", default=None, help="SSL certificate path (default: cert.pem in module dir)")
    parser.add_argument("--key", default=None, help="SSL private key path (default: key.pem in module dir)")
    parser.add_argument("--no-qr", action="store_true", help="Disable terminal QR code")
    args = parser.parse_args()

    start_server(
        host=args.host,
        port=args.port,
        cert_file=args.cert,
        key_file=args.key,
        show_qr=not args.no_qr
    )

