# display_epd.py
import time
import os
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd2in13_V4

class EducationalDisplay:
    def __init__(self):
        self.epd = epd2in13_V4.EPD()
        self.epd.init()
        self.epd.Clear(0xFF)
        time.sleep(0.3)

        self.width = 250
        self.height = 122
        
        font_thai_paths = [
            "/usr/share/fonts/truetype/tlwg/Garuda.ttf",
            "/usr/share/fonts/truetype/tlwg/Waree.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
        
        loaded_font = None
        for path in font_thai_paths:
            if os.path.exists(path):
                loaded_font = path
                break

        if loaded_font:
            self.font_large = ImageFont.truetype(loaded_font, 22)
            self.font_medium = ImageFont.truetype(loaded_font, 15)
            self.font_small = ImageFont.truetype(loaded_font, 12)
        else:
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    def clear(self):
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        self.render_and_display(image, partial=False)

    def _process_transparent_image(self, img):
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            try:
                alpha = img.split()[-1]
                bg.paste(img, mask=alpha)
            except Exception:
                bg.paste(img)
            return bg
        return img.convert('RGB')

    def render_and_display(self, image, partial=True):
        image = self._process_transparent_image(image)

        if image.size == (250, 122):
            image = image.rotate(270, expand=True, fillcolor=(255, 255, 255))

        if image.size != (122, 250):
            image = image.resize((122, 250))

        image_1bit = image.convert('1')
        buffer = self.epd.getbuffer(image_1bit)

        if partial:
            if hasattr(self.epd, 'displayPartial'):
                self.epd.displayPartial(buffer)
            elif hasattr(self.epd, 'display_partial'):
                self.epd.display_partial(buffer)
            else:
                self.epd.display(buffer)
        else:
            self.epd.display(buffer)

    def _draw_check_overlay(self, draw):
        """Draw a checkmark overlay [✓] on the top-right corner upon confirmation."""
        draw.rectangle([224, 2, 248, 22], fill=(255, 255, 255), outline=0, width=2)
        draw.line([(228, 12), (234, 18)], fill=0, width=3)
        draw.line([(234, 18), (244, 6)], fill=0, width=3)

    def draw_ai_menu(self, menu_items, selected_idx, show_check=False):
        """Render the main AI system menu."""
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        for idx, item in enumerate(menu_items):
            prefix = "> " if idx == selected_idx else "  "
            line_text = f"{prefix}{item}"
            if idx == 0:
                col_x = 5; row_y = 6
            elif idx == 1:
                col_x = 5; row_y = 32
            elif idx == 2:
                col_x = 5; row_y = 60
            elif idx == 3:
                col_x = 125; row_y = 60
            elif idx == 4:
                col_x = 5; row_y = 86
            elif idx == 5:
                col_x = 125; row_y = 86
            draw.text((col_x, row_y), line_text, font=self.font_medium, fill=0)
        if show_check:
            self._draw_check_overlay(draw)
        self.render_and_display(image)

    def draw_wifi_options(self, ssid, selected_option_idx, show_check=False):
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.text((10, 12), f"Connected: {ssid}", font=self.font_medium, fill=0)
        options = ["Sync (Web -> Board)", "Update (Board -> Web)"]
        y = 45
        for idx, opt in enumerate(options):
            prefix = "> " if idx == selected_option_idx else "  "
            draw.text((15, y), f"{prefix}{opt}", font=self.font_medium, fill=0)
            y += 28
        if show_check:
            self._draw_check_overlay(draw)
        self.render_and_display(image)

    def draw_wifi_result(self, title, status, detail, ssid):
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.text((10, 12), f"=== {title} ===", font=self.font_medium, fill=0)
        draw.text((10, 38), f"Status: {status}", font=self.font_medium, fill=0)
        draw.text((10, 62), f"Data: {detail}", font=self.font_medium, fill=0)
        draw.text((10, 86), f"Connected: {ssid}", font=self.font_medium, fill=0)
        self.render_and_display(image)

    def draw_camera_preview(self, img_path, show_check=False):
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        if img_path and os.path.exists(img_path):
            try:
                raw_img = Image.open(img_path)
                thumb = raw_img.resize((100, 100)).convert('RGB')
                image.paste(thumb, (10, 11))
                draw.rectangle([9, 10, 111, 112], outline=0)
            except Exception:
                draw.text((15, 50), "Image Loaded", font=self.font_medium, fill=0)
        if show_check:
            self._draw_check_overlay(draw)
        self.render_and_display(image)

    def draw_image_page(self, page_img_or_path, page_num=1, total_pages=1):
        if isinstance(page_img_or_path, str):
            if os.path.exists(page_img_or_path):
                image = Image.open(page_img_or_path)
            else:
                image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        else:
            image = page_img_or_path
        image = self._process_transparent_image(image)
        if image.size != (250, 122):
            image = image.resize((250, 122))
        self.render_and_display(image)

    def draw_history_list(self, history_slots, selected_idx):
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        y = 15
        for idx, slot_name in enumerate(history_slots):
            prefix = "> " if idx == selected_idx else "  "
            line_text = f"{prefix}{slot_name}"
            draw.text((20, y), line_text, font=self.font_medium, fill=0)
            y += 30
        self.render_and_display(image)