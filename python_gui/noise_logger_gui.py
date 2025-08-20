import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial
import serial.tools.list_ports
import threading
import time
import queue
from datetime import datetime
from typing import Dict, List, Optional

class ESP32NoiseLoggerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("ESP32 Noise Logger - Real-time Audio Classification")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
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
        
        # GUI elements
        self.port_var: tk.StringVar = tk.StringVar()
        self.custom_label_var: tk.StringVar = tk.StringVar()
        self.feature_labels: Dict[str, ttk.Label] = {}
        
        # GUI widgets (initialized in setup_ui)
        self.connection_status: ttk.Label
        self.uptime_label: ttk.Label
        self.samples_label: ttk.Label
        self.memory_label: ttk.Label
        self.classification_label: ttk.Label
        self.confidence_label: ttk.Label
        self.dataset_info_label: ttk.Label
        self.log_text: scrolledtext.ScrolledText
        
        self.setup_ui()
        self.auto_connect_serial()
        self.start_data_thread()

    def setup_ui(self) -> None:
        """Create the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(6, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Connection status and controls
        connection_frame = ttk.Frame(main_frame)
        connection_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        connection_frame.grid_columnconfigure(0, weight=1)
        
        self.connection_status = ttk.Label(connection_frame, text="Connecting...", foreground="orange", font=("Arial", 10, "bold"))
        self.connection_status.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Connection control buttons
        button_frame = ttk.Frame(connection_frame)
        button_frame.grid(row=1, column=0, sticky="w")
        
        ttk.Button(button_frame, text="🔄 Auto Connect", 
                  command=self.reconnect_esp32).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="📋 Manual Select", 
                  command=self.manual_connect_dialog).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="❌ Disconnect", 
                  command=self.disconnect_esp32).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(button_frame, text="🔍 Scan Ports", 
                  command=self.scan_and_display_ports).grid(row=0, column=3)
        
        # System status frame
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.uptime_label = ttk.Label(status_frame, text="Uptime: --")
        self.uptime_label.grid(row=0, column=0, padx=(0, 20))
        
        self.samples_label = ttk.Label(status_frame, text="Samples: --")
        self.samples_label.grid(row=0, column=1, padx=(0, 20))
        
        self.memory_label = ttk.Label(status_frame, text="Free Memory: --")
        self.memory_label.grid(row=0, column=2)
        
        # Real-time results frame
        results_frame = ttk.LabelFrame(main_frame, text="Real-time Classification", padding="10")
        results_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.classification_label = ttk.Label(results_frame, text="Classification: unknown", font=("Arial", 12, "bold"))
        self.classification_label.grid(row=0, column=0, columnspan=2, pady=(0, 5))
        
        self.confidence_label = ttk.Label(results_frame, text="Confidence: 0%")
        self.confidence_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Features display
        features_frame = ttk.Frame(results_frame)
        features_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        self.feature_labels = {}
        feature_names = ["RMS", "ZCR", "Spectral Centroid", "Low Energy", "Mid Energy", "High Energy", "Spectral Flux"]
        
        for i, name in enumerate(feature_names):
            row = i // 2
            col = i % 2
            label = ttk.Label(features_frame, text=f"{name}: --")
            label.grid(row=row, column=col, sticky="w", padx=(0, 20), pady=2)
            self.feature_labels[name.lower().replace(" ", "_")] = label
        
        # Labeling frame
        label_frame = ttk.LabelFrame(main_frame, text="Label Current Sound", padding="10")
        label_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        # Quick label buttons
        button_frame = ttk.Frame(label_frame)
        button_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        
        quick_labels = ["traffic", "machinery", "human", "background", "other"]
        for i, label_text in enumerate(quick_labels):
            btn = ttk.Button(button_frame, text=label_text.capitalize(), 
                           command=lambda l=label_text: self.send_label(l))
            btn.grid(row=0, column=i, padx=2, sticky="ew")
            button_frame.grid_columnconfigure(i, weight=1)
        
        # Custom label
        ttk.Label(label_frame, text="Custom label:").grid(row=1, column=0, sticky="w", pady=(10, 5))
        custom_entry = ttk.Entry(label_frame, textvariable=self.custom_label_var)
        custom_entry.grid(row=2, column=0, sticky="ew", padx=(0, 5))
        custom_entry.bind("<Return>", lambda e: self.send_custom_label())
        
        custom_btn = ttk.Button(label_frame, text="Send Label", command=self.send_custom_label)
        custom_btn.grid(row=2, column=1, sticky="ew")
        
        label_frame.grid_columnconfigure(0, weight=1)
        
        # Dataset info
        dataset_frame = ttk.LabelFrame(main_frame, text="Dataset Information", padding="10")
        dataset_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.dataset_info_label = ttk.Label(dataset_frame, text="Dataset: No data")
        self.dataset_info_label.grid(row=0, column=0, sticky="w")
        
        # Controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ttk.Button(controls_frame, text="Get Status", command=self.request_status).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(controls_frame, text="Save Data", command=self.save_data).grid(row=0, column=1, padx=5)
        ttk.Button(controls_frame, text="Clear Data", command=self.clear_data).grid(row=0, column=2, padx=5)
        ttk.Button(controls_frame, text="Reconnect", command=self.reconnect).grid(row=0, column=3, padx=(5, 0))
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=6, column=0, columnspan=2, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky="nsew")

    def find_esp32_port(self) -> Optional[str]:
        """Find ESP32 board port by checking device descriptions and VID/PID"""
        esp32_keywords = [
            'CP210x',  # Silicon Labs CP2102 (common on ESP32 boards)
            'CH340',   # WCH CH340 USB-to-Serial
            'CH341',   # WCH CH341 USB-to-Serial
            'FTDI',    # FTDI USB-to-Serial
            'ESP32',   # Direct ESP32 reference
            'Silicon Labs',  # Silicon Labs devices
            'USB-SERIAL CH340',  # CH340 description
            'USB2.0-Serial',     # Generic USB serial
        ]
        
        # Known ESP32 VID:PID combinations
        esp32_vid_pids = [
            (0x10C4, 0xEA60),  # Silicon Labs CP2102/CP2104
            (0x1A86, 0x7523),  # WCH CH340
            (0x1A86, 0x55D4),  # WCH CH341
            (0x0403, 0x6001),  # FTDI FT232R
            (0x0403, 0x6010),  # FTDI FT2232H
            (0x303A, 0x1001),  # Espressif ESP32-S2
            (0x303A, 0x1002),  # Espressif ESP32-S3
        ]
        
        try:
            ports = list(serial.tools.list_ports.comports())
            self.log_message(f"Scanning {len(ports)} available ports for ESP32...")
            
            for port in ports:
                # Log port details for debugging
                self.log_message(f"Checking port {port.device}: {port.description}")
                
                # Check by VID/PID first (most reliable)
                if hasattr(port, 'vid') and hasattr(port, 'pid') and port.vid and port.pid:
                    if (port.vid, port.pid) in esp32_vid_pids:
                        self.log_message(f"Found ESP32 by VID/PID: {port.device} (VID:{port.vid:04X}, PID:{port.pid:04X})")
                        return port.device
                
                # Check by description keywords
                description = (port.description or "").upper()
                manufacturer = (port.manufacturer or "").upper()
                
                for keyword in esp32_keywords:
                    if keyword.upper() in description or keyword.upper() in manufacturer:
                        self.log_message(f"Found potential ESP32 by description: {port.device} ({port.description})")
                        return port.device
                        
            return None
            
        except Exception as e:
            self.log_message(f"Error scanning ports: {e}")
            return None

    def test_esp32_connection(self, port: str) -> bool:
        """Test if the given port has an ESP32 with our firmware"""
        try:
            self.log_message(f"Testing connection to {port}...")
            test_connection = serial.Serial(port, 115200, timeout=2)
            time.sleep(2)  # Wait for ESP32 to reset and initialize
            
            # Send multiple test commands to verify it's our firmware
            test_commands = ["GET_STATUS", "GET_FEATURES", "PING"]
            
            for cmd in test_commands:
                test_connection.write((cmd + "\n").encode())
                time.sleep(0.5)
                
                # Read any available responses
                responses: List[str] = []
                while test_connection.in_waiting > 0:
                    response = test_connection.readline().decode().strip()
                    if response:
                        responses.append(response)
                        
                # Check for expected response patterns
                for response in responses:
                    if any(pattern in response for pattern in ["STATUS:", "FEATURES:", "ERROR:", "OK:"]):
                        test_connection.close()
                        self.log_message(f"✓ ESP32 Noise Logger confirmed on {port}")
                        return True
                        
            test_connection.close()
            self.log_message(f"✗ No valid response from {port}")
            return False
            
        except Exception as e:
            self.log_message(f"✗ Connection test failed on {port}: {e}")
            return False

    def auto_connect_serial(self) -> None:
        """Automatically connect to ESP32 with enhanced detection"""
        self.connection_status.config(text="Searching for ESP32...", foreground="orange")
        self.log_message("=== Starting ESP32 Auto-Detection ===")
        
        try:
            # First, try to find ESP32 by hardware detection
            esp32_port = self.find_esp32_port()
            
            if esp32_port:
                self.log_message(f"Attempting connection to detected ESP32 on {esp32_port}")
                if self.test_esp32_connection(esp32_port):
                    self.connect_to_port(esp32_port)
                    return
                    
            # If hardware detection fails, test all available ports
            self.log_message("Hardware detection failed, testing all available ports...")
            ports = list(serial.tools.list_ports.comports())
            
            for port in ports:
                if self.test_esp32_connection(port.device):
                    self.connect_to_port(port.device)
                    return
                    
            # No ESP32 found
            self.connection_status.config(text="No ESP32 Noise Logger found", foreground="red")
            self.connected = False
            self.log_message("❌ No ESP32 Noise Logger found on any port")
            self.log_message("Please check:")
            self.log_message("  - ESP32 is connected via USB")
            self.log_message("  - Correct firmware is uploaded") 
            self.log_message("  - Drivers are installed")
            
        except Exception as e:
            self.connection_status.config(text=f"Auto-connect error: {str(e)}", foreground="red")
            self.connected = False
            self.log_message(f"Auto-connect error: {str(e)}")

    def connect_to_port(self, port: str) -> None:
        """Connect to a specific port"""
        try:
            self.serial_connection = serial.Serial(port, 115200, timeout=1)
            time.sleep(2)  # Wait for ESP32 to reset
            
            self.connected = True
            self.connection_status.config(text=f"✓ Connected: {port}", foreground="green")
            self.log_message(f"🔗 Successfully connected to ESP32 on {port}")
            
            # Send initial commands to sync
            self.serial_connection.write(b"GET_STATUS\n")
            
        except Exception as e:
            self.connected = False
            self.connection_status.config(text=f"Connection failed: {str(e)}", foreground="red")
            self.log_message(f"Connection failed to {port}: {str(e)}")
            
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                self.serial_connection = None

    def manual_connect_dialog(self) -> None:
        """Show manual port selection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manual Port Selection")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select ESP32 Port:", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Port listbox
        frame = ttk.Frame(dialog)
        frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        listbox = tk.Listbox(frame, height=8)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)  # type: ignore
        listbox.configure(yscrollcommand=scrollbar.set)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate ports
        ports = list(serial.tools.list_ports.comports())
        for i, port in enumerate(ports):
            display_text = f"{port.device} - {port.description}"
            listbox.insert(i, display_text)
            
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def connect_selected():
            selection = listbox.curselection()  # type: ignore
            if selection:
                port_index = int(selection[0])  # type: ignore
                selected_port = str(ports[port_index].device)
                dialog.destroy()
                self.connect_to_port(selected_port)
            else:
                messagebox.showwarning("Warning", "Please select a port")
                
        def refresh_ports():
            listbox.delete(0, tk.END)
            ports.clear()
            ports.extend(serial.tools.list_ports.comports())
            for i, port in enumerate(ports):
                display_text = f"{port.device} - {port.description}"
                listbox.insert(i, display_text)
        
        ttk.Button(button_frame, text="Connect", command=connect_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh", command=refresh_ports).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def reconnect_esp32(self) -> None:
        """Reconnect to ESP32 - disconnect first if connected, then auto-connect"""
        if self.connected:
            self.disconnect_esp32()
            time.sleep(1)  # Wait a moment before reconnecting
        self.auto_connect_serial()

    def disconnect_esp32(self) -> None:
        """Disconnect from ESP32"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                self.serial_connection = None
            
            self.connected = False
            self.connection_status.config(text="Disconnected", foreground="red")
            self.log_message("🔌 Disconnected from ESP32")
            
        except Exception as e:
            self.log_message(f"Error during disconnect: {e}")

    def scan_and_display_ports(self) -> None:
        """Scan and display all available ports with details"""
        self.log_message("=== Port Scan Results ===")
        try:
            ports = list(serial.tools.list_ports.comports())
            if not ports:
                self.log_message("No serial ports found")
                return
                
            for i, port in enumerate(ports, 1):
                self.log_message(f"{i}. Port: {port.device}")
                self.log_message(f"   Description: {port.description}")
                self.log_message(f"   Manufacturer: {port.manufacturer or 'Unknown'}")
                
                if hasattr(port, 'vid') and hasattr(port, 'pid'):
                    vid_pid = f"VID:{port.vid:04X}, PID:{port.pid:04X}" if port.vid and port.pid else "Unknown"
                    self.log_message(f"   VID/PID: {vid_pid}")
                
                # Test if it's likely an ESP32
                esp32_indicators: List[str] = []
                if port.description and any(keyword.upper() in port.description.upper() 
                                         for keyword in ['CP210x', 'CH340', 'CH341', 'ESP32', 'Silicon Labs']):
                    esp32_indicators.append("Description match")
                    
                if hasattr(port, 'vid') and hasattr(port, 'pid') and port.vid and port.pid:
                    esp32_vid_pids = [(0x10C4, 0xEA60), (0x1A86, 0x7523), (0x1A86, 0x55D4), 
                                     (0x0403, 0x6001), (0x0403, 0x6010), (0x303A, 0x1001), (0x303A, 0x1002)]
                    if (port.vid, port.pid) in esp32_vid_pids:
                        esp32_indicators.append("VID/PID match")
                
                if esp32_indicators:
                    self.log_message(f"   🎯 Likely ESP32: {', '.join(esp32_indicators)}")
                else:
                    self.log_message(f"   ❓ Unknown device type")
                    
                self.log_message("")  # Empty line between ports
                
        except Exception as e:
            self.log_message(f"Error scanning ports: {e}")

    def start_data_thread(self) -> None:
        """Start background thread for data reception"""
        def data_receiver():
            while self.running:
                try:
                    if self.connected and self.serial_connection and self.serial_connection.is_open:
                        if self.serial_connection.in_waiting > 0:
                            line = self.serial_connection.readline().decode().strip()
                            if line:
                                self.data_queue.put(line)
                except Exception as e:
                    self.log_message(f"Data reception error: {str(e)}")
                    self.connected = False
                time.sleep(0.01)
        
        self.data_thread = threading.Thread(target=data_receiver, daemon=True)
        self.data_thread.start()
        
        # Start data processing
        self.process_queue()

    def process_queue(self) -> None:
        """Process incoming data from queue"""
        try:
            while not self.data_queue.empty():
                line = self.data_queue.get_nowait()
                self.process_serial_data(line)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(50, self.process_queue)

    def process_serial_data(self, data: str) -> None:
        """Process data received from ESP32"""
        try:
            if data.startswith("FEATURES:"):
                self.parse_features(data)
            elif data.startswith("STATUS:"):
                self.parse_status(data)
            elif data.startswith("DATASET:"):
                self.parse_dataset(data)
            elif data.startswith("LABELED:"):
                self.parse_labeled(data)
            elif data.startswith("ERROR:"):
                self.log_message(f"ESP32 Error: {data[6:]}")
            elif data.startswith("OK:"):
                self.log_message(f"ESP32 OK: {data[3:]}")
            else:
                self.log_message(f"ESP32: {data}")
        except Exception as e:
            self.log_message(f"Data processing error: {str(e)}")

    def parse_features(self, data: str) -> None:
        """Parse feature data from ESP32"""
        try:
            parts = data[9:].split(',')  # Remove "FEATURES:" prefix
            if len(parts) >= 9:
                features = {
                    'rms': float(parts[0]),
                    'zcr': float(parts[1]),
                    'spectral_centroid': float(parts[2]),
                    'low_energy': float(parts[3]),
                    'mid_energy': float(parts[4]),
                    'high_energy': float(parts[5]),
                    'spectral_flux': float(parts[6])
                }
                
                self.current_features = features
                self.current_classification = parts[7]
                self.current_confidence = float(parts[8])
                
                self.update_display()
                
        except Exception as e:
            self.log_message(f"Feature parsing error: {str(e)}")

    def parse_status(self, data: str) -> None:
        """Parse status data from ESP32"""
        try:
            parts = data[7:].split(',')  # Remove "STATUS:" prefix
            if len(parts) >= 3:
                sample_count = parts[0]
                uptime_ms = int(parts[1])
                free_memory = parts[2]
                
                uptime_sec = uptime_ms // 1000
                uptime_str = f"{uptime_sec // 60}:{uptime_sec % 60:02d}"
                
                self.samples_label.config(text=f"Samples: {sample_count}")
                self.uptime_label.config(text=f"Uptime: {uptime_str}")
                self.memory_label.config(text=f"Free Memory: {free_memory} bytes")
                
        except Exception as e:
            self.log_message(f"Status parsing error: {str(e)}")

    def parse_dataset(self, data: str) -> None:
        """Parse dataset information"""
        try:
            parts = data[8:].split(',')  # Remove "DATASET:" prefix
            if len(parts) >= 6:
                total = parts[0]
                traffic = parts[1]
                machinery = parts[2]
                human = parts[3]
                background = parts[4]
                other = parts[5]
                
                text = f"Total: {total} (Traffic: {traffic}, Machinery: {machinery}, Human: {human}, Background: {background}, Other: {other})"
                self.dataset_info_label.config(text=text)
                
        except Exception as e:
            self.log_message(f"Dataset parsing error: {str(e)}")

    def parse_labeled(self, data: str) -> None:
        """Parse labeling confirmation"""
        try:
            parts = data[8:].split(',')  # Remove "LABELED:" prefix
            if len(parts) >= 2:
                label = parts[0]
                count = parts[1]
                self.log_message(f"Labeled as '{label}' - Total samples: {count}")
                
        except Exception as e:
            self.log_message(f"Label parsing error: {str(e)}")

    def update_display(self) -> None:
        """Update the GUI display with current data"""
        if self.current_features:
            # Update classification
            self.classification_label.config(text=f"Classification: {self.current_classification}")
            self.confidence_label.config(text=f"Confidence: {self.current_confidence*100:.1f}%")
            
            # Update features
            self.feature_labels['rms'].config(text=f"RMS: {self.current_features['rms']:.4f}")
            self.feature_labels['zcr'].config(text=f"ZCR: {self.current_features['zcr']:.4f}")
            self.feature_labels['spectral_centroid'].config(text=f"Spectral Centroid: {self.current_features['spectral_centroid']:.1f}")
            self.feature_labels['low_energy'].config(text=f"Low Energy: {self.current_features['low_energy']:.4f}")
            self.feature_labels['mid_energy'].config(text=f"Mid Energy: {self.current_features['mid_energy']:.4f}")
            self.feature_labels['high_energy'].config(text=f"High Energy: {self.current_features['high_energy']:.4f}")
            self.feature_labels['spectral_flux'].config(text=f"Spectral Flux: {self.current_features['spectral_flux']:.4f}")

    def send_command(self, command: str) -> None:
        """Send command to ESP32"""
        try:
            if self.connected and self.serial_connection:
                self.serial_connection.write(f"{command}\n".encode())
                self.log_message(f"Sent: {command}")
            else:
                self.log_message("Not connected to ESP32")
        except Exception as e:
            self.log_message(f"Send error: {str(e)}")

    def send_label(self, label: str) -> None:
        """Send label for current sound"""
        self.send_command(f"LABEL:{label}")

    def send_custom_label(self) -> None:
        """Send custom label"""
        label = self.custom_label_var.get().strip()
        if label:
            self.send_label(label)
            self.custom_label_var.set("")

    def request_status(self) -> None:
        """Request status from ESP32"""
        self.send_command("GET_STATUS")
        self.send_command("GET_DATASET")

    def save_data(self) -> None:
        """Save data on ESP32"""
        self.send_command("SAVE_DATA")

    def clear_data(self) -> None:
        """Clear data on ESP32"""
        if messagebox.askyesno("Confirm", "Clear all training data?"):
            self.send_command("CLEAR_DATA")

    def reconnect(self) -> None:
        """Reconnect to ESP32"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.connected = False
        self.connection_status.config(text="Reconnecting...", foreground="orange")
        self.root.after(1000, self.auto_connect_serial)

    def log_message(self, message: str) -> None:
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def on_closing(self) -> None:
        """Handle window closing"""
        self.running = False
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = ESP32NoiseLoggerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.on_closing()


if __name__ == "__main__":
    main()
