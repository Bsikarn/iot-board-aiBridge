# Embedded AI Visual Problem Solver

A personal project for Sikarn Pattarasirimongkol, a Full-stack Developer focusing on Data Engineering and Software Engineering. An embedded hardware application built on Raspberry Pi with an E-Ink display that captures visual problems via camera and solves them using cloud AI services. Web coding: https://github.com/Bsikarn/iot-web-aiBridge

---

## Tech Stack

### Languages
- Python 3

### Hardware & Display
- Raspberry Pi (GPIO Control)
- Waveshare 2.13-inch E-Ink Display (`epd2in13_V4`)
- Raspberry Pi Camera Module (`rpicam-still` / `libcamera-still`)

### Libraries & Tools
- RPi.GPIO (Hardware Button Input)
- Pillow / PIL (Image Processing & UI Rendering)
- Requests (HTTP API Communication)
- NetworkManager / nmcli / wpa_supplicant (Wi-Fi Management)

### Backend & Services
- Vercel API Endpoints (`/api/ask`, `/api/settings`, `/api/wifi-settings`, `/api/status`)

## Active Features

- **Multi-Page Visual Problem Capture** — Captures up to 12 images per problem query using Raspberry Pi camera tools (`rpicam-still` / `libcamera-still`) with automatic rotation and thumbnail preview.
- **AI Solver & Async Task Polling** — Submits captured problem images alongside prompt slots, AI model selections, and knowledge base configurations to cloud API endpoints with asynchronous long-polling status tracking.
- **E-Ink UI Engine & State Machine** — Displays an interactive multi-screen menu system, live processing status progress, and multi-page solution images optimized for 2.13-inch E-Paper screens.
- **Hardware Button Navigation** — Complete navigation and control using physical GPIO push buttons (Up, Down, Enter/Select, Special/Exit).
- **Wi-Fi Synchronization & Hotspot Keep-Alive** — Two-way Wi-Fi credential sync between hardware board and web backend, with a background daemon sending heartbeats to keep mobile hotspots active.
- **Local History & Settings Caching** — Retains recent solution pages in local memory and caches server slot/model label mappings in `settings_cache.json`.

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
| **S** | Pin 33 | Special / Exit / Reset Menu |

## Directory Structure

```text
ordinary/
├── display_epd.py        # E-Ink display driver, layout rendering, and image scaling
├── main.py               # Main application entry point and GPIO button event loop
├── network_mod.py        # API communication, camera capture, Wi-Fi sync & keep-alive
├── ui_engine.py          # State machine UI engine, local cache, and history management
├── architecture_diagram.html # Interactive Archify HTML architecture diagram
└── settings_cache.json   # ⚠️ Auto-generated cache file for settings mappings
```

## Environment Variables

```env
# Cloud API and Authentication Keys
BOARD_SECRET_KEY=bseqaluvtksgifkrphab
VERCEL_API_URL=https://aicalculate-iot.vercel.app/api/ask
```
