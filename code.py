import digitalio
import board
import time
import adafruit_dht

dht = adafruit_dht.DHT11(board.D5)

while True:
    temp = dht.temperature
    humidity = dht.humidity

    print(f"Temperature: {temp}°C")
    print(f"Humidity: {humidity}%")

    # failed to return a reading
    except RuntimeError as error:
    print(error)

    if humidity < 30:
        print("Needs water")