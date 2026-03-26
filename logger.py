import serial
import serial.tools.list_ports
import time

# --- НАСТРОЙКИ СКАНИРОВАНИЯ ---
START_FREQ = 2_120_000
STOP_FREQ = 2_140_000
POINTS = 250
RECORD_DURATION = 30  # Для QP 30 секунд обычно достаточно для накопления статистики

# --- НАСТРОЙКИ ЗАПИСИ ---
FILENAME = "raw_tinysa_qp_dump.txt"


def find_tinysa():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "usbmodem" in p.device.lower() or "tinysa" in p.description.lower():
            return p.device
    return None


def start_raw_logger():
    port = find_tinysa()
    if not port:
        print("❌ tinySA не найден. Проверь кабель.")
        return

    print(f"📡 Порт найден: {port}")
    print(f"⚙️ Режим: Quasi-Peak (QP) | RBW: 9kHz")
    print(f"💾 Запись в файл '{FILENAME}' на {RECORD_DURATION} секунд...")

    try:
        ser = serial.Serial(port, 115200, timeout=1)
        ser.reset_input_buffer()

        # 1. Включаем квазипиковый детектор
        ser.write(b"detector qp\r\n")
        time.sleep(0.2)

        # 2. Устанавливаем RBW 9 кГц (стандарт CISPR для этого диапазона)
        ser.write(b"rbw 9k\r\n")
        time.sleep(0.2)

        # 3. Настраиваем границы свипа
        sweep_cmd = f"sweep {START_FREQ} {STOP_FREQ} {POINTS}\r\n"
        ser.write(sweep_cmd.encode())
        time.sleep(0.5)

        start_time = time.time()
        with open(FILENAME, "w", encoding="utf-8") as f:
            while time.time() - start_time < RECORD_DURATION:
                # Запрашиваем данные
                ser.write(b"data 0\r\n")

                # В режиме QP прибор сканирует медленнее!
                # Увеличиваем паузу до 0.8с, чтобы он успевал обновить экран
                time.sleep(0.8)

                if ser.in_waiting:
                    raw_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    f.write(raw_data)

                    elapsed = time.time() - start_time
                    print(f"📥 Запись QP: {elapsed:.1f}/{RECORD_DURATION} сек.", end='\r')

        # Возвращаем детектор в обычный режим после записи (опционально)
        # ser.write(b"detector auto\r\n")

        print(f"\n✅ Запись завершена. Файл сохранен в {FILENAME}")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()


if __name__ == "__main__":
    start_raw_logger()