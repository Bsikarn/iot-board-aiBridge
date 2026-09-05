# network_mod.py
import requests
import subprocess
import os
import re
import time
import threading
import socket
from PIL import Image

BOARD_SECRET_KEY = "bseqaluvtksgifkrphab"

class EducationalNetwork:
    def __init__(self, vercel_url):
        self.vercel_url = vercel_url
        if "/api/ask" in vercel_url:
            self.settings_url = vercel_url.replace("/api/ask", "/api/settings")
            self.wifi_sync_url = vercel_url.replace("/api/ask", "/api/wifi-settings")
        else:
            base = vercel_url.rstrip("/")
            self.settings_url = f"{base}/api/settings"
            self.wifi_sync_url = f"{base}/api/wifi-settings"

        self.headers = {
            "x-board-key": BOARD_SECRET_KEY
        }

        # Background Thread ส่ง Heartbeat เลี้ยง Hotspot iPhone ไม่ให้ตัด
        self.start_keep_alive()

    def start_keep_alive(self):
        """ส่ง Ping ขนาดจิ๋ว (~60 Bytes) ทุก 30 วินาที เพื่อไม่ให้ Hotspot iPhone หลับ"""
        def _heartbeat_worker():
            while True:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(3)
                    s.connect(("1.1.1.1", 53))
                    s.close()
                except Exception:
                    pass
                time.sleep(30)

        t = threading.Thread(target=_heartbeat_worker, daemon=True)
        t.start()

    def capture_image(self, step=1):
        """ถ่ายภาพและหมุนภาพ 90 องศา (270° CCW) ให้ตั้งตรงอัตโนมัติก่อนบันทึก"""
        temp_raw = f"/dev/shm/raw_snap_{step}.jpg"
        temp_final = f"/dev/shm/edu_snap_{step}.jpg"
        
        captured = False
        try:
            subprocess.run(["rpicam-still", "-n", "-o", temp_raw, "--immediate", "--width", "800", "--height", "600"], check=True)
            captured = True
        except Exception:
            try:
                subprocess.run(["libcamera-still", "-n", "-o", temp_raw, "--immediate", "--width", "800", "--height", "600"], check=True)
                captured = True
            except Exception:
                captured = False

        if captured and os.path.exists(temp_raw):
            try:
                img = Image.open(temp_raw)
                rotated = img.rotate(270, expand=True)
                rotated.save(temp_final, "JPEG", quality=85)
                return temp_final
            except Exception as e:
                print(f"⚠️ Rotation error: {e}")
                return temp_raw
        return None

    def fetch_settings(self):
        try:
            res = requests.get(self.settings_url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"⚠️ fetch_settings error: {e}")
        return None

    def get_current_wifi_ssid(self):
        try:
            result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True, check=True)
            ssid = result.stdout.strip()
            if ssid:
                return ssid
        except Exception:
            try:
                res = subprocess.run(['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'], capture_output=True, text=True, check=True)
                for line in res.stdout.splitlines():
                    if line.startswith('yes:'):
                        return line.split(':', 1)[1]
            except Exception:
                pass
        return "Offline"

    def get_local_saved_wifis(self):
        saved_networks = []
        seen_ssids = set()

        try:
            res = subprocess.run(['sudo', 'nmcli', '-t', '-f', 'NAME,TYPE', 'connection', 'show'], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if ':802-11-wireless' in line or ':wifi' in line:
                        ssid = line.split(':', 1)[0].strip()
                        if ssid and ssid not in seen_ssids:
                            psk = ""
                            try:
                                psk_res = subprocess.run(['sudo', 'nmcli', '-s', '-g', '802-11-wireless-security.psk', 'connection', 'show', ssid], capture_output=True, text=True, timeout=3)
                                if psk_res.returncode == 0 and psk_res.stdout.strip():
                                    psk = psk_res.stdout.strip()
                            except Exception:
                                pass
                            seen_ssids.add(ssid)
                            saved_networks.append({"ssid": ssid, "password": psk})
        except Exception as e:
            print(f"⚠️ nmcli query info: {e}")

        if not saved_networks:
            wpa_path = "/etc/wpa_supplicant/wpa_supplicant.conf"
            if os.path.exists(wpa_path):
                try:
                    res = subprocess.run(['sudo', 'cat', wpa_path], capture_output=True, text=True, timeout=3)
                    if res.returncode == 0 and res.stdout:
                        content = res.stdout
                        matches = re.findall(r'network=\{([^}]+)\}', content, re.DOTALL)
                        for block in matches:
                            ssid_match = re.search(r'ssid="([^"]+)"', block)
                            psk_match = re.search(r'psk="([^"]+)"', block)
                            if ssid_match:
                                ssid = ssid_match.group(1).strip()
                                psk = psk_match.group(1).strip() if psk_match else ""
                                if ssid and ssid not in seen_ssids:
                                    seen_ssids.add(ssid)
                                    saved_networks.append({"ssid": ssid, "password": psk})
                except Exception as e:
                    print(f"⚠️ Error reading wpa_supplicant: {e}")

        current_ssid = self.get_current_wifi_ssid()
        if current_ssid and current_ssid not in ["Offline", "No Wi-Fi", "Unknown"]:
            if current_ssid not in seen_ssids:
                seen_ssids.add(current_ssid)
                saved_networks.append({"ssid": current_ssid, "password": ""})

        return saved_networks

    def sync_wifi_from_web(self):
        current_ssid = self.get_current_wifi_ssid()
        try:
            res = requests.get(self.wifi_sync_url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                wifi_list = []
                if isinstance(data, list):
                    wifi_list = data
                elif isinstance(data, dict):
                    wifi_list = data.get("wifi", data.get("networks", data.get("profiles", [])))
                
                web_ssids = [item.get("ssid", item.get("name", "")) for item in wifi_list if isinstance(item, dict)]
                
                if current_ssid not in ["Offline", "No Wi-Fi", "Unknown"]:
                    if current_ssid not in web_ssids:
                        return False, "Active SSID Missing", len(wifi_list)

                return True, "Sync Success", len(wifi_list)
            elif res.status_code == 401:
                return False, "401 Unauthorized", 0
        except Exception as e:
            print(f"⚠️ sync_wifi_from_web error: {e}")
        return False, "Server Error", 0

    def update_wifi_to_web(self):
        local_wifis = self.get_local_saved_wifis()
        payload = {
            "networks": local_wifis,
            "wifi": local_wifis
        }
        try:
            res = requests.post(self.wifi_sync_url, json=payload, headers=self.headers, timeout=10)
            if res.status_code in [200, 201]:
                return True, len(local_wifis)
        except Exception as e:
            print(f"⚠️ update_wifi_to_web error: {e}")
        return False, len(local_wifis)

    def post_to_api(self, image_paths, slot_idx, model_idx, kb_idx, progress_callback=None):
        payload = {
            "prompt_index": str(slot_idx),
            "ai_index": str(model_idx),
            "model_index": str(model_idx),
            "kb_index": str(kb_idx)
        }
        
        if isinstance(image_paths, str):
            image_paths = [image_paths]

        opened_files = []
        files = []
        try:
            for idx, p in enumerate(image_paths):
                if p and os.path.exists(p):
                    f = open(p, 'rb')
                    opened_files.append(f)
                    files.append((f'image_{idx + 1}', (f'snap_{idx + 1}.jpg', f, 'image/jpeg')))

            if not files:
                return {"reply": "Error: Images missing."}

            response = requests.post(self.vercel_url, data=payload, files=files, headers=self.headers, timeout=30)
            if response.status_code not in [200, 202]:
                return {"reply": f"Server Error: {response.status_code}"}

            if progress_callback:
                progress_callback("sent")

            res_data = response.json()
            task_id = res_data.get("task_id")

            if not task_id and "pages" in res_data:
                return res_data

            if not task_id:
                return {"reply": "Error: No task_id returned from server."}

            status_url = self.vercel_url.replace("/api/ask", "/api/status")
            start_time = time.time()
            max_wait_seconds = 600

            print(f"⏳ [Task Started]: ID = {task_id}, Polling results...")

            while (time.time() - start_time) < max_wait_seconds:
                time.sleep(3)
                try:
                    poll_res = requests.get(f"{status_url}?task_id={task_id}", headers=self.headers, timeout=10)
                    if poll_res.status_code == 200:
                        poll_data = poll_res.json()
                        status = poll_data.get("status")
                        step = poll_data.get("step")

                        if progress_callback and step:
                            progress_callback(step)

                        if status == "completed":
                            print("✅ [Task Completed]: Received AI response pages!")
                            return poll_data
                        elif status == "failed":
                            return {"reply": f"AI Failed: {poll_data.get('error', 'Unknown error')}"}
                        else:
                            print(f"🔄 [Processing...]: Step = {step}, Elapsed {int(time.time() - start_time)}s")
                except Exception as poll_err:
                    print(f"⚠️ Polling tick error: {poll_err}")

            return {"reply": "Timeout: AI took more than 10 minutes to finish."}

        except Exception as e:
            return {"reply": f"Connect Error: {e}"}
        finally:
            for f in opened_files:
                try:
                    f.close()
                except Exception:
                    pass