# network_mod.py
import requests
import subprocess
import os
import re

# Secret key for board authentication with Vercel API
BOARD_SECRET_KEY = ""

class EducationalNetwork:
    def __init__(self, vercel_url=""):
        self.vercel_url = vercel_url
        if vercel_url and "/api/ask" in vercel_url:
            self.settings_url = vercel_url.replace("/api/ask", "/api/settings")
            self.wifi_sync_url = vercel_url.replace("/api/ask", "/api/wifi-settings")
        elif vercel_url:
            base = vercel_url.rstrip("/")
            self.settings_url = f"{base}/api/settings"
            self.wifi_sync_url = f"{base}/api/wifi-settings"
        else:
            self.settings_url = ""
            self.wifi_sync_url = ""

        # Attach secret header to authorize requests
        self.headers = {
            "x-board-key": BOARD_SECRET_KEY
        }

    def capture_image(self):
        temp_path = "/dev/shm/edu_snap.jpg"
        try:
            subprocess.run(["rpicam-still", "-n", "-o", temp_path, "--immediate", "--width", "800", "--height", "600"], check=True)
            return temp_path
        except Exception:
            try:
                subprocess.run(["libcamera-still", "-n", "-o", temp_path, "--immediate", "--width", "800", "--height", "600"], check=True)
                return temp_path
            except Exception:
                return None

    def fetch_settings(self):
        """Fetch all mappings from server with authorization headers."""
        if not self.settings_url:
            return None
        try:
            res = requests.get(self.settings_url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                print(f"📡 [Settings Fetched Successfully]: {data}")
                return data
            else:
                print(f"⚠️ fetch_settings HTTP Status: {res.status_code}")
        except Exception as e:
            print(f"⚠️ fetch_settings error: {e}")
        return None

    def get_current_wifi_ssid(self):
        """Get the current connected Wi-Fi SSID."""
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
        """Get all local saved Wi-Fi networks and passwords on the board."""
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
        """Sync Wi-Fi settings from Web to board."""
        if not self.wifi_sync_url:
            return False, "No Sync URL", 0
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
                        print(f"🛑 [Safety Guard]: Active SSID '{current_ssid}' is missing from Web list!")
                        return False, "Active SSID Missing", len(wifi_list)

                return True, "Sync Success", len(wifi_list)
            elif res.status_code == 401:
                return False, "401 Unauthorized", 0
        except Exception as e:
            print(f"⚠️ sync_wifi_from_web error: {e}")
        return False, "Server Error", 0

    def update_wifi_to_web(self):
        """Update: Push all local Wi-Fi profiles from board to Web."""
        if not self.wifi_sync_url:
            return False, 0
        local_wifis = self.get_local_saved_wifis()
        payload = {
            "networks": local_wifis,
            "wifi": local_wifis
        }
        try:
            res = requests.post(self.wifi_sync_url, json=payload, headers=self.headers, timeout=10)
            print(f"📡 Update Wi-Fi Response Status: {res.status_code}, Text: {res.text[:100]}")
            if res.status_code in [200, 201]:
                return True, len(local_wifis)
            elif res.status_code == 401:
                print("🛑 401 Unauthorized: Invalid Secret Token Key")
        except Exception as e:
            print(f"⚠️ update_wifi_to_web error: {e}")
        return False, len(local_wifis)

    def post_to_api(self, image_path, slot_idx, model_idx, kb_idx):
        if not self.vercel_url:
            return {"reply": "Error: VERCEL_URL is not set."}
        payload = {
            "prompt_index": str(slot_idx),
            "ai_index": str(model_idx),
            "model_index": str(model_idx),
            "kb_index": str(kb_idx)
        }
        
        try:
            if not image_path or not os.path.exists(image_path):
                return {"reply": "Error: Image missing."}
            with open(image_path, 'rb') as img:
                files = {'image': ('snap.jpg', img, 'image/jpeg')}
                response = requests.post(self.vercel_url, data=payload, files=files, headers=self.headers, timeout=35)

            try:
                return response.json()
            except Exception:
                return {"reply": response.text}

        except Exception as e:
            return {"reply": f"Connect Error: {e}"}