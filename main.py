import numpy as np
import matplotlib.pyplot as plt
import re

# Параметры должны соответствовать логгеру
START_FREQ = 2_120_000
STOP_FREQ = 2_140_000
EXPECTED_POINTS = 250
INPUT_FILE = "raw_tinysa_calc_qp.txt"


def plot_internal_qp():
    try:
        with open(INPUT_FILE, "r") as f:
            content = f.read()
    except:
        print("❌ Файл не найден")
        return

    # Нарезка пакетов по маркеру начала выдачи
    raw_packets = content.split('data 0')
    all_scans = []
    # Извлекаем числа, включая экспоненты
    num_re = re.compile(r"[-+]?\d*\.\d+e[+-]\d+|[-+]?\d*\.\d+|[-+]?\d+")

    for packet in raw_packets:
        found = num_re.findall(packet)
        if len(found) >= EXPECTED_POINTS:
            all_scans.append(np.array([float(v) for v in found[:EXPECTED_POINTS]]))

    if not all_scans:
        print("❌ Нет данных для построения.")
        return

    scans_matrix = np.array(all_scans)

    # Считаем Max Hold по всем проходам в режиме QP
    # Пересчитываем в dBuV (dBm + 107)
    final_curve = np.max(scans_matrix, axis=0) + 107

    freqs = np.linspace(START_FREQ / 1e6, STOP_FREQ / 1e6, EXPECTED_POINTS)

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(freqs, final_curve, color='#00FF00', linewidth=2, label='Internal tinySA QP (Max Hold)')
    ax.fill_between(freqs, final_curve, 0, color='#00FF00', alpha=0.1)

    peak_idx = np.argmax(final_curve)
    ax.annotate(f"PEAK QP: {final_curve[peak_idx]:.1f} dBuV\n{freqs[peak_idx]:.3f} MHz",
                xy=(freqs[peak_idx], final_curve[peak_idx]), xytext=(15, 15),
                textcoords='offset points', color='white', weight='bold',
                arrowprops=dict(arrowstyle='->', color='yellow'))

    ax.set_ylim([0, 110])
    ax.set_title(f"EMC PRE-COMPLIANCE (INTERNAL QP MODE) | Scans: {len(all_scans)}")
    ax.set_ylabel("Amplitude (dBµV)")
    ax.set_xlabel("Frequency (MHz)")
    ax.grid(True, alpha=0.1)
    ax.legend()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    plot_internal_qp()