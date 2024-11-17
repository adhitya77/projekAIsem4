import tkinter as tk
from tkinter import ttk, messagebox
import json
import datetime
import os
import math
import threading
import time
from pynput import mouse, keyboard

class StepCounter:
    def __init__(self):
        self.movement_threshold = 20  # Threshold untuk mendeteksi gerakan
        self.step_threshold = 5  # Jumlah gerakan untuk dihitung sebagai 1 langkah
        self.movement_count = 0
        self.total_steps = 0
        self.last_movement = None
        self.is_running = True
        
    def calculate_movement(self, x, y):
        if self.last_movement is None:
            self.last_movement = (x, y)
            return 0
            
        distance = math.sqrt(
            (x - self.last_movement[0])**2 + 
            (y - self.last_movement[1])**2
        )
        self.last_movement = (x, y)
        return distance
        
    def on_move(self, x, y):
        if not self.is_running:
            return
            
        movement = self.calculate_movement(x, y)
        if movement > self.movement_threshold:
            self.movement_count += 1
            if self.movement_count >= self.step_threshold:
                self.total_steps += 1
                self.movement_count = 0
                
    def on_press(self, key):
        if not self.is_running:
            return
            
        self.movement_count += 1
        if self.movement_count >= self.step_threshold:
            self.total_steps += 1
            self.movement_count = 0
            
    def stop(self):
        self.is_running = False

class ActivityTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pelacak Langkah Otomatis")
        self.root.geometry("800x600")
        
        # Inisialisasi step counter
        self.step_counter = StepCounter()
        self.start_tracking()
        
        # Inisialisasi data
        self.data_file = "aktivitas_data.json"
        self.data = self.load_data()
        
        self.setup_gui()
        self.update_thread = threading.Thread(target=self.update_display, daemon=True)
        self.update_thread.start()
        
    def setup_gui(self):
        # Frame utama
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame status
        status_frame = ttk.LabelFrame(main_frame, text="Status Pelacakan", padding="10")
        status_frame.pack(fill=tk.X, pady=10)
        
        # Label untuk menampilkan langkah
        self.steps_label = ttk.Label(
            status_frame, 
            text="Langkah: 0", 
            font=('Helvetica', 24)
        )
        self.steps_label.pack(pady=10)
        
        # Label untuk informasi jarak dan kalori
        self.info_label = ttk.Label(
            status_frame,
            text="Jarak: 0 km | Kalori: 0 kal",
            font=('Helvetica', 12)
        )
        self.info_label.pack(pady=5)
        
        # Frame aktivitas
        activity_frame = ttk.LabelFrame(main_frame, text="Catat Aktivitas Tambahan", padding="10")
        activity_frame.pack(fill=tk.X, pady=10)
        
        # Input aktivitas
        ttk.Label(activity_frame, text="Nama Aktivitas:").grid(row=0, column=0, padx=5, pady=5)
        self.aktivitas_entry = ttk.Entry(activity_frame)
        self.aktivitas_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(activity_frame, text="Durasi (menit):").grid(row=1, column=0, padx=5, pady=5)
        self.durasi_entry = ttk.Entry(activity_frame)
        self.durasi_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(
            activity_frame, 
            text="Catat Aktivitas",
            command=self.catat_aktivitas
        ).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Frame ringkasan
        summary_frame = ttk.LabelFrame(main_frame, text="Ringkasan Hari Ini", padding="10")
        summary_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.summary_text = tk.Text(summary_frame, height=10)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # Tombol kontrol
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            control_frame,
            text="Simpan Data",
            command=self.save_current_steps
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="Reset Langkah",
            command=self.reset_steps
        ).pack(side=tk.LEFT, padx=5)
        
    def start_tracking(self):
        # Mulai pelacakan mouse
        self.mouse_listener = mouse.Listener(
            on_move=self.step_counter.on_move
        )
        self.mouse_listener.start()
        
        # Mulai pelacakan keyboard
        self.keyboard_listener = keyboard.Listener(
            on_press=self.step_counter.on_press
        )
        self.keyboard_listener.start()
        
    def update_display(self):
        while True:
            if hasattr(self, 'steps_label'):
                steps = self.step_counter.total_steps
                jarak = round(steps * 0.7 / 1000, 2)  # dalam kilometer
                kalori = round(steps * 0.04)
                
                self.steps_label.config(
                    text=f"Langkah: {steps}"
                )
                self.info_label.config(
                    text=f"Jarak: {jarak} km | Kalori: {kalori} kal"
                )
                self.update_ringkasan()
            time.sleep(0.1)
            
    def reset_steps(self):
        self.step_counter.total_steps = 0
        self.step_counter.movement_count = 0
        messagebox.showinfo("Reset", "Penghitung langkah telah direset!")
        
    def save_current_steps(self):
        tanggal = datetime.datetime.now().strftime("%Y-%m-%d")
        steps = self.step_counter.total_steps
        jarak = round(steps * 0.7 / 1000, 2)
        kalori = round(steps * 0.04)
        
        if tanggal not in self.data:
            self.data[tanggal] = {
                'langkah': 0,
                'jarak': 0,
                'kalori': 0,
                'aktivitas': []
            }
            
        self.data[tanggal]['langkah'] += steps
        self.data[tanggal]['jarak'] += jarak
        self.data[tanggal]['kalori'] += kalori
        
        self.save_data()
        self.reset_steps()
        messagebox.showinfo("Sukses", "Data langkah berhasil disimpan!")
        
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as file:
                    return json.load(file)
            except:
                return {}
        return {}
        
    def save_data(self):
        with open(self.data_file, 'w') as file:
            json.dump(self.data, file)
            
    def catat_aktivitas(self):
        try:
            aktivitas = self.aktivitas_entry.get().strip()
            durasi = int(self.durasi_entry.get())
            
            if not aktivitas or durasi < 0:
                raise ValueError
                
            tanggal = datetime.datetime.now().strftime("%Y-%m-%d")
            
            if tanggal not in self.data:
                self.data[tanggal] = {
                    'langkah': 0,
                    'jarak': 0,
                    'kalori': 0,
                    'aktivitas': []
                }
                
            aktivitas_baru = {
                'nama': aktivitas,
                'durasi': durasi,
                'waktu': datetime.datetime.now().strftime("%H:%M")
            }
            
            self.data[tanggal]['aktivitas'].append(aktivitas_baru)
            self.save_data()
            
            self.aktivitas_entry.delete(0, tk.END)
            self.durasi_entry.delete(0, tk.END)
            
            messagebox.showinfo(
                "Sukses", 
                f"Berhasil mencatat aktivitas {aktivitas} selama {durasi} menit!"
            )
            
        except ValueError:
            messagebox.showerror(
                "Error",
                "Masukkan nama aktivitas dan durasi yang valid!"
            )
            
    def update_ringkasan(self):
        tanggal = datetime.datetime.now().strftime("%Y-%m-%d")
        self.summary_text.delete(1.0, tk.END)
        
        current_steps = self.step_counter.total_steps
        current_jarak = round(current_steps * 0.7 / 1000, 2)
        current_kalori = round(current_steps * 0.04)
        
        self.summary_text.insert(tk.END, f"=== Sesi Aktif ===\n")
        self.summary_text.insert(tk.END, f"Langkah: {current_steps}\n")
        self.summary_text.insert(tk.END, f"Jarak: {current_jarak} km\n")
        self.summary_text.insert(tk.END, f"Kalori: {current_kalori} kal\n\n")
        
        if tanggal in self.data:
            ringkasan = self.data[tanggal]
            self.summary_text.insert(tk.END, f"=== Total Hari Ini ===\n")
            self.summary_text.insert(tk.END, f"Total Langkah: {ringkasan['langkah']}\n")
            self.summary_text.insert(tk.END, f"Total Jarak: {ringkasan['jarak']} km\n")
            self.summary_text.insert(tk.END, f"Total Kalori: {ringkasan['kalori']} kal\n\n")
            
            if ringkasan['aktivitas']:
                self.summary_text.insert(tk.END, "Aktivitas Tambahan:\n")
                for aktivitas in ringkasan['aktivitas']:
                    self.summary_text.insert(
                        tk.END,
                        f"- {aktivitas['nama']} ({aktivitas['durasi']} menit) "
                        f"pada {aktivitas['waktu']}\n"
                    )
                    
    def on_closing(self):
        self.step_counter.stop()
        self.mouse_listener.stop()
        self.keyboard_listener.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ActivityTrackerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()