# 🧠 Embedded AI Hardware for Visual Problem Solving

A personal project for Sikarn Pattarasirimongkol, a Full-stack Developer focusing on Data Engineering and Software Engineering. An embedded hardware application built on Raspberry Pi with an E-Ink display that captures visual problems via camera and solves them using cloud AI services. Web coding: https://github.com/Bsikarn/iot-web-aiBridge

---

## Tech Stack

### Languages
- Python 3

### Hardware & Display
- Raspberry Pi (GPIO Control)
- Waveshare 2.13-inch E-Ink Display (epd2in13_V4)
- Raspberry Pi Camera Module (`rpicam-still` / `libcamera-still`)

### Libraries & Tools
- RPi.GPIO (Hardware Button Input)
- Pillow / PIL (Image Processing & UI Rendering)
- Requests (HTTP API Communication)
- NetworkManager / nmcli / wpa_supplicant (Wi-Fi Management)

### Cloud & Backend Integration
- Vercel API Endpoints (`/api/ask`, `/api/settings`, `/api/wifi-settings`)

## ⚡ Active Features

- **Visual Problem Capturing** — Captures images of handwritten or printed problem statements using Raspberry Pi camera tools.
- **AI Solver Integration** — Sends captured images along with prompt slots, AI model selections, and knowledge base configurations to cloud API endpoints.
- **E-Ink UI Engine** — Displays an interactive multi-screen menu system and multi-page solution images optimized for 2.13-inch E-Paper screens.
- **Hardware Button Navigation** — Complete navigation and confirmation control using physical push buttons (Up, Down, Select).
- **Wi-Fi Synchronization** — Two-way Wi-Fi credential sync and update between the hardware board and web backend.
- **Local History & Caching** — Stores recent solution pages in memory and caches server setting mappings locally in `settings_cache.json`.

## Hardware Pinout

### E-Ink Display Connection
| Display Pin | Raspberry Pi BOARD Pin | Description |
| :--- | :--- | :--- |
| **VCC** | Pin 17 | 3.3V Power |
| **GND** | Pin 25 | Ground |
| **DIN** | Pin 19 | SPI MOSI |
| **CLK** | Pin 23 | SPI Clock |
| **CS** | Pin 24 | SPI Chip Select |
| **DC** | Pin 22 | Data/Command Control |
| **RES** | Pin 11 | Reset |
| **BUSY** | Pin 18 | Busy Status |

### Push Button Connection
| Button / Line | Raspberry Pi BOARD Pin | Description / Function |
| :--- | :--- | :--- |
| **GND** | Pin 14 | Shared Ground |
| **U** | Pin 29 | Up Navigation |
| **E** | Pin 31 | Enter / Select |
| **D** | Pin 32 | Down Navigation |

## Directory Structure

```text
ordinary/
├── display_epd.py        # E-Ink display rendering driver and layout builder
├── main.py               # Main application entry point and GPIO button event loop
├── network_mod.py        # Network requests, camera capture, and Wi-Fi manager
├── ui_engine.py          # State machine UI engine and local cache management
└── settings_cache.json   # ⚠️ Auto-generated cache file for settings mappings
```

## 🔐 Environment Variables

```env
# Hardcoded in network_mod.py (or configured via environment)
BOARD_SECRET_KEY=
VERCEL_API_URL=
```
