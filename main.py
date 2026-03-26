import serial
import serial.tools.list_ports
import time
import matplotlib.pyplot as plt
import numpy as np

# --- НАСТРОЙКИ ---
START_FREQ = 2_000_000
STOP_FREQ = 2_500_000
POINTS = 150
ITERATIONS = 50

# Параметры детектора CISPR
TC = 0.001  # Заряд (1 ms)
TD = 0.160  # Разряд (160 ms)
FS = 10


def apply_quasi_peak_logic(data_dbm):
    data_dbuv = data_dbm + 107
    v_linear = 10 ** (data_dbuv / 20)
    qp_v = np.zeros_like(v_linear)
    current_qp = v_linear[0]
    alpha_c = 1 - np.exp(-1 / (FS * TC))
    alpha_d = 1 - np.exp(-1 / (FS * TD))
    for i in range(len(v_linear)):
        if v_linear[i] > current_qp:
            current_qp += alpha_c * (v_linear[i] - current_qp)
        else:
            current_qp -= alpha_d * current_qp
        qp_v[i] = current_qp
    return 20 * np.log10(qp_v + 1e-12)


def find_tinysa():
    ports = serial.tools.list_ports.comports()
    return next((p.device for p in ports if "usbmodem" in p.device.lower() or "tinysa" in p.description.lower()), None)


def wait_for_device(ser):
    buffer = ""
    start = time.time()
    while "ch>" not in buffer and time.time() - start < 2.0:
        if ser.in_waiting > 0:
            buffer += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    return time.time() - start


def run_final_scan():
    port = find_tinysa()
    if not port: return

    ser = serial.Serial(port, 115200, timeout=0.1)
    ser.write(f"sweep {START_FREQ} {STOP_FREQ} {POINTS}\r\n".encode())
    wait_for_device(ser)

    all_qp_scans = []

    print(f"🚀 Сбор {ITERATIONS} итераций с Quasi-Peak анализом...")

    try:
        for _ in range(ITERATIONS):
            ser.reset_input_buffer()
            ser.write(b"data 0\r\n")

            raw_scan = []
            timeout = time.time() + 1.0
            while len(raw_scan) < POINTS and time.time() < timeout:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                try:
                    val = float(line)
                    if -150 < val < 50: raw_scan.append(val)
                except:
                    continue

            if len(raw_scan) >= POINTS:
                all_qp_scans.append(apply_quasi_peak_logic(np.array(raw_scan[:POINTS])))

            ser.write(b"wait\r\n")
            wait_for_device(ser)
            if (_ + 1) % 10 == 0: print(f"📊 Прогресс: {_ + 1}/{ITERATIONS}")

    finally:
        ser.close()

    final_qp = np.mean(all_qp_scans, axis=0)
    freqs = np.linspace(START_FREQ / 1e6, STOP_FREQ / 1e6, POINTS)

    # --- ВИЗУАЛИЗАЦИЯ ---
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 7))

    # Основная линия
    line, = ax.plot(freqs, final_qp, color='#FFD700', linewidth=2, label='Quasi-Peak (Calculated)')
    ax.fill_between(freqs, final_qp, 0, color='#FFD700', alpha=0.1)

    # --- МАРКЕР МАКСИМУМА ---
    max_idx = np.argmax(final_qp)
    max_f = freqs[max_idx]
    max_v = final_qp[max_idx]

    # Рисуем точку
    ax.scatter(max_f, max_v, color='red', s=50, edgecolors='white', zorder=5)

    # Текстовая аннотация
    ax.annotate(f'MAX: {max_v:.2f} dBµV\n{max_f:.3f} MHz',
                xy=(max_f, max_v),
                xytext=(max_f + 0.01, max_v + 5),
                color='white', fontweight='bold',
                arrowprops=dict(facecolor='white', shrink=0.05, width=1, headwidth=6))

    ax.set_ylim([0, 110])
    ax.set_xlim([freqs[0], freqs[-1]])
    ax.grid(True, alpha=0.2, color='white', linestyle='--')
    ax.set_title(f"EMC PRE-COMPLIANCE: FINAL REPORT", color='white', fontsize=14, pad=20)
    ax.set_ylabel("Amplitude (dBµV)", color='white')
    ax.set_xlabel("Frequency (MHz)", color='white')

    print(f"\n📢 Худшая точка: {max_v:.2f} dBuV на {max_f:.3f} MHz")
    plt.show()


if __name__ == "__main__":
    run_final_scan()