import serial
import serial.tools.list_ports
import time
import matplotlib.pyplot as plt
import numpy as np


def find_tinysa():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "usbmodem" in port.device.lower() or "tinysa" in port.description.lower():
            return port.device
    return None


def get_spectrum(start_hz, stop_hz, points=290):
    port_name = find_tinysa()
    if not port_name: return None

    try:
        ser = serial.Serial(port_name, 115200, timeout=2)
        # Команда сканирования: scan [start] [stop] [points] [binary=0]
        command = f"scan {start_hz} {stop_hz} {points} 0\r\n"
        ser.write(command.encode())

        time.sleep(1)  # Ждем завершения сканирования
        raw_data = ser.read_all().decode('utf-8', errors='ignore')
        ser.close()

        # Парсим строки (tinySA отдает данные построчно: частота уровень)
        amplitudes = []
        for line in raw_data.split('\n'):
            parts = line.strip().split()
            if len(parts) == 2:
                try:
                    amplitudes.append(float(parts[1]))
                except:
                    continue

        return np.array(amplitudes)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None


def plot_spectrum():
    # Давай глянем диапазон FM (88 - 108 МГц) или что тебе интересно
    START = 88_000_000
    STOP = 108_000_000

    print(f"📡 Сканирую диапазон {START / 1e6:.1f} - {STOP / 1e6:.1f} MHz...")
    data = get_spectrum(START, STOP)

    if data is not None and len(data) > 0:
        frequencies = np.linspace(START / 1e6, STOP / 1e6, len(data))

        plt.figure(figsize=(10, 5))
        plt.plot(frequencies, data, color='lime', linewidth=1.5)
        plt.fill_between(frequencies, data, -120, color='lime', alpha=0.2)
        plt.title(f"tinySA Spectrum Analyzer ({START / 1e6}-{STOP / 1e6} MHz)")
        plt.xlabel("Frequency (MHz)")
        plt.ylabel("Level (dBm)")
        plt.grid(True, alpha=0.3)
        plt.ylim([-120, 0])  # Типичный динамический диапазон
        plt.show()
    else:
        print("❌ Не удалось получить данные спектра.")


if __name__ == "__main__":
    plot_spectrum()