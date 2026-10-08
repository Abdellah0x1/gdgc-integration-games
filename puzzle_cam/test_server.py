import os
import sys
import time
import urllib.request
import ssl
import subprocess
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

def test_cert_generation():
    print("[*] Testing generate_ssl_certificates in isolated directory...")
    sys.path.insert(0, BASE_DIR)
    from server import generate_ssl_certificates, find_local_ips
    from cryptography import x509

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_cert = os.path.join(tmpdir, "test_cert.pem")
        tmp_key = os.path.join(tmpdir, "test_key.pem")
        
        ok = generate_ssl_certificates(tmp_cert, tmp_key)
        assert ok, "Failed to generate SSL certificates in tempdir"
        assert os.path.exists(tmp_cert), "Certificate file missing"
        assert os.path.exists(tmp_key), "Key file missing"

        with open(tmp_cert, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
            san_ext = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            sans = [str(x.value) for x in san_ext.value]
            print(f"[+] Generated cert SANs: {sans}")
            assert "localhost" in sans, "localhost missing from SANs"
            assert "127.0.0.1" in sans, "127.0.0.1 missing from SANs"
    print("[SUCCESS] Certificate generation verified.")


def test_https_server():
    server_script = os.path.join(BASE_DIR, "server.py")
    test_port = 8446
    print(f"[*] Starting server subprocess on port {test_port} for testing...")
    
    proc = subprocess.Popen(
        [sys.executable, server_script, "--port", str(test_port), "--no-qr"],
        cwd=BASE_DIR
    )

    try:
        time.sleep(2)  # Give server time to bind and start
        
        # Create unverified SSL context (since cert is self-signed)
        ctx = ssl._create_unverified_context()

        endpoints = [
            ("/", 200, "text/html"),
            ("/style.css", 200, "text/css"),
            ("/app.js", 200, "application/javascript"),
            ("/logo.png", 200, "image/png"),
            ("/vendor/mediapipe/camera_utils.js", 200, "application/javascript"),
            ("/vendor/mediapipe/drawing_utils.js", 200, "application/javascript"),
            ("/vendor/mediapipe/hands.js", 200, "application/javascript"),
            ("/vendor/mediapipe/hands.binarypb", 200, "application/octet-stream"),
            ("/vendor/mediapipe/hands_solution_wasm_bin.wasm", 200, "application/wasm"),
            ("/vendor/mediapipe/hands_solution_packed_assets.data", 200, "application/octet-stream"),
            ("/vendor/mediapipe/hands_solution_packed_assets_loader.js", 200, "application/javascript"),
            ("/vendor/mediapipe/hands_solution_wasm_bin.js", 200, "application/javascript"),
            ("/vendor/mediapipe/hands_solution_simd_wasm_bin.js", 200, "application/javascript"),
            ("/vendor/mediapipe/hands_solution_simd_wasm_bin.wasm", 200, "application/wasm"),
            ("/vendor/mediapipe/hand_landmark_full.tflite", 200, "application/octet-stream"),
            ("/vendor/mediapipe/hand_landmark_lite.tflite", 200, "application/octet-stream"),
            ("/vendor/mediapipe/face_mesh.js", 200, "application/javascript"),
            ("/vendor/mediapipe/face_mesh.binarypb", 200, "application/octet-stream"),
            ("/vendor/mediapipe/face_mesh_solution_wasm_bin.wasm", 200, "application/wasm"),
            ("/vendor/mediapipe/face_mesh_solution_packed_assets.data", 200, "application/octet-stream"),
        ]

        all_passed = True

        # 1. Test GET requests and headers
        print("\n[*] Testing GET requests...")
        for path, expected_status, expected_mime in endpoints:
            url = f"https://127.0.0.1:{test_port}{path}"
            req = urllib.request.Request(url)
            try:
                with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                    status = response.status
                    content_type = response.headers.get("Content-Type", "")
                    cors_origin = response.headers.get("Access-Control-Allow-Origin", "")
                    cache_ctrl = response.headers.get("Cache-Control", "")
                    data = response.read()

                    if status != expected_status or expected_mime not in content_type:
                        print(f"[X] MISMATCH on {path}: expected ({expected_status}, {expected_mime}), got ({status}, {content_type})")
                        all_passed = False
                    elif cors_origin != "*":
                        print(f"[X] CORS MISMATCH on {path}: expected Access-Control-Allow-Origin: *")
                        all_passed = False
                    elif "no-cache" not in cache_ctrl:
                        print(f"[X] Cache-Control missing no-cache on {path}")
                        all_passed = False
                    else:
                        print(f"[+] GET {path} -> Status: {status}, MIME: {content_type}, Size: {len(data)} bytes")
            except Exception as e:
                print(f"[X] FAILED {path}: {e}")
                all_passed = False

        # 2. Test HEAD request (critical for app.js probe)
        print("\n[*] Testing HEAD request...")
        head_url = f"https://127.0.0.1:{test_port}/vendor/mediapipe/hands.binarypb"
        req = urllib.request.Request(head_url, method="HEAD")
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                status = response.status
                content_type = response.headers.get("Content-Type", "")
                content_length = int(response.headers.get("Content-Length", 0))
                print(f"[+] HEAD /vendor/mediapipe/hands.binarypb -> Status: {status}, Content-Length: {content_length}")
                if status != 200 or content_length != 550 or "application/octet-stream" not in content_type:
                    print("[X] HEAD probe verification failed")
                    all_passed = False
        except Exception as e:
            print(f"[X] HEAD request failed: {e}")
            all_passed = False

        # 3. Test OPTIONS request (CORS preflight)
        print("\n[*] Testing OPTIONS request...")
        opt_url = f"https://127.0.0.1:{test_port}/vendor/mediapipe/hands_solution_wasm_bin.wasm"
        req = urllib.request.Request(opt_url, method="OPTIONS")
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                status = response.status
                methods = response.headers.get("Access-Control-Allow-Methods", "")
                print(f"[+] OPTIONS -> Status: {status}, Allow-Methods: {methods}")
                if status != 200 or "HEAD" not in methods or "GET" not in methods:
                    print("[X] OPTIONS verification failed")
                    all_passed = False
        except Exception as e:
            print(f"[X] OPTIONS request failed: {e}")
            all_passed = False

        if not all_passed:
            print("\n[FAIL] Some endpoint verifications failed.")
            sys.exit(1)

        print("\n[SUCCESS] All HTTPS endpoints, MIME types, HEAD, OPTIONS, and CORS headers verified successfully!")

    finally:
        print("[*] Terminating server subprocess...")
        proc.terminate()
        proc.wait()
        print("[*] Server terminated.")


def test_parent_cleanliness():
    print("\n[*] Verifying parent directory cleanliness...")
    parent_items = os.listdir(PARENT_DIR)
    print(f"Items in parent directory ({PARENT_DIR}): {parent_items}")
    assert parent_items == ["puzzle_cam"], f"Parent directory contains unexpected items: {parent_items}"
    print("[SUCCESS] Parent directory is completely clean.")


if __name__ == "__main__":
    test_cert_generation()
    test_https_server()
    test_parent_cleanliness()
    print("\n[ALL TESTS PASSED]")
