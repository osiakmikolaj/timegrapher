"""
main_window.py
Glowne okno aplikacji (GUI) - Timegrapher Acoustic Watch Analyzer.
"""

import time
import statistics

import serial.tools.list_ports
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QTabWidget,
                             QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView, QComboBox, QGroupBox,
                             QLineEdit, QDoubleSpinBox)
from PyQt6.QtGui import QFont, QCloseEvent
from PyQt6.QtCore import QTimer
import pyqtgraph as pg

from serial_worker import SerialWorker
from database import TimegrapherDB
from config import DEFAULT_LIFT_ANGLE_DEG

# Progi referencyjne "zdrowego" ruchu (typowe wartosci branzowe)
RATE_GOOD_THRESHOLD = 10.0      # s/d
AMP_GOOD_MIN = 270.0            # stopnie
AMP_GOOD_MAX = 310.0            # stopnie
AMP_OK_MIN = 250.0               # stopnie (jeszcze akceptowalne)


class TimegrapherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timegrapher - Acoustic Watch Analyzer")
        self.resize(1100, 800)

        self.db = TimegrapherDB()

        self.is_measuring = False
        self.worker = None
        self.current_session_id = None
        self.reset_session_data()

        self.init_ui()

    def reset_session_data(self):
        self.time_data = []
        self.rate_data = []
        self.tick_data = []
        self.tock_data = []
        self.session_rates = []
        self.start_time = time.time()

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # --- TAB 1: LIVE DASHBOARD ---
        self.tab_live = QWidget()
        live_layout = QVBoxLayout(self.tab_live)

        # 1. CONTROL PANEL
        ctrl_group = QGroupBox("Control Panel")
        ctrl_layout = QHBoxLayout()

        self.combo_port = QComboBox()
        self.refresh_ports()

        btn_refresh_ports = QPushButton("Refresh Ports")
        btn_refresh_ports.clicked.connect(self.refresh_ports)

        self.combo_bph = QComboBox()
        self.combo_bph.addItems(["14400", "18000", "21600", "25200", "28800", "36000"])
        self.combo_bph.setCurrentText("21600")  # Defaulted for Seagull ST3600

        self.spin_lift_angle = QDoubleSpinBox()
        self.spin_lift_angle.setRange(30.0, 80.0)
        self.spin_lift_angle.setSingleStep(0.5)
        self.spin_lift_angle.setValue(DEFAULT_LIFT_ANGLE_DEG)
        self.spin_lift_angle.setSuffix("°")

        self.edit_watch_name = QLineEdit()
        self.edit_watch_name.setPlaceholderText("np. Seagull ST3600 #1")

        self.btn_toggle_measure = QPushButton("START MEASUREMENT")
        self.btn_toggle_measure.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold; padding: 10px;")
        self.btn_toggle_measure.clicked.connect(self.toggle_measurement)

        ctrl_layout.addWidget(QLabel("Port:"))
        ctrl_layout.addWidget(self.combo_port)
        ctrl_layout.addWidget(btn_refresh_ports)
        ctrl_layout.addWidget(QLabel("Target BPH:"))
        ctrl_layout.addWidget(self.combo_bph)
        ctrl_layout.addWidget(QLabel("Lift Angle:"))
        ctrl_layout.addWidget(self.spin_lift_angle)
        ctrl_layout.addWidget(QLabel("Zegarek:"))
        ctrl_layout.addWidget(self.edit_watch_name)
        ctrl_layout.addWidget(self.btn_toggle_measure)
        ctrl_group.setLayout(ctrl_layout)
        live_layout.addWidget(ctrl_group)

        # 2. MAIN VALUES DISPLAY
        self.val_rate = QLabel("0.0")
        self.val_beat_error = QLabel("0.0")
        self.val_bph = QLabel("0")
        self.val_amp = QLabel("0")

        val_layout = QHBoxLayout()
        val_layout.addWidget(self.create_value_widget("Rate [s/d]", self.val_rate))
        val_layout.addWidget(self.create_value_widget("Beat Error [ms]", self.val_beat_error))
        val_layout.addWidget(self.create_value_widget("Beat Rate [VPH]", self.val_bph))
        val_layout.addWidget(self.create_value_widget("Amplitude [°]", self.val_amp))
        live_layout.addLayout(val_layout)

        # 2b. HEALTH STATUS + SESSION TIMER
        status_row_layout = QHBoxLayout()

        self.lbl_health = QLabel("")
        self.lbl_health.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        status_row_layout.addWidget(self.lbl_health)

        status_row_layout.addStretch()

        self.lbl_timer = QLabel("Czas pomiaru: 00:00")
        self.lbl_timer.setFont(QFont("Arial", 13))
        self.lbl_timer.setStyleSheet("color: #888;")
        status_row_layout.addWidget(self.lbl_timer)

        live_layout.addLayout(status_row_layout)

        self.session_timer = QTimer(self)
        self.session_timer.timeout.connect(self.update_timer_label)

        # 3. STATISTICS PANEL
        stats_group = QGroupBox("Session Statistics")
        stats_layout = QHBoxLayout()
        self.lbl_avg = QLabel("Avg: 0.0 s/d")
        self.lbl_max = QLabel("Max: 0.0 s/d")
        self.lbl_min = QLabel("Min: 0.0 s/d")
        self.lbl_std = QLabel("Std Dev (σ): 0.00")

        for lbl in [self.lbl_avg, self.lbl_max, self.lbl_min, self.lbl_std]:
            lbl.setFont(QFont("Arial", 12))
            stats_layout.addWidget(lbl)

        stats_group.setLayout(stats_layout)
        live_layout.addWidget(stats_group)

        # 4. CHARTS
        charts_layout = QHBoxLayout()

        self.rate_plot = pg.PlotWidget(title="Rate Drift over Time")
        self.rate_plot.setLabel('left', 'Rate', units='s/d')
        self.rate_plot.setLabel('bottom', 'Time', units='s')
        self.rate_plot.showGrid(x=True, y=True)
        self.rate_line = self.rate_plot.plot(pen=pg.mkPen(color='cyan', width=2))
        charts_layout.addWidget(self.rate_plot)

        self.tape_plot = pg.PlotWidget(title="Paper Tape Simulation (Beat Error)")
        self.tape_plot.setLabel('left', 'Deviation', units='ms')
        self.tape_plot.setLabel('bottom', 'Time', units='s')
        self.tape_plot.showGrid(x=True, y=True)

        self.tick_scatter = pg.ScatterPlotItem(pen=pg.mkPen(width=1, color='r'), symbol='o', size=5, brush=pg.mkBrush('r'))
        self.tock_scatter = pg.ScatterPlotItem(pen=pg.mkPen(width=1, color='b'), symbol='o', size=5, brush=pg.mkBrush('b'))
        self.tape_plot.addItem(self.tick_scatter)
        self.tape_plot.addItem(self.tock_scatter)
        charts_layout.addWidget(self.tape_plot)

        live_layout.addLayout(charts_layout)

        self.lbl_status = QLabel("Ready. Select port and BPH, then click Start.")
        self.lbl_status.setStyleSheet("color: gray;")
        live_layout.addWidget(self.lbl_status)

        self.tabs.addTab(self.tab_live, "Live Dashboard")

        # --- TAB 2: DATA HISTORY (SESSION BASED MANAGEMENT) ---
        self.tab_history = QWidget()
        history_layout = QVBoxLayout(self.tab_history)

        self.table_history = QTableWidget(0, 5)
        self.table_history.setHorizontalHeaderLabels(["Session ID", "Date & Time", "Zegarek", "Target BPH", "Data Points Recorded"])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.table_history)

        btn_layout = QHBoxLayout()

        self.btn_refresh = QPushButton("Refresh Sessions")
        self.btn_refresh.clicked.connect(self.load_history)

        self.btn_export = QPushButton("Export Selected to CSV")
        self.btn_export.clicked.connect(self.export_to_csv)

        self.btn_delete = QPushButton("Delete Selected Session")
        self.btn_delete.setStyleSheet("background-color: #E74C3C; color: white; font-weight: bold;")
        self.btn_delete.clicked.connect(self.delete_session)

        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_delete)

        history_layout.addLayout(btn_layout)

        self.tabs.addTab(self.tab_history, "Data History")
        self.load_history()

    def refresh_ports(self):
        self.combo_port.clear()
        ports = serial.tools.list_ports.comports()
        for p in ports:
            self.combo_port.addItem(f"{p.device} ({p.description})", p.device)

    def create_value_widget(self, title: str, val_label: QLabel) -> QWidget:
        layout = QVBoxLayout()
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 14px; color: #888;")
        val_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        val_label.setStyleSheet("color: gray;")
        layout.addWidget(lbl_title)
        layout.addWidget(val_label)
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def toggle_measurement(self):
        if not self.is_measuring:
            port = self.combo_port.currentData()
            if not port:
                self.show_error("Please select a valid COM port.")
                return

            target_bph = int(self.combo_bph.currentText())
            lift_angle = self.spin_lift_angle.value()
            watch_name = self.edit_watch_name.text().strip()

            self.current_session_id = self.db.create_session(target_bph, watch_name, lift_angle)

            self.reset_session_data()
            self.rate_line.setData([], [])
            self.tick_scatter.setData([], [])
            self.tock_scatter.setData([], [])
            self.lbl_health.setText("")

            self.worker = SerialWorker(port, target_bph, lift_angle)
            self.worker.new_data.connect(self.update_display)
            self.worker.error_signal.connect(self.show_error)
            self.worker.status_signal.connect(lambda s: self.lbl_status.setText(s))
            self.worker.start()

            self.session_timer.start(1000)

            self.is_measuring = True
            self.btn_toggle_measure.setText("STOP MEASUREMENT")
            self.btn_toggle_measure.setStyleSheet("background-color: #E74C3C; color: white; font-weight: bold; padding: 10px;")
            self.combo_port.setEnabled(False)
            self.combo_bph.setEnabled(False)
            self.spin_lift_angle.setEnabled(False)
            self.edit_watch_name.setEnabled(False)
        else:
            if self.worker:
                self.worker.stop()
            self.session_timer.stop()
            self.is_measuring = False
            self.btn_toggle_measure.setText("START MEASUREMENT")
            self.btn_toggle_measure.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold; padding: 10px;")
            self.lbl_status.setText("Measurement stopped.")
            self.val_rate.setStyleSheet("color: gray;")
            self.val_amp.setStyleSheet("color: gray;")
            self.lbl_timer.setText("Czas pomiaru: 00:00")
            self.combo_port.setEnabled(True)
            self.combo_bph.setEnabled(True)
            self.spin_lift_angle.setEnabled(True)
            self.edit_watch_name.setEnabled(True)
            self.load_history()

    def update_display(self, rate: float, beat_error: float, bph: int, amplitude: float, a1_ms: float, a2_ms: float):
        # 1. Update text fields
        self.val_rate.setText(f"{rate:+5.1f}")
        self.val_beat_error.setText(f"{beat_error:4.1f}")
        self.val_bph.setText(f"{bph}")
        self.val_amp.setText(f"{amplitude:.0f}" if amplitude > 0 else "---")

        # Color alerting thresholds
        color_rate = "#2ECC71" if abs(rate) < 15 else "#E74C3C"
        self.val_rate.setStyleSheet(f"color: {color_rate};")
        color_amp = "#2ECC71" if 270 <= amplitude <= 310 else "#E74C3C" if amplitude > 0 else "gray"
        self.val_amp.setStyleSheet(f"color: {color_amp};")

        self.update_health_status(rate, amplitude)

        current_time = time.time() - self.start_time
        target_bph = int(self.combo_bph.currentText())
        t_ideal_ms = (3600.0 / target_bph) * 1000.0

        # 2. Update real-time statistics
        self.session_rates.append(rate)
        avg_rate = statistics.mean(self.session_rates)
        max_rate = max(self.session_rates)
        min_rate = min(self.session_rates)
        std_rate = statistics.stdev(self.session_rates) if len(self.session_rates) > 1 else 0.0

        self.lbl_avg.setText(f"Avg: {avg_rate:+.1f} s/d")
        self.lbl_max.setText(f"Max: {max_rate:+.1f} s/d")
        self.lbl_min.setText(f"Min: {min_rate:+.1f} s/d")
        self.lbl_std.setText(f"Std Dev (σ): {std_rate:.2f}")

        # 3. Stream data into the Plots (supports up to 10000 data points history)
        self.time_data.append(current_time)
        self.rate_data.append(rate)

        self.tick_data.append({'pos': (current_time, a1_ms - t_ideal_ms)})
        self.tock_data.append({'pos': (current_time, a2_ms - t_ideal_ms)})

        if len(self.time_data) > 10000:
            self.time_data.pop(0)
            self.rate_data.pop(0)
            self.tick_data.pop(0)
            self.tock_data.pop(0)

        self.rate_line.setData(self.time_data, self.rate_data)
        self.tick_scatter.setData(self.tick_data)
        self.tock_scatter.setData(self.tock_data)

        # 4. Save metrics into database connected via Session Key
        self.db.save_measurement(self.current_session_id, rate, beat_error, bph, amplitude)

    def update_health_status(self, rate: float, amplitude: float):
        """Ocena kondycji ruchu na podstawie typowych progow branzowych."""
        if amplitude <= 0:
            self.lbl_health.setText("")
            return

        rate_ok = abs(rate) <= RATE_GOOD_THRESHOLD
        amp_good = AMP_GOOD_MIN <= amplitude <= AMP_GOOD_MAX
        amp_ok = AMP_OK_MIN <= amplitude < AMP_GOOD_MIN or AMP_GOOD_MAX < amplitude

        if rate_ok and amp_good:
            self.lbl_health.setText("✅ Zdrowy ruch")
            self.lbl_health.setStyleSheet("color: #2ECC71;")
        elif amp_ok or abs(rate) <= 20:
            self.lbl_health.setText("⚠️ Do sprawdzenia")
            self.lbl_health.setStyleSheet("color: #F39C12;")
        else:
            self.lbl_health.setText("❌ Wymaga serwisu")
            self.lbl_health.setStyleSheet("color: #E74C3C;")

    def update_timer_label(self):
        """Aktualizuje etykiete czasu trwania pomiaru co sekunde (podpiete pod QTimer)."""
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60

        if elapsed < 30:
            hint = f"  (poczekaj jeszcze {30 - elapsed}s na ustabilizowanie odczytu)"
        else:
            hint = ""

        self.lbl_timer.setText(f"Czas pomiaru: {minutes:02d}:{seconds:02d}{hint}")

    def load_history(self):
        rows = self.db.get_sessions_summary()

        self.table_history.setRowCount(0)
        for row_idx, row_data in enumerate(rows):
            self.table_history.insertRow(row_idx)
            for col_idx, col_data in enumerate(row_data):
                val = str(col_data) if col_data is not None else "0"
                item = QTableWidgetItem(val)
                self.table_history.setItem(row_idx, col_idx, item)

    def export_to_csv(self):
        selected_row = self.table_history.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a session from the table first.")
            return

        session_id = self.table_history.item(selected_row, 0).text()

        path, _ = QFileDialog.getSaveFileName(self, "Save Session", f"session_{session_id}_export.csv", "CSV Files (*.csv)")
        if path:
            try:
                self.db.export_session_to_csv(session_id, path)
                QMessageBox.information(self, "Success", f"Session {session_id} exported successfully to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def delete_session(self):
        """Safely removes a targeted session and cascades down to remove all its dependent measurements"""
        selected_row = self.table_history.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a session from the table first.")
            return

        session_id = self.table_history.item(selected_row, 0).text()

        reply = QMessageBox.question(self, "Confirm Deletion",
                                     f"Are you sure you want to delete Session {session_id} and all its measurements?\nThis action cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_session(session_id)
                self.load_history()
                QMessageBox.information(self, "Success", f"Session {session_id} deleted successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete session:\n{e}")

    def show_error(self, message: str):
        self.lbl_status.setText(message)
        self.lbl_status.setStyleSheet("color: red;")

    def closeEvent(self, event: QCloseEvent):
        if self.worker:
            self.worker.stop()
        self.db.close()
        event.accept()
