# twenty2020_bar_plus.py
import time
import platform
import subprocess
import shutil
import tkinter as tk

# ====== Konfigurasi ======
INTERVAL_MIN     = 20          # durasi kerja (menit)
LAST_WARN_SEC    = 3 * 60      # ambang kuning/oranye (detik)
BREAK_SECONDS    = 20          # countdown istirahat (detik)
BAR_WIDTH        = 560
BAR_HEIGHT       = 38
FONT_NAME        = "Segoe UI"

USE_SOUND        = True        # bunyi saat masuk merah
BEEP_AT_START    = True        # bunyi saat break dimulai
BEEP_EACH_SEC    = False       # bunyi tiap detik di mode break
SHAKE_ON_BREAK   = True        # efek "getar" jendela saat break dimulai

MINIMIZE_ON_BREAK = True       # <<< FITUR BARU: minimize semua aplikasi saat mulai break
# =========================

OS = platform.system().lower()

def play_beep_tiny():
    """Beep ringan cross-platform sebisanya."""
    if not USE_SOUND:
        return
    try:
        if "windows" in OS:
            import winsound
            winsound.Beep(880, 180)
            winsound.Beep(660, 120)
        # di *nix kita pakai root.bell() dari instance (dipanggil dalam class)
    except Exception:
        pass

def minimize_all_windows():
    """Minimize semua window di OS, lalu kembalikan kontrol ke app (bar akan dimunculkan lagi di depan)."""
    try:
        if "windows" in OS:
            # Kirim hotkey Win+M (minimize all, bukan toggle).
            import ctypes
            user32 = ctypes.WinDLL("user32", use_last_error=True)

            # constants
            VK_LWIN = 0x5B
            VK_M    = 0x4D
            KEYEVENTF_KEYUP = 0x0002

            # Tekan Win
            ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)
            # Tekan M
            ctypes.windll.user32.keybd_event(VK_M, 0, 0, 0)
            # Lepas M
            ctypes.windll.user32.keybd_event(VK_M, 0, KEYEVENTF_KEYUP, 0)
            # Lepas Win
            ctypes.windll.user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)

        elif "linux" in OS:
            # Prioritas: wmctrl (show desktop), fallback: xdotool Super+d
            if shutil.which("wmctrl"):
                subprocess.run(["wmctrl", "-k", "on"], check=False)
            elif shutil.which("xdotool"):
                subprocess.run(["xdotool", "key", "Super+d"], check=False)
            else:
                # Tidak tersedia; tidak apa-apa—skip
                pass
        else:
            # macOS (opsional): show desktop via AppleScript (Mission Control)
            # subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 103'], check=False)
            pass
    except Exception:
        # swallow error, tidak fatal
        pass


