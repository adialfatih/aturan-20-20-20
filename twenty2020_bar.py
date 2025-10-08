import time
import tkinter as tk

# ====== Konfigurasi ======
INTERVAL_MIN = 20          # durasi kerja (menit)
LAST_WARN_SEC = 3 * 60     # ambang kuning/oranye (detik)
BAR_WIDTH = 520            # lebar bar
BAR_HEIGHT = 38            # tinggi bar
FONT_NAME = "Segoe UI"     # ganti sesuai selera
# =========================

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

        # Warna
        self.color_ok = "#18a558"       # hijau
        self.color_warn = "#f0a500"     # kuning/oranye
        self.color_break = "#e63946"    # merah
        self.color_text = "#ffffff"     # putih

        # Kontainer utama (single line)
        self.frame = tk.Frame(self.root, height=BAR_HEIGHT, width=BAR_WIDTH, bg=self.color_ok)
        self.frame.pack(fill="both", expand=True)

        # Label teks (hitungan mundur / pesan)
        self.label = tk.Label(
            self.frame, text="", fg=self.color_text, bg=self.color_ok,
            font=(FONT_NAME, 12, "bold"), padx=12
        )
        self.label.pack(side="left", fill="both", expand=True)

        # Tombol “Selesai Istirahat” (muncul hanya saat BREAK)
        self.btn_done = tk.Button(
            self.frame, text="Selesai Istirahat",
            fg=self.color_text, bg="#333333", activebackground="#444444",
            font=(FONT_NAME, 11, "bold"), relief="flat",
            command=self.finish_break
        )
        # default: disembunyikan
        self.btn_done.pack_forget()

        # Tutup jendela → hanya hide (biar tetap bisa dibuka jika jalan via console)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Fitur drag bar (klik & geser di area mana pun)
        self._drag_data = {'x': 0, 'y': 0}
        for w in (self.frame, self.label):
            w.bind("<ButtonPress-1>", self.start_move)
            w.bind("<B1-Motion>", self.on_move)

        # Mulai loop UI
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
        # Sembunyikan; untuk keluar total, tutup dari Task Manager/Terminal
        self.root.withdraw()

    # ---------- Logika ----------
    def set_bar_color(self, color):
        self.frame.configure(bg=color)
        self.label.configure(bg=color)

    def format_mmss(self, secs):
        secs = max(0, int(secs))
        m = secs // 60
        s = secs % 60
        return f"{m:02d}:{s:02d}"

    def go_break(self):
        self.mode = "BREAK"
        self.btn_done.pack(side="right", padx=10)
        self.set_bar_color(self.color_break)
        self.label.config(text="Anda harus istirahat. Lihat jauh ±6 meter. ")
        # Tidak ada auto-20 detik—menunggu tombol “Selesai Istirahat”.

    def finish_break(self):
        # Reset ke sesi kerja berikutnya
        self.mode = "WORK"
        self.work_end_ts = time.time() + INTERVAL_MIN * 60
        self.btn_done.pack_forget()
        self.set_bar_color(self.color_ok)
        self.label.config(text=f"Kerja: {INTERVAL_MIN:02d}:00")

    def tick(self):
        if self.mode == "WORK":
            remain = int(self.work_end_ts - time.time())
            if remain <= 0:
                # masuk fase break
                self.go_break()
            else:
                # warna berdasarkan sisa waktu
                if remain <= LAST_WARN_SEC:
                    self.set_bar_color(self.color_warn)
                else:
                    self.set_bar_color(self.color_ok)
                self.label.config(text=f"Kerja: {self.format_mmss(remain)}  •  Aturan 20-20-20")
        else:
            # BREAK → bar merah + pesan + tombol "Selesai Istirahat"
            # tidak ada countdown otomatis
            pass

        # refresh tiap 250ms agar smooth
        self.root.after(250, self.tick)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    TwentyBar().run()
