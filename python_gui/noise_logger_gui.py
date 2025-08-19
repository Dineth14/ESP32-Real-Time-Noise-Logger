import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial
import serial.tools.list_ports
import threading
import time
import queue
from datetime import datetime
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ESP32NoiseLoggerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("ESP32 Noise Logger - Real-time Audio Classification")
        self.root.geometry("1200x800")
        
        # Serial connection
        self.serial_connection: Optional[serial.Serial] = None
        self.connected: bool = False
        
        # Data storage
        self.feature_history: List[Dict[str, float]] = []
        self.classification_history: List[str] = []
        self.max_history: int = 100
        
        # Threading
        self.data_queue: queue.Queue[str] = queue.Queue()
        self.running: bool = True
        
        # Current features
        self.current_features: Optional[Dict[str, float]] = None
        self.current_classification: str = "unknown"
        self.current_confidence: float = 0.0
        
        # GUI elements (will be initialized in setup_ui)
        self.port_var: tk.StringVar = tk.StringVar()
        self.port_combo: ttk.Combobox
        self.connect_btn: ttk.Button
        self.connection_status: ttk.Label
        self.uptime_label: ttk.Label
        self.samples_label: ttk.Label
        self.memory_label: ttk.Label
        self.feature_labels: Dict[str, ttk.Label] = {}
        self.classification_label: ttk.Label
        self.confidence_label: ttk.Label
        self.history_listbox: tk.Listbox
        self.custom_label_var: tk.StringVar = tk.StringVar()
        self.dataset_info_label: ttk.Label
        self.fig: Figure
        self.ax: Axes
        self.canvas: FigureCanvasTkAgg
        self.log_text: scrolledtext.ScrolledText
        
        self.setup_ui()
        self.start_data_thread()
        
    def setup_ui(self) -> None:
        # Create main frames
        self.create_connection_frame()
        self.create_status_frame()
        self.create_features_frame()
        self.create_classification_frame()
        self.create_labeling_frame()
        self.create_dataset_frame()
        self.create_plot_frame()
        self.create_log_frame()
        
    def create_connection_frame(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Connection", padding=10)
        frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Port selection
        ttk.Label(frame, text="Port:").grid(row=0, column=0, padx=5)
        self.port_combo = ttk.Combobox(frame, textvariable=self.port_var, width=15)
        self.port_combo.grid(row=0, column=1, padx=5)
        
        # Refresh ports button
        ttk.Button(frame, text="Refresh", command=self.refresh_ports).grid(row=0, column=2, padx=5)
        
        # Connect button
        self.connect_btn = ttk.Button(frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=3, padx=5)
        
        # Connection status
        self.connection_status = ttk.Label(frame, text="Disconnected", foreground="red")
        self.connection_status.grid(row=0, column=4, padx=5)
        
        self.refresh_ports()
        
    def create_status_frame(self) -> None:
        frame = ttk.LabelFrame(self.root, text="System Status", padding=10)
        frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Status labels
        self.uptime_label = ttk.Label(frame, text="Uptime: --")
        self.uptime_label.grid(row=0, column=0, padx=10)
        
        self.samples_label = ttk.Label(frame, text="Samples: --")
        self.samples_label.grid(row=0, column=1, padx=10)
        
        self.memory_label = ttk.Label(frame, text="Free Memory: --")
        self.memory_label.grid(row=0, column=2, padx=10)
        
    def create_features_frame(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Audio Features", padding=10)
        frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        # Feature labels
        features = ["RMS", "ZCR", "Spectral Centroid", "Low Energy", "Mid Energy", "High Energy", "Spectral Flux"]
        
        for i, feature in enumerate(features):
            ttk.Label(frame, text=f"{feature}:").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            label = ttk.Label(frame, text="--", foreground="blue")
            label.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.feature_labels[feature] = label
            
    def create_classification_frame(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Classification", padding=10)
        frame.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        
        # Current classification
        ttk.Label(frame, text="Current Classification:", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=5)
        
        self.classification_label = ttk.Label(frame, text="unknown", font=("Arial", 14), foreground="green")
        self.classification_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.confidence_label = ttk.Label(frame, text="Confidence: --%")
        self.confidence_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Classification history
        ttk.Label(frame, text="Recent Classifications:", font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=2, pady=(10, 5))
        
        self.history_listbox = tk.Listbox(frame, height=10, width=25)
        self.history_listbox.grid(row=4, column=0, columnspan=2, pady=5)
        
    def create_labeling_frame(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Label Current Sound", padding=10)
        frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Predefined label buttons
        labels = ["traffic", "machinery", "human", "background", "other"]
        for i, label in enumerate(labels):
            btn = ttk.Button(frame, text=label.title(), 
                           command=lambda l=label: self.label_current_sound(l))
            btn.grid(row=0, column=i, padx=5, pady=5)
        
        # Custom label
        ttk.Label(frame, text="Custom:").grid(row=1, column=0, padx=5, pady=5)
        entry = ttk.Entry(frame, textvariable=self.custom_label_var, width=15)
        entry.grid(row=1, column=1, padx=5, pady=5)
        entry.bind("<Return>", lambda e: self.label_current_sound(self.custom_label_var.get()))
        
        ttk.Button(frame, text="Label", 
                  command=lambda: self.label_current_sound(self.custom_label_var.get())).grid(row=1, column=2, padx=5, pady=5)
        
    def create_dataset_frame(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Dataset Management", padding=10)
        frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Dataset info
        self.dataset_info_label = ttk.Label(frame, text="Total samples: 0")
        self.dataset_info_label.grid(row=0, column=0, columnspan=3, pady=5)
        
        # Control buttons
        ttk.Button(frame, text="Save Dataset", command=self.save_dataset).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(frame, text="Load Dataset", command=self.load_dataset).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Clear Dataset", command=self.clear_dataset).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(frame, text="Get Status", command=self.get_status).grid(row=1, column=3, padx=5, pady=5)
        
    def create_plot_frame(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Feature Visualization", padding=10)
        frame.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 4))  # type: ignore
        self.canvas = FigureCanvasTkAgg(self.fig, frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize empty plot
        self.ax.set_title("Real-time Audio Features")  # type: ignore
        self.ax.set_xlabel("Time")  # type: ignore
        self.ax.set_ylabel("Feature Value")  # type: ignore
        self.ax.grid(True)  # type: ignore
        
    def create_log_frame(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Communication Log", padding=10)
        frame.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(frame, height=8, width=100)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for resizing
        self.root.grid_rowconfigure(5, weight=1)
        self.root.grid_rowconfigure(6, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
    def refresh_ports(self) -> None:
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])
            
    def toggle_connection(self) -> None:
        if self.connected:
            self.disconnect()
        else:
            self.connect()
            
    def connect(self) -> None:
        try:
            port = self.port_var.get()
            if not port:
                messagebox.showerror("Error", "Please select a port")
                return
                
            self.serial_connection = serial.Serial(port, 115200, timeout=1)
            time.sleep(2)  # Wait for ESP32 to reset
            
            self.connected = True
            self.connect_btn.config(text="Disconnect")
            self.connection_status.config(text="Connected", foreground="green")
            self.log_message(f"Connected to {port}")
            
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self.log_message(f"Connection failed: {e}")
            
    def disconnect(self) -> None:
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
            
        self.connected = False
        self.connect_btn.config(text="Connect")
        self.connection_status.config(text="Disconnected", foreground="red")
        self.log_message("Disconnected")
        
    def send_command(self, command: str) -> bool:
        if self.connected and self.serial_connection:
            try:
                self.serial_connection.write((command + "\n").encode())
                self.log_message(f"Sent: {command}")
                return True
            except Exception as e:
                self.log_message(f"Send error: {e}")
                return False
        return False
        
    def label_current_sound(self, label: str) -> None:
        if not label.strip():
            messagebox.showwarning("Warning", "Please enter a label")
            return
            
        if self.send_command(f"LABEL:{label}"):
            self.log_message(f"Labeled current sound as: {label}")
            self.custom_label_var.set("")
            
    def save_dataset(self) -> None:
        self.send_command("SAVE_DATA")
        
    def load_dataset(self) -> None:
        self.send_command("LOAD_DATA")
        
    def clear_dataset(self) -> None:
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all training data?"):
            self.send_command("CLEAR_DATA")
            
    def get_status(self) -> None:
        self.send_command("GET_STATUS")
        
    def start_data_thread(self) -> None:
        self.data_thread = threading.Thread(target=self.data_reader, daemon=True)
        self.data_thread.start()
        
        # Start GUI update timer
        self.root.after(100, self.process_data_queue)
        
    def data_reader(self) -> None:
        while self.running:
            if self.connected and self.serial_connection:
                try:
                    if self.serial_connection.in_waiting:
                        line = self.serial_connection.readline().decode().strip()
                        if line:
                            self.data_queue.put(line)
                except Exception as e:
                    self.data_queue.put(f"ERROR:Serial read error: {e}")
            time.sleep(0.01)
            
    def process_data_queue(self) -> None:
        try:
            while True:
                line = self.data_queue.get_nowait()
                self.process_serial_data(line)
        except queue.Empty:
            pass
        finally:
            if self.running:
                self.root.after(100, self.process_data_queue)
                
    def process_serial_data(self, line: str) -> None:
        self.log_message(f"Received: {line}")
        
        if line.startswith("FEATURES:"):
            self.parse_features(line)
        elif line.startswith("STATUS:"):
            self.parse_status(line)
        elif line.startswith("LABELED:"):
            self.parse_label_confirmation(line)
        elif line.startswith("DATASET:"):
            self.parse_dataset_info(line)
        elif line.startswith("ERROR:"):
            self.log_message(line, "error")
        elif line.startswith("OK:"):
            self.log_message(line, "success")
            
    def parse_features(self, line: str) -> None:
        try:
            data = line.split(":")[1].split(",")
            if len(data) >= 9:
                features = {
                    "RMS": float(data[0]),
                    "ZCR": float(data[1]),
                    "Spectral Centroid": float(data[2]),
                    "Low Energy": float(data[3]),
                    "Mid Energy": float(data[4]),
                    "High Energy": float(data[5]),
                    "Spectral Flux": float(data[6])
                }
                
                classification = data[7]
                confidence = float(data[8]) * 100
                
                self.update_features_display(features)
                self.update_classification_display(classification, confidence)
                self.update_plots(features)
                
        except Exception as e:
            self.log_message(f"Error parsing features: {e}")
            
    def parse_status(self, line: str) -> None:
        try:
            data = line.split(":")[1].split(",")
            samples = data[0]
            uptime = int(data[1]) // 1000  # Convert to seconds
            memory = data[2]
            
            self.samples_label.config(text=f"Samples: {samples}")
            self.uptime_label.config(text=f"Uptime: {uptime}s")
            self.memory_label.config(text=f"Free Memory: {memory} bytes")
            
        except Exception as e:
            self.log_message(f"Error parsing status: {e}")
            
    def parse_label_confirmation(self, line: str) -> None:
        try:
            data = line.split(":")[1].split(",")
            label = data[0]
            total_samples = data[1]
            self.log_message(f"Successfully labeled as '{label}'. Total samples: {total_samples}")
        except Exception as e:
            self.log_message(f"Error parsing label confirmation: {e}")
            
    def parse_dataset_info(self, line: str) -> None:
        try:
            data = line.split(":")[1].split(",")
            total = data[0]
            self.dataset_info_label.config(text=f"Total samples: {total}")
        except Exception as e:
            self.log_message(f"Error parsing dataset info: {e}")
            
    def update_features_display(self, features: Dict[str, float]) -> None:
        for feature_name, value in features.items():
            if feature_name in self.feature_labels:
                self.feature_labels[feature_name].config(text=f"{value:.4f}")
                
    def update_classification_display(self, classification: str, confidence: float) -> None:
        self.classification_label.config(text=classification)
        self.confidence_label.config(text=f"Confidence: {confidence:.1f}%")
        
        # Add to history
        timestamp = datetime.now().strftime("%H:%M:%S")
        history_item = f"{timestamp}: {classification} ({confidence:.1f}%)"
        self.history_listbox.insert(0, history_item)
        
        # Keep only recent items
        if self.history_listbox.size() > 20:
            self.history_listbox.delete(tk.END)
            
    def update_plots(self, features: Dict[str, float]) -> None:
        # Store feature history
        self.feature_history.append(features)
        if len(self.feature_history) > self.max_history:
            self.feature_history.pop(0)
            
        # Update plot
        if len(self.feature_history) > 1:
            self.ax.clear()
            
            # Plot selected features
            x = range(len(self.feature_history))
            
            # Normalize and plot key features
            rms_values = [f["RMS"] for f in self.feature_history]
            zcr_values = [f["ZCR"] for f in self.feature_history]
            centroid_values = [f["Spectral Centroid"] / 1000 for f in self.feature_history]  # Normalize
            
            self.ax.plot(x, rms_values, label="RMS", linewidth=2)  # type: ignore
            self.ax.plot(x, zcr_values, label="ZCR", linewidth=2)  # type: ignore
            self.ax.plot(x, centroid_values, label="Spectral Centroid (kHz)", linewidth=2)  # type: ignore
            
            self.ax.set_title("Real-time Audio Features")  # type: ignore
            self.ax.set_xlabel("Time (samples)")  # type: ignore
            self.ax.set_ylabel("Feature Value")  # type: ignore
            self.ax.legend()  # type: ignore
            self.ax.grid(True)  # type: ignore
            
            self.canvas.draw()
            
    def log_message(self, message: str, level: str = "info") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        
        # Color coding
        if level == "error":
            # Add red color for errors
            pass
        elif level == "success":
            # Add green color for success
            pass
            
    def on_closing(self) -> None:
        self.running = False
        if self.connected:
            self.disconnect()
        self.root.destroy()

def main() -> None:
    root = tk.Tk()
    app = ESP32NoiseLoggerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
