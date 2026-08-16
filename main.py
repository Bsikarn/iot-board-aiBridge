# main.py
import time
import RPi.GPIO as GPIO

from display_epd import EducationalDisplay
from network_mod import EducationalNetwork
from ui_engine import EducationalUIEngine

# Define 3 main button pins: U (Up), E (Select/Enter), D (Down)
PIN_U = 29
PIN_E = 31
PIN_D = 32

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

BUTTON_PINS = {
    PIN_U: 'u',
    PIN_E: 'e',
    PIN_D: 'd'
}

for pin in BUTTON_PINS.keys():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def fetch_active_button():
    for pin, btn_code in BUTTON_PINS.items():
        if GPIO.input(pin) == GPIO.LOW:
            return btn_code
    return None

def main():
    print("--------------------------------------------------")
    print("🚀 [System Boot] Starting Embedded AI Visual Problem Solver...")
    print("--------------------------------------------------")

    try:
        display_unit = EducationalDisplay()
        display_unit.clear()
        print("✅ [Hardware Status] E-Ink Display: INITIALIZED")
    except Exception as e:
        print(f"🚨 [Hardware Error] Display Init Failed: {e}")
        display_unit = None

    network_unit = EducationalNetwork(vercel_url="")

    # Enter the main AI menu screen immediately
    if display_unit:
        ui_core = EducationalUIEngine(display_unit, network_unit)
        ui_core.draw_active_screen()
    else:
        ui_core = None

    last_button_state = None

    try:
        while True:
            btn = fetch_active_button()
            if btn and ui_core:
                if btn != last_button_state:
                    last_button_state = btn
                    print(f"🔘 [Button Input]: {btn.upper()}")
                    ui_core.handle_input(btn)
                    time.sleep(0.01)
            else:
                last_button_state = None

            time.sleep(0.002)

    except KeyboardInterrupt:
        print("\n👋 [System Shutdown] Exiting program...")
    finally:
        try:
            GPIO.cleanup()
        except Exception:
            pass

if __name__ == "__main__":
    main()