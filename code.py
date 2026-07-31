import board, gc
from time import sleep, monotonic
gc.collect()

oled = None
try:
    import mini_oled
    disp = mini_oled.MiniOLED(board.SCL, board.SDA)
    disp.fill(0)
    disp.text("READY", 0, 0)
    disp.show()
    oled = disp
    print("[INIT] OLED Display Ready")
except Exception as e:
    oled = None
    print("[INIT] OLED Skipped -", type(e).__name__, "-", e)

gc.collect()
print("[DEBUG] Free mem after OLED init:", gc.mem_free())

import digitalio, analogio
from pwmio import PWMOut

print("EcoPulse System")

soil_pin = analogio.AnalogIn(board.A1)
touch_pin = digitalio.DigitalInOut(board.D3)
touch_pin.direction = digitalio.Direction.INPUT
buzzer = digitalio.DigitalInOut(board.D6)
buzzer.direction = digitalio.Direction.OUTPUT
red_led = digitalio.DigitalInOut(board.D7)
red_led.direction = digitalio.Direction.OUTPUT
servo_pwm = PWMOut(board.D5, frequency=50)

def set_servo_angle(angle):
    duty = int(1638 + (angle / 180.0) * (8192 - 1638))
    servo_pwm.duty_cycle = duty

set_servo_angle(0)

gc.collect()
print("[DEBUG] Free mem after servo/pins init:", gc.mem_free())

dht_sensor = None
try:
    import adafruit_dht
    dht_sensor = adafruit_dht.DHT11(board.D2)
    print("[INIT] DHT11 Air Sensor Ready")
except Exception as e:
    print("[INIT] DHT11 Skipped or Not Connected:", e)

gc.collect()
print("[DEBUG] Free mem after DHT11 init:", gc.mem_free())

humidifier_on = False
last_touch = False
last_beep_time = monotonic()
buzzer_state = False
display_mode = 0

print("[SYSTEM] Free Memory:", gc.mem_free(), "bytes")

while True:
    gc.collect()

    current_touch = touch_pin.value
    if current_touch and not last_touch:
        display_mode = (display_mode + 1) % 3
        print("\n[UI] Mode:", display_mode)
        sleep(0.1)
    last_touch = current_touch

    raw_val = soil_pin.value
    dryness = (raw_val / 65535.0) * 100.0

    if dryness > 60.0:
        red_led.value = True
        if monotonic() - last_beep_time >= 0.15:
            buzzer_state = not buzzer_state
            buzzer.value = buzzer_state
            last_beep_time = monotonic()
        alarm_str = "[ALERT: DRY]"
    else:
        red_led.value = False
        buzzer.value = False
        alarm_str = "[OK: NORMAL]"

    air_temp = 0
    air_humidity = 0
    if dht_sensor is not None:
        gc.collect()
        try:
            air_temp = dht_sensor.temperature
            air_humidity = dht_sensor.humidity
        except Exception:
            pass

    if air_humidity and air_humidity > 0:
        if air_humidity < 40 and not humidifier_on:
            print("\n[AUTO] Humidity low. Pump ON.")
            set_servo_angle(60); sleep(0.4); set_servo_angle(0)
            humidifier_on = True
        elif air_humidity > 60 and humidifier_on:
            print("\n[AUTO] Humidity ok. Pump OFF.")
            set_servo_angle(60); sleep(0.4); set_servo_angle(0)
            humidifier_on = False

    if oled is not None:
        gc.collect()
        try:
            oled.fill(0)
            if display_mode == 0:
                oled.text("SOIL", 0, 0)
                oled.text("DRY:" + str(int(dryness)) + "%", 0, 22)
                oled.text("ALERT" if dryness > 60.0 else "OK", 0, 45)
            elif display_mode == 1:
                oled.text("AIR", 0, 0)
                oled.text("T:" + str(air_temp) + "C H:" + str(air_humidity) + "%", 0, 22)
                oled.text("PUMP:" + ("ON" if humidifier_on else "OFF"), 0, 45)
            oled.show()
        except Exception:
            pass

    h_str = "ON" if humidifier_on else "OFF"
    print("Soil Dryness: " + "{:4.1f}".format(dryness) + "% " + alarm_str +
          " | Air: " + str(air_temp) + "C / " + str(air_humidity) +
          "% | Humidifier: " + h_str)

    gc.collect()
    sleep(0.15)