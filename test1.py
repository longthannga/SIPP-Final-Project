import time
import board
import digitalio
import analogio
import busio
import gc
from pwmio import PWMOut

# Perform deep garbage collection immediately on boot
gc.collect()

print("==========================================")
print("   EcoPulse System (Memory-Optimized)     ")
print("==========================================")

# ==========================================
# 1. HARDWARE PIN INITIALIZATION
# ==========================================

# Soil Moisture Sensor (Analog Pin A1)
soil_pin = analogio.AnalogIn(board.A1)

# Touch Sensor - TTP223B (Digital Pin D3)
touch_pin = digitalio.DigitalInOut(board.D3)
touch_pin.direction = digitalio.Direction.INPUT

# Buzzer (Digital Pin D6 - Simple digital toggle prevents PWM timer conflicts with Servo)
buzzer = digitalio.DigitalInOut(board.D6)
buzzer.direction = digitalio.Direction.OUTPUT

# Red Alarm LED (Digital Pin D7)
red_led = digitalio.DigitalInOut(board.D7)
red_led.direction = digitalio.Direction.OUTPUT

# SG90 Servo Motor (PWM Pin D5)
servo_pwm = PWMOut(board.D5, frequency=50)

def set_servo_angle(angle):
    """Controls the servo angle using raw PWM duty cycles."""
    min_duty = 1638  # ~0 degrees
    max_duty = 8192  # ~180 degrees
    duty = int(min_duty + (angle / 180.0) * (max_duty - min_duty))
    servo_pwm.duty_cycle = duty

# Reset servo to home position
set_servo_angle(0)

# Safely initialize DHT11 Air Sensor
dht_sensor = None
try:
    import adafruit_dht
    dht_sensor = adafruit_dht.DHT11(board.D2)
    print("[INIT] DHT11 Air Sensor Ready")
except Exception:
    print("[INIT] DHT11 Skipped or Not Connected")

gc.collect()

# Safely initialize OLED Display
oled = None
try:
    import adafruit_ssd1306
    i2c = busio.I2C(board.SCL, board.SDA)
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3c)
    oled.fill(0)
    oled.text("EcoPulse Ready", 0, 0, 1)
    oled.show()
    print("[INIT] OLED Display Ready")
except Exception:
    print("[INIT] OLED Skipped (Serial Output Only)")

gc.collect()

# ==========================================
# 2. SYSTEM STATE VARIABLES
# ==========================================

humidifier_on = False
last_touch = False
last_beep_time = time.monotonic()
buzzer_state = False
display_mode = 0  # 0: Soil Page | 1: Air Page | 2: Screen OFF Mode

print("[SYSTEM] Free Memory:", gc.mem_free(), "bytes")
print("[SYSTEM] Initialization Complete! Running Control Loop...\n")

# ==========================================
# 3. MAIN CONTROL LOOP
# ==========================================

while True:
    # Reclaim unallocated memory at the start of each iteration
    gc.collect()

    # --- Step 1: Touch Pad UI Toggle (0 -> 1 -> 2 -> 0) ---
    current_touch = touch_pin.value
    if current_touch and not last_touch:
        display_mode = (display_mode + 1) % 3
        print("\n[UI] Touch Detected! Display Mode set to:", display_mode)
        time.sleep(0.1)
    last_touch = current_touch

    # --- Step 2: Read Soil Sensor & Control Soil Alarm ---
    raw_val = soil_pin.value
    dryness = (raw_val / 65535.0) * 100.0

    if dryness > 60.0:
        red_led.value = True
        # Toggle buzzer every 0.15s to generate a continuous loud beeping alert
        if time.monotonic() - last_beep_time >= 0.15:
            buzzer_state = not buzzer_state
            buzzer.value = buzzer_state
            last_beep_time = time.monotonic()
        alarm_str = "[ALERT: DRY]"
    else:
        red_led.value = False
        buzzer.value = False
        alarm_str = "[OK: NORMAL]"

    # --- Step 3: Read DHT11 Air Sensor ---
    air_temp = 0
    air_humidity = 0
    if dht_sensor is not None:
        try:
            air_temp = dht_sensor.temperature
            air_humidity = dht_sensor.humidity
        except Exception:
            pass  # Ignore occasional reading glitches gracefully

    # --- Step 4: Automated Humidifier Servo Control ---
    if air_humidity and air_humidity > 0:
        if air_humidity < 40 and not humidifier_on:
            print("\n[AUTO CONTROL] Air Humidity Low (<40%). Actuating Servo: Turning Humidifier ON.")
            set_servo_angle(60)
            time.sleep(0.4)
            set_servo_angle(0)
            humidifier_on = True
        elif air_humidity > 60 and humidifier_on:
            print("\n[AUTO CONTROL] Air Humidity Sufficient (>60%). Actuating Servo: Turning Humidifier OFF.")
            set_servo_angle(60)
            time.sleep(0.4)
            set_servo_angle(0)
            humidifier_on = False

    # --- Step 5: Render OLED Screen (Memory-Efficient String Concatenation) ---
    if oled is not None:
        try:
            oled.fill(0)
            if display_mode == 0:
                # Page 0: Soil Status
                oled.text("== EcoPulse: SOIL ==", 0, 0, 1)
                oled.text("Dryness: " + str(int(dryness)) + "%", 0, 22, 1)
                oled.text("STATUS: " + ("ALERT!" if dryness > 60.0 else "OK"), 0, 45, 1)
            elif display_mode == 1:
                # Page 1: Air & Humidifier Status
                oled.text("== EcoPulse: AIR ==", 0, 0, 1)
                oled.text("Temp: " + str(air_temp) + " C", 0, 18, 1)
                oled.text("Humid: " + str(air_humidity) + "%", 0, 33, 1)
                oled.text("PUMP: " + ("ON" if humidifier_on else "OFF"), 0, 48, 1)
            elif display_mode == 2:
                # Page 2: Screen OFF Mode
                pass
            oled.show()
        except Exception:
            pass  # Suppress graphics buffer errors to ensure system stability

    # --- Step 6: Serial Console Output ---
    h_str = "ON" if humidifier_on else "OFF"
    print(f"Soil Dryness: {dryness:4.1f}% {alarm_str} | Air: {air_temp}C / {air_humidity}% | Humidifier: {h_str}")

    time.sleep(0.15)
