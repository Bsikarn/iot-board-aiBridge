# ui_engine.py
import os
import json
import base64
import io
from PIL import Image

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE_PATH = os.path.join(CURRENT_DIR, "settings_cache.json")

class EducationalUIEngine:
    def __init__(self, display_instance, network_instance):
        self.display = display_instance
        self.net = network_instance
        
        # Define screen states of the AI device
        self.AI_MENU = 1               
        self.PREVIEW_PHOTO = 2         
        self.SHOWING_RESULT = 3        
        self.HISTORY_MENU = 4          
        self.SHOWING_HISTORY_RESULT = 5 
        self.WIFI_OPTION_SCREEN = 6    
        self.WIFI_RESULT_SCREEN = 7    

        # Initialize system at AI_MENU state immediately
        self.current_state = self.AI_MENU
        
        self.slot_index = 1         
        self.model_index = 1        
        self.kb_index = 1           
        self.menu_index = 0         
        
        self.slot_mappings = {
            1: "General",
            2: "Math",
            3: "Physics",
            4: "Chemistry",
            5: "Short Ans"
        }
        self.model_mappings = {
            1: "GPT-4o",
            2: "Claude 3.5",
            3: "Gemini 1.5",
            4: "DeepSeek",
            5: "Llama 3"
        }
        
        self.load_local_cache()
        
        self.local_history = []     
        self.current_answer_pages = []  
        self.current_page_idx = 0
        
        self.pending_photo_path = None
        self.history_selected_idx = 0
        self.history_page_idx = 0

        self.wifi_option_idx = 0       
        self.wifi_connected_ssid = "Unknown"
        self.wifi_result_title = ""
        self.wifi_result_status = ""
        self.wifi_result_detail = ""
        self.last_known_wifi_count = 0

    def load_local_cache(self):
        if os.path.exists(CACHE_FILE_PATH):
            try:
                with open(CACHE_FILE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "slots" in data and isinstance(data["slots"], dict):
                        for k, v in data["slots"].items():
                            self.slot_mappings[int(k)] = str(v)
                    if "models" in data and isinstance(data["models"], dict):
                        for k, v in data["models"].items():
                            self.model_mappings[int(k)] = str(v)
            except Exception as e:
                print(f"⚠️ load_local_cache error: {e}")

    def save_local_cache(self):
        try:
            cache_data = {
                "slots": self.slot_mappings,
                "models": self.model_mappings
            }
            with open(CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ save_local_cache error: {e}")

    def refresh_settings(self):
        if self.net:
            settings_data = self.net.fetch_settings()
            if settings_data and isinstance(settings_data, dict):
                slots_raw = settings_data.get("slots", settings_data.get("prompts", []))
                if isinstance(slots_raw, list):
                    for idx_item, slot in enumerate(slots_raw):
                        try:
                            if isinstance(slot, dict):
                                idx = int(slot.get("index", slot.get("id", idx_item + 1)))
                                name = str(slot.get("name", slot.get("title", ""))).strip()
                            else:
                                idx = idx_item + 1
                                name = str(slot).strip()
                            if name:
                                self.slot_mappings[idx] = name
                        except Exception:
                            pass
                elif isinstance(slots_raw, dict):
                    for k, v in slots_raw.items():
                        try:
                            self.slot_mappings[int(k)] = str(v).strip()
                        except Exception:
                            pass
                
                models_raw = settings_data.get("models", settings_data.get("ai", settings_data.get("ais", settings_data.get("ai_models", []))))
                if isinstance(models_raw, list):
                    for idx_item, model in enumerate(models_raw):
                        try:
                            if isinstance(model, dict):
                                idx = int(model.get("index", model.get("id", idx_item + 1)))
                                name = str(model.get("name", model.get("title", model.get("label", "")))).strip()
                            else:
                                idx = idx_item + 1
                                name = str(model).strip()
                            if name:
                                self.model_mappings[idx] = name
                        except Exception:
                            pass
                elif isinstance(models_raw, dict):
                    for k, v in models_raw.items():
                        try:
                            self.model_mappings[int(k)] = str(v).strip()
                        except Exception:
                            pass

                self.save_local_cache()

    def get_slot_display_name(self, slot_idx):
        return self.slot_mappings.get(slot_idx, str(slot_idx))

    def get_model_display_name(self, model_idx):
        return self.model_mappings.get(model_idx, str(model_idx))

    def save_answer_to_history(self, page_images):
        if not page_images:
            return
        new_entry = {
            "id": f"#{len(self.local_history) + 1:02d}",
            "pages": page_images
        }
        self.local_history.insert(0, new_entry)
        for idx, entry in enumerate(self.local_history):
            entry["id"] = f"#{idx + 1:02d}"
        while len(self.local_history) > 3:
            self.local_history.pop()

    def draw_active_screen(self):
        if not self.display:
            return

        if self.current_state == self.AI_MENU:
            slot_name = self.get_slot_display_name(self.slot_index)
            model_name = self.get_model_display_name(self.model_index)
            
            menu_items = [
                f"Slot: {slot_name}",
                f"Model: {model_name}",
                f"KB: {self.kb_index}",
                "History",
                "WiFi Sync",
                "Take Photo"
            ]
            self.display.draw_ai_menu(menu_items, self.menu_index)

        elif self.current_state == self.WIFI_OPTION_SCREEN:
            self.display.draw_wifi_options(
                ssid=self.wifi_connected_ssid,
                selected_option_idx=self.wifi_option_idx
            )

        elif self.current_state == self.WIFI_RESULT_SCREEN:
            self.display.draw_wifi_result(
                title=self.wifi_result_title,
                status=self.wifi_result_status,
                detail=self.wifi_result_detail,
                ssid=self.wifi_connected_ssid
            )

        elif self.current_state == self.PREVIEW_PHOTO:
            self.display.draw_camera_preview(self.pending_photo_path)

        elif self.current_state == self.SHOWING_RESULT:
            if self.current_answer_pages:
                total_p = len(self.current_answer_pages)
                img = self.current_answer_pages[self.current_page_idx]
                self.display.draw_image_page(img, self.current_page_idx + 1, total_p)

        elif self.current_state == self.HISTORY_MENU:
            slots_list = [entry["id"] for entry in self.local_history]
            if not slots_list:
                slots_list = ["(No History) - [E] Back"]
            self.display.draw_history_list(slots_list, self.history_selected_idx)

        elif self.current_state == self.SHOWING_HISTORY_RESULT:
            if self.local_history and self.history_selected_idx < len(self.local_history):
                pages = self.local_history[self.history_selected_idx]["pages"]
                total_p = len(pages)
                img = pages[self.history_page_idx]
                self.display.draw_image_page(img, self.history_page_idx + 1, total_p)

    def handle_input(self, btn):
        btn = btn.lower()

        # 1. Wi-Fi Sync/Update result screen: Press [E] to return to AI Menu
        if self.current_state == self.WIFI_RESULT_SCREEN:
            if btn == 'e':
                self.current_state = self.AI_MENU
                self.draw_active_screen()
            return

        # 2. Wi-Fi Option selection screen (Sync vs Update)
        elif self.current_state == self.WIFI_OPTION_SCREEN:
            if btn == 'u':
                self.wifi_option_idx = (self.wifi_option_idx - 1) % 2
            elif btn == 'd':
                self.wifi_option_idx = (self.wifi_option_idx + 1) % 2
            elif btn == 'e':
                if self.display:
                    self.display.draw_wifi_options(
                        ssid=self.wifi_connected_ssid,
                        selected_option_idx=self.wifi_option_idx,
                        show_check=True
                    )

                if self.net:
                    if self.wifi_option_idx == 0:
                        self.wifi_result_title = "SYNC (WEB -> BOARD)"
                        success, status_msg, new_count = self.net.sync_wifi_from_web()
                        if success:
                            self.wifi_result_status = "Sync Success"
                            diff = new_count - self.last_known_wifi_count
                            if diff > 0:
                                self.wifi_result_detail = f"Added: +{diff} values"
                            elif diff < 0:
                                self.wifi_result_detail = f"Removed: {abs(diff)} values"
                            else:
                                self.wifi_result_detail = "Status: Unchanged"
                            self.last_known_wifi_count = new_count
                            self.refresh_settings()
                        else:
                            self.wifi_result_status = "Sync Blocked"
                            if status_msg == "Active SSID Missing":
                                self.wifi_result_detail = "Active SSID Missing! Update First"
                            elif "401" in status_msg:
                                self.wifi_result_detail = "Auth Error (Bad Key)"
                            else:
                                self.wifi_result_detail = status_msg

                    elif self.wifi_option_idx == 1:
                        self.wifi_result_title = "UPDATE (BOARD -> WEB)"
                        success, count = self.net.update_wifi_to_web()
                        if success:
                            self.wifi_result_status = "Update Success"
                            self.wifi_result_detail = f"Pushed: {count} values"
                            self.refresh_settings()
                        else:
                            self.wifi_result_status = "Update Failed"
                            self.wifi_result_detail = "Server Error"

                    self.wifi_connected_ssid = self.net.get_current_wifi_ssid()
                else:
                    self.wifi_result_title = "WI-FI ACTION"
                    self.wifi_result_status = "Failed"
                    self.wifi_result_detail = "No Network Unit"
                    self.wifi_connected_ssid = "Offline"

                self.current_state = self.WIFI_RESULT_SCREEN
            self.draw_active_screen()
            return

        # 3. Main menu mode (AI_MENU)
        elif self.current_state == self.AI_MENU:
            if btn == 'u':
                self.menu_index = (self.menu_index - 1) % 6
            elif btn == 'd':
                self.menu_index = (self.menu_index + 1) % 6
            elif btn == 'e':
                if self.menu_index == 0:
                    max_slots = max(len(self.slot_mappings), 5)
                    self.slot_index = (self.slot_index % max_slots) + 1
                elif self.menu_index == 1:
                    max_models = max(len(self.model_mappings), 5)
                    self.model_index = (self.model_index % max_models) + 1
                elif self.menu_index == 2:
                    self.kb_index = (self.kb_index % 3) + 1
                elif self.menu_index == 3:
                    self.current_state = self.HISTORY_MENU
                    self.history_selected_idx = 0
                elif self.menu_index == 4:
                    if self.net:
                        self.wifi_connected_ssid = self.net.get_current_wifi_ssid()
                    else:
                        self.wifi_connected_ssid = "Offline"
                    self.wifi_option_idx = 0
                    self.current_state = self.WIFI_OPTION_SCREEN
                elif self.menu_index == 5:
                    if self.net:
                        if self.display:
                            slot_name = self.get_slot_display_name(self.slot_index)
                            model_name = self.get_model_display_name(self.model_index)
                            menu_items = [
                                f"Slot: {slot_name}",
                                f"Model: {model_name}",
                                f"KB: {self.kb_index}",
                                "History",
                                "WiFi Sync",
                                "Take Photo"
                            ]
                            self.display.draw_ai_menu(menu_items, self.menu_index, show_check=True)

                        photo_path = self.net.capture_image()
                        if photo_path and os.path.exists(photo_path):
                            self.pending_photo_path = photo_path
                            self.current_state = self.PREVIEW_PHOTO

            self.draw_active_screen()
            return

        # 4. Photo preview mode (PREVIEW_PHOTO): [E] = Send to AI / [U, D] = Cancel to menu
        elif self.current_state == self.PREVIEW_PHOTO:
            if btn == 'e':
                if self.net and self.pending_photo_path:
                    if self.display:
                        self.display.draw_camera_preview(self.pending_photo_path, show_check=True)

                    res = self.net.post_to_api(
                        self.pending_photo_path,
                        slot_idx=self.slot_index,
                        model_idx=self.model_index,
                        kb_idx=self.kb_index
                    )
                    pages_list = res.get("pages", []) if isinstance(res, dict) else []
                    page_images = []
                    if pages_list:
                        for b64_str in pages_list:
                            try:
                                if "," in b64_str:
                                    b64_str = b64_str.split(",", 1)[1]
                                img_data = base64.b64decode(b64_str)
                                pil_img = Image.open(io.BytesIO(img_data))
                                page_images.append(pil_img)
                            except Exception:
                                pass

                    if page_images:
                        self.current_answer_pages = page_images
                        self.current_page_idx = 0
                        self.save_answer_to_history(page_images)
                        self.current_state = self.SHOWING_RESULT
                        self.refresh_settings()
                    else:
                        self.current_state = self.AI_MENU
                else:
                    self.current_state = self.AI_MENU
            elif btn in ['u', 'd']:
                self.pending_photo_path = None
                self.current_state = self.AI_MENU

            self.draw_active_screen()
            return

        # 5. Solution view mode (SHOWING_RESULT): [U, D] = Change page / [E] = Return to menu
        elif self.current_state == self.SHOWING_RESULT:
            total_pages = len(self.current_answer_pages)
            if btn == 'u':
                if total_pages > 1 and self.current_page_idx > 0:
                    self.current_page_idx -= 1
            elif btn == 'd':
                if total_pages > 1 and self.current_page_idx < total_pages - 1:
                    self.current_page_idx += 1
            elif btn == 'e':
                self.current_state = self.AI_MENU
            self.draw_active_screen()
            return

        # 6. History selection mode (HISTORY_MENU): [U, D] = Navigate / [E] = Open (Return to menu if empty)
        elif self.current_state == self.HISTORY_MENU:
            total_hist = len(self.local_history)
            if total_hist == 0:
                if btn == 'e':
                    self.current_state = self.AI_MENU
            else:
                if btn == 'u':
                    self.history_selected_idx = (self.history_selected_idx - 1) % total_hist
                elif btn == 'd':
                    self.history_selected_idx = (self.history_selected_idx + 1) % total_hist
                elif btn == 'e':
                    self.history_page_idx = 0
                    self.current_state = self.SHOWING_HISTORY_RESULT

            self.draw_active_screen()
            return

        # 7. History solution view mode (SHOWING_HISTORY_RESULT): [U, D] = Change page / [E] = Return to menu
        elif self.current_state == self.SHOWING_HISTORY_RESULT:
            current_entry = self.local_history[self.history_selected_idx]
            total_pages = len(current_entry["pages"])
            if btn == 'u':
                if total_pages > 1 and self.history_page_idx > 0:
                    self.history_page_idx -= 1
            elif btn == 'd':
                if total_pages > 1 and self.history_page_idx < total_pages - 1:
                    self.history_page_idx += 1
            elif btn == 'e':
                self.current_state = self.AI_MENU
            self.draw_active_screen()
            return