class TwentyBar:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("20-20-20")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.geometry(f"{BAR_WIDTH}x{BAR_HEIGHT}+60+60")

        # State
        self.mode = "WORK"  # WORK | BREAK
        self.work_end_ts = time.time() + INTERVAL_MIN * 60
        self.break_end_ts = None
        self._tick_job = None

        # Warna
        self.color_ok = "#18a558"       # hijau
        self.color_warn = "#f0a500"     # kuning/oranye
        self.color_break = "#e63946"    # merah
        self.color_text = "#ffffff"     # putih

        # Kontainer (bar 1 garis)
        self.frame = tk.Frame(self.root, height=BAR_HEIGHT, width=BAR_WIDTH, bg=self.color_ok)
        self.frame.pack(fill="both", expand=True)

        # Label teks
        self.label = tk.Label(
            self.frame, text="", fg=self.color_text, bg=self.color_ok,
            font=(FONT_NAME, 12, "bold"), padx=12
        )
        self.label.pack(side="left", fill="both", expand=True)

        # Tombol Selesai Istirahat
        self.btn_done = tk.Button(
            self.frame, text="Selesai Istirahat",
            fg=self.color_text, bg="#333333", activebackground="#444444",
            font=(FONT_NAME, 11, "bold"), relief="flat",
            command=self.finish_break
        )
        self.btn_done.pack_forget()

        # Tombol “Tunda 5m” (opsional)
        self.btn_snooze = tk.Button(
            self.frame, text="Tunda 5m",
            fg=self.color_text, bg="#555555", activebackground="#666666",
            font=(FONT_NAME, 10), relief="flat",
            command=self.snooze_5m
        )
        self.btn_snooze.pack(side="right", padx=(0, 8))

        # Tutup → hide
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Drag window (klik & geser)
        self._drag_data = {'x': 0, 'y': 0}
        for w in (self.frame, self.label):
            w.bind("<ButtonPress-1>", self.start_move)
            w.bind("<B1-Motion>", self.on_move)

        # Loop
        self.tick()

    # ---------- UX ----------
    def start_move(self, event):
        self._drag_data['x'] = event.x
        self._drag_data['y'] = event.y

    def on_move(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_data['x'])
        y = self.root.winfo_y() + (event.y - self._drag_data['y'])
        self.root.geometry(f"+{x}+{y}")

    def on_close(self):
        self.root.withdraw()

    def set_bar_color(self, color):
        self.frame.configure(bg=color)
        self.label.configure(bg=color)

    @staticmethod
    def fmt_mmss(secs):
        secs = max(0, int(secs))
        m = secs // 60
        s = secs % 60
        return f"{m:02d}:{s:02d}"

    # ---------- Efek "getar" window ----------
    def shake(self, times=10, pixels=8, delay=20):
        if not SHAKE_ON_BREAK:
            return
        try:
            x0 = self.root.winfo_x()
            y0 = self.root.winfo_y()
            seq = []
            for i in range(times):
                dx = pixels if i % 2 == 0 else -pixels
                seq.append((x0 + dx, y0))
            seq.append((x0, y0))
            def step(i=0):
                if i >= len(seq):
                    return
                self.root.geometry(f"+{seq[i][0]}+{seq[i][1]}")
                self.root.after(delay, step, i+1)
            step()
        except Exception:
            pass

    def show_bar_front(self):
        """Munculkan bar kembali di depan (setelah minimize-all)."""
        try:
            self.root.deiconify()
            # Ulangi beberapa kali untuk mengatasi WM tertentu
            self.root.lift()
            self.root.attributes("-topmost", True)
            # Focus tidak wajib, tetapi membantu di Windows
            try:
                self.root.focus_force()
            except Exception:
                pass
        except Exception:
            pass

    # ---------- Mode ----------
    def go_break(self):
        self.mode = "BREAK"
        self.break_end_ts = time.time() + BREAK_SECONDS
        self.btn_done.pack(side="right", padx=8)
        self.set_bar_color(self.color_break)

        # Minimalkan semua app lain (opsional)
        if MINIMIZE_ON_BREAK:
            minimize_all_windows()
            # Tampilkan bar kembali di depan setelah system minimize-all selesai
            self.root.after(400, self.show_bar_front)
        else:
            self.show_bar_front()

        # bunyi & getar
        if BEEP_AT_START:
            if "windows" in OS:
                play_beep_tiny()
            else:
                try:
                    self.root.bell()
                except Exception:
                    pass
        self.shake()

        self.label.config(text=f"Anda harus istirahat • {self.fmt_mmss(BREAK_SECONDS)}")

    def finish_break(self):
        self.mode = "WORK"
        self.work_end_ts = time.time() + INTERVAL_MIN * 60
        self.break_end_ts = None
        self.btn_done.pack_forget()
        self.set_bar_color(self.color_ok)
        self.label.config(text=f"Kerja: {INTERVAL_MIN:02d}:00")

    def snooze_5m(self):
        if self.mode == "WORK":
            self.work_end_ts = time.time() + 5 * 60
            self.set_bar_color(self.color_warn)
            self.label.config(text=f"Tunda: {self.fmt_mmss(5*60)}")

    # ---------- Loop ----------
    def tick(self):
        if self.mode == "WORK":
            remain = int(self.work_end_ts - time.time())
            if remain <= 0:
                self.go_break()
            else:
                if remain <= LAST_WARN_SEC:
                    self.set_bar_color(self.color_warn)
                else:
                    self.set_bar_color(self.color_ok)
                self.label.config(text=f"Kerja: {self.fmt_mmss(remain)}  •  Aturan 20-20-20")
        else:
            # BREAK: countdown 20 detik; tidak auto lanjut kerja
            if self.break_end_ts is not None:
                remain = int(self.break_end_ts - time.time())
                if remain < 0:
                    remain = 0
                if BEEP_EACH_SEC and remain > 0:
                    try:
                        if "windows" in OS:
                            import winsound
                            winsound.Beep(880, 40)
                        else:
                            self.root.bell()
                    except Exception:
                        pass
                self.set_bar_color(self.color_break)
                if remain == 0:
                    self.label.config(text="Istirahat selesai — klik 'Selesai Istirahat' untuk lanjut")
                else:
                    self.label.config(text=f"Anda harus istirahat • {self.fmt_mmss(remain)}")

        self._tick_job = self.root.after(250, self.tick)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    TwentyBar().run()
