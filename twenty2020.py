import sys, time, platform
import tkinter as tk
from tkinter import ttk
from threading import Timer

# Notifikasi sistem (opsional, aman jika lib tak ada)
NOTIFY = None
OS = platform.system().lower()
try:
    if 'linux' in OS:
        import notify2
        notify2_inited = False
        NOTIFY = 'linux'
    elif 'windows' in OS:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        NOTIFY = 'windows'
except Exception:
    NOTIFY = None

INTERVAL_MIN = 20   # tiap 20 menit
BREAK_SEC    = 20   # istirahat 20 detik (lihat 20 feet ~ 6 meter)
SNOOZE_MIN   = 5

class TwentyApp:
    def __init__(self, interval_min=20, break_sec=20):
        self.interval = interval_min * 60
        self.break_sec = break_sec
        self.snooze_min = SNOOZE_MIN
        self.root = tk.Tk()
        self.root.title("20-20-20")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.geometry("+50+50")

        # Minimal floating window
        frm = ttk.Frame(self.root, padding=12)
        frm.grid()
        self.label = ttk.Label(frm, text="20-20-20 Reminder", font=("Segoe UI", 12, "bold"))
        self.label.grid(column=0, row=0, columnspan=3, pady=(0,8))

        self.status = ttk.Label(frm, text="Menunggu 20 menit…")
        self.status.grid(column=0, row=1, columnspan=3, pady=(0,8))

        self.btn_start = ttk.Button(frm, text="Mulai Istirahat", command=self.start_break)
        self.btn_start.grid(column=0, row=2, padx=4)
        self.btn_snooze = ttk.Button(frm, text=f"Snooze {self.snooze_min}m", command=self.snooze)
        self.btn_snooze.grid(column=1, row=2, padx=4)
        self.btn_skip = ttk.Button(frm, text="Skip", command=self.schedule_next)
        self.btn_skip.grid(column=2, row=2, padx=4)

        # Countdown label saat break
        self.count_label = ttk.Label(frm, text="")
        self.count_label.grid(column=0, row=3, columnspan=3, pady=(8,0))

        # Mulai timer pertama
        self._timer = None
        self._countdown_job = None
        self.schedule_next()

        # Close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Inisialisasi notifikasi linux jika ada
        if NOTIFY == 'linux':
            global notify2_inited
            if not 'notify2_inited' in globals() or not notify2_inited:
                try:
                    notify2.init("20-20-20")
                    notify2_inited = True
                except:
                    pass

    def notify(self, title, msg):
        try:
            if NOTIFY == 'windows':
                toaster.show_toast(title, msg, duration=3, threaded=True)
            elif NOTIFY == 'linux':
                n = notify2.Notification(title, msg)
                n.set_timeout(2500)
                n.show()
        except:
            pass  # jika lib tak ada, diam saja

    def schedule_next(self, delay=None):
        if self._timer: self._timer.cancel()
        wait = self.interval if delay is None else delay
        self.status.config(text=f"Menunggu {wait//60:.0f} menit…")
        self.count_label.config(text="")
        self.root.attributes("-topmost", True)  # pastikan tetap di depan
        self._timer = Timer(wait, self._show_break_prompt)
        self._timer.daemon = True
        self._timer.start()

    def _show_break_prompt(self):
        # panggil di UI thread
        self.root.after(0, self._prompt_ui)

    def _prompt_ui(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.status.config(text="Saatnya 20-20-20! Lihat objek ±6 meter selama 20 detik.")
        self.notify("20-20-20", "Istirahatkan mata 20 detik, lihat jauh (±6 meter).")
        # auto-mulai break? bisa: self.start_break()

    def start_break(self):
        # Countdown 20 detik
        if self._countdown_job: self.root.after_cancel(self._countdown_job)
        end_ts = time.time() + self.break_sec
        self._tick(end_ts)

    def _tick(self, end_ts):
        remain = int(round(end_ts - time.time()))
        if remain <= 0:
            self.count_label.config(text="Selesai! 👀")
            self.status.config(text="Mantap. Lanjut aktivitas.")
            # jadwalkan interval berikutnya
            self.schedule_next()
            return
        self.count_label.config(text=f"Sisa: {remain} detik")
        self._countdown_job = self.root.after(1000, self._tick, end_ts)

    def snooze(self):
        # Tunda 5 menit
        self.status.config(text=f"Ditunda {self.snooze_min} menit…")
        self.count_label.config(text="")
        self.schedule_next(delay=self.snooze_min * 60)

    def on_close(self):
        # Minimize ke taskbar saja biar tetap jalan
        self.root.withdraw()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    TwentyApp(INTERVAL_MIN, BREAK_SEC).run()
