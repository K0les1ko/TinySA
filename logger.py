import serial
import serial.tools.list_ports
import time

# --- НАСТРОЙКИ СКАНИРОВАНИЯ (Должны совпадать с тем, что ты хочешь видеть) ---
START_FREQ = 2_120_000
STOP_FREQ = 2_140_000
POINTS = 250
RECORD_DURATION = 60  # Секунд записи
FILENAME = "raw_tinysa_calc_qp.txt"


def find_tinysa():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "usbmodem" in p.device.lower() or "tinysa" in p.description.lower():
            return p.device
    return None


def start_raw_logger():
    port = find_tinysa()
    if not port:
        print("❌ tinySA не найден.")
        return

    try:
        ser = serial.Serial(port, 115200, timeout=1)
        ser.reset_input_buffer()

        print(f"📡 Порт: {port}")
        print("⚠️  УБЕДИСЬ, ЧТО НА ЭКРАНЕ ВКЛЮЧЕН 'CALC: QUASI' ВРУЧНУЮ!")

        # Устанавливаем только частоты, это базовые команды
        ser.write(f"sweep {START_FREQ} {STOP_FREQ} {POINTS}\r\n".encode())
        time.sleep(0.5)

        start_time = time.time()
        with open(FILENAME, "w", encoding="utf-8") as f:
            while time.time() - start_time < RECORD_DURATION:
                # Команда 'data 0' всегда отдает то, что на экране.
                # Если на экране включен CALC: QUASI — она отдаст QP.
                ser.write(b"data 0\r\n")

                # Задержка 0.8с, чтобы прибор успевал обсчитать QP-кадр
                time.sleep(0.8)

                if ser.in_waiting:
                    raw_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    f.write(raw_data)

                    elapsed = time.time() - start_time
                    print(f"📥 Пишем данные QP: {elapsed:.1f}/{RECORD_DURATION} сек.", end='\r')

        print(f"\n✅ Запись завершена. Файл: {FILENAME}")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    finally:
        if 'ser' in locals():
            ser.close()


if __name__ == "__main__":
    start_raw_logger()