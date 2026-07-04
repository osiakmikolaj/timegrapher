"""
serial_worker.py
Watek odpowiedzialny za komunikacje z Raspberry Pi Pico przez port szeregowy
oraz obliczenia rate, beat error, BPH i amplitude na podstawie timestampow.
"""

import time
import math
import serial

from PyQt6.QtCore import QThread, pyqtSignal

from config import BAUD_RATE, DEFAULT_LIFT_ANGLE_DEG
from utils import delta_us


class SerialWorker(QThread):
    new_data = pyqtSignal(float, float, int, float, float, float)
    error_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)

    def __init__(self, port, target_bph, lift_angle_deg=DEFAULT_LIFT_ANGLE_DEG):
        super().__init__()
        self.running = True
        self.port = port
        self.target_bph = target_bph
        self.lift_angle_deg = lift_angle_deg

    def run(self):
        if not self.port:
            self.error_signal.emit("Error: No port selected.")
            return

        try:
            ser = serial.Serial(self.port, BAUD_RATE, timeout=1)
            self.status_signal.emit(f"Connected to {self.port}. Listening...")
        except Exception as e:
            self.error_signal.emit(f"Port Error: {e}")
            return

        current_group = []
        ticks = []
        t_ideal_ms = (3600.0 / self.target_bph) * 1000.0

        # Anti-echo / Blanking state memory
        last_group_start = 0

        while self.running:
            try:
                # 1. Push group after timeout (silence)
                if ser.in_waiting == 0 and len(current_group) > 0:
                    now = time.time() * 1000000
                    if (now - current_group[-1][1]) > 50000:
                        self.process_tick_group(current_group, ticks, t_ideal_ms)
                        last_group_start = current_group[0][0]
                        current_group = []
                        continue

                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.isdigit():
                    ts_pico = int(line)
                    ts_pc = time.time() * 1000000

                    if not current_group:
                        # BLANKING PERIOD: If impulse comes within 80ms of the last tick start, it's an echo!
                        if last_group_start != 0 and delta_us(last_group_start, ts_pico) < 80000:
                            continue
                        current_group.append((ts_pico, ts_pc))
                    else:
                        # Max burst duration for a single tick (25ms)
                        if delta_us(current_group[0][0], ts_pico) < 25000:
                            current_group.append((ts_pico, ts_pc))
                        else:
                            # Group finished, process it
                            self.process_tick_group(current_group, ticks, t_ideal_ms)
                            last_group_start = current_group[0][0]

                            # Check if the current trailing pulse belongs to the echo window
                            if delta_us(last_group_start, ts_pico) < 80000:
                                current_group = []
                            else:
                                current_group = [(ts_pico, ts_pc)]
            except Exception:
                pass
        ser.close()

    def process_tick_group(self, group, ticks, t_ideal_ms):
        # UWAGA METODOLOGICZNA: t_lift_us mierzymy jako calkowita rozpietosc
        # czasowa calej wykrytej grupy impulsow (od pierwszego do ostatniego
        # echa/odbicia zarejestrowanego w oknie 25ms), a nie jako bezposredni
        # czas przejscia widelek kotwicy przez kamien impulsowy. To swiadome
        # przyblizenie - przy tak prostym torze analogowym (piezo + komparator)
        # nie da sie latwo wydzielic samego "czystego" impulsu bez wplywu
        # dzwoniacych odbic mechanicznych.
        t_start = group[0][0]
        t_lift_us = delta_us(group[0][0], group[-1][0]) if len(group) > 1 else 0
        ticks.append((t_start, t_lift_us))

        if len(ticks) >= 3:
            t1, lift1 = ticks[0]
            t2, lift2 = ticks[1]
            t3, lift3 = ticks[2]

            A1_ms = delta_us(t1, t2) / 1000.0
            A2_ms = delta_us(t2, t3) / 1000.0

            beat_error = abs(A1_ms - A2_ms)
            full_period_ms = A1_ms + A2_ms
            bph = round((3600000.0 / full_period_ms) * 2) if full_period_ms > 0 else 0

            t_avg_ms = full_period_ms / 2.0
            rate_sd = ((t_avg_ms - t_ideal_ms) / t_ideal_ms) * 86400.0 if t_ideal_ms > 0 else 0.0

            # OUTLIER REJECTION: odrzucamy tylko ewidentnie bledne wartosci
            # (np. pojedynczy falszywy impuls, ktory przeszedl przez filtr echa),
            # nie kazde drobne odchylenie - stad dosc luzne progi.
            if abs(rate_sd) > 999.0 or beat_error > 500.0:
                ticks.pop(0)
                return

            amplitude = 0.0
            if bph > 0 and lift1 > 0:
                omega = (2.0 * math.pi * bph) / 7200.0
                t_lift_s = lift1 / 1000000.0
                if t_lift_s > 0.002:
                    val = (omega * t_lift_s) / 2.0
                    if 0 < val < math.pi:
                        amp_rad = math.radians(self.lift_angle_deg / 2.0) / math.sin(val)
                        amplitude = math.degrees(amp_rad)
                        if not (100 <= amplitude <= 360):
                            amplitude = 0.0

            self.new_data.emit(rate_sd, beat_error, bph, amplitude, A1_ms, A2_ms)
            ticks.pop(0)

    def stop(self):
        self.running = False
        self.wait()
