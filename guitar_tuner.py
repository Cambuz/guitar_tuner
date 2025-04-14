import tkinter as tk
from tkinter import ttk
import pyaudio
import numpy as np
from scipy.fft import fft
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import sys
import math
import os

# Modern color scheme
COLORS = {
    'background': '#2C3E50',
    'foreground': '#ECF0F1',
    'accent': '#3498DB',
    'success': '#2ECC71',
    'warning': '#F1C40F',
    'error': '#E74C3C',
    'text': '#ECF0F1',
    'secondary': '#34495E',
    'button_hover': '#2980B9',
    'button_pressed': '#2573A7',
    'input_bg': '#34495E',
    'border': '#7F8C8D',
    'button_text': '#000000'  # Black text for buttons
}

class GuitarTuner:
    def __init__(self, root):
        self.root = root
        self.root.title("Guitar Tuner")
        # Set fixed window size and background
        self.root.geometry("400x600")
        self.root.configure(bg=COLORS['background'])
        
        # Prevent window resizing
        self.root.resizable(False, False)
        
        # Configure style
        self.style = ttk.Style()
        
        # Configure Frame style
        self.style.configure('TFrame', background=COLORS['background'])
        
        # Configure Label style
        self.style.configure('TLabel', 
                           background=COLORS['background'],
                           foreground=COLORS['text'],
                           font=('Arial', 10))
        
        # Configure Button style
        self.style.configure('TButton',
                           background=COLORS['accent'],
                           foreground=COLORS['button_text'],  # Black text
                           padding=(20, 10),
                           font=('Arial', 12, 'bold'))
        self.style.map('TButton',
                      background=[('active', COLORS['button_hover']),
                                ('pressed', COLORS['button_pressed'])],
                      foreground=[('active', COLORS['button_text']),  # Keep black text on hover
                                ('pressed', COLORS['button_text'])])  # Keep black text when pressed
        
        # Configure Radiobutton style
        self.style.configure('TRadiobutton',
                           background=COLORS['background'],
                           foreground=COLORS['text'],
                           font=('Arial', 10))
        self.style.map('TRadiobutton',
                      background=[('active', COLORS['background'])],
                      foreground=[('active', COLORS['accent'])])
        
        # Configure Combobox style
        self.style.configure('TCombobox',
                           background='#ECF0F1',  # Light background
                           foreground=COLORS['button_text'],  # Black text
                           fieldbackground='#ECF0F1',  # Light background for the field
                           arrowcolor=COLORS['button_text'],  # Black arrow
                           borderwidth=1,
                           relief='solid',
                           padding=(5, 2))
        
        self.style.map('TCombobox',
                      fieldbackground=[('readonly', '#ECF0F1')],  # Light background in readonly state
                      selectbackground=[('readonly', COLORS['accent'])],
                      selectforeground=[('readonly', COLORS['text'])],  # White text for selected item
                      background=[('readonly', '#ECF0F1'),
                                ('active', COLORS['accent'])],
                      foreground=[('readonly', COLORS['button_text'])])  # Black text in readonly state
        
        # Make Combobox text readable
        self.root.option_add('*TCombobox*Listbox.background', '#ECF0F1')  # Light background for dropdown
        self.root.option_add('*TCombobox*Listbox.foreground', COLORS['button_text'])  # Black text for dropdown
        self.root.option_add('*TCombobox*Listbox.selectBackground', COLORS['accent'])  # Blue for selected item
        self.root.option_add('*TCombobox*Listbox.selectForeground', COLORS['text'])  # White text for selected item
        self.root.option_add('*TCombobox*Listbox.font', ('Arial', 9))
        
        # Set Combobox to readonly state
        self.root.option_add('*TCombobox*background', '#ECF0F1')  # Light background
        self.root.option_add('*TCombobox*foreground', COLORS['button_text'])  # Black text
        self.root.option_add('*TCombobox*fieldbackground', '#ECF0F1')  # Light background for field
        self.root.option_add('*TCombobox*font', ('Arial', 9))
        
        # Configuration audio
        self.CHUNK = 2048
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 44100
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.current_device = None
        
        # Configuration de détection des notes
        self.NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.A4_FREQ = 440.0
        
        # Décalage d'accordage en demi-tons
        self.semitone_offset = 0
        
        # Création des éléments de l'interface graphique
        self.create_gui()
        
        # Démarrage du thread de traitement audio
        self.running = True
        self.audio_thread = threading.Thread(target=self.process_audio)
        self.audio_thread.start()
        
        # Configuration de la fermeture correcte de la fenêtre
        self.root.protocol("WM_DELETE_WINDOW", self.close)
    
    def get_input_devices(self):
        """Récupère la liste des périphériques d'entrée audio"""
        devices = []
        bluetooth_keywords = ['bluetooth', 'bt', 'wireless']  # Keywords to identify Bluetooth devices
        
        for i in range(self.p.get_device_count()):
            try:
                device_info = self.p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # C'est un périphérique d'entrée
                    name = device_info['name'].lower()
                    
                    # Skip Bluetooth devices
                    if any(keyword in name for keyword in bluetooth_keywords):
                        print(f"Skipping Bluetooth device: {device_info['name']}")
                        continue
                    
                    # Test if the device can be opened with our settings
                    try:
                        test_stream = self.p.open(
                            format=self.FORMAT,
                            channels=self.CHANNELS,
                            rate=self.RATE,
                            input=True,
                            input_device_index=i,
                            frames_per_buffer=self.CHUNK,
                            start=False  # Don't start the stream, just test if it can be opened
                        )
                        test_stream.close()
                        devices.append((device_info['name'], i))
                        print(f"Added USB device: {device_info['name']}")
                    except Exception as e:
                        print(f"Device {device_info['name']} is not compatible: {str(e)}")
            except Exception as e:
                print(f"Error getting device info for index {i}: {str(e)}")
        
        if not devices:
            print("No compatible USB audio devices found")
        
        return devices
    
    def on_device_change(self, event):
        """Gestion du changement de périphérique audio"""
        try:
            selection = self.device_combo.get()
            device_index = None
            
            # Trouver l'index du périphérique sélectionné
            for name, idx in self.input_devices:
                if name == selection:
                    device_index = idx
                    break
            
            if device_index is not None and device_index != self.current_device:
                self.current_device = device_index
                # Redémarrer le flux audio avec le nouveau périphérique
                self.restart_audio_stream()
        except Exception as e:
            error_msg = f"Erreur lors du changement de périphérique: {str(e)}"
            print(error_msg)
            self.show_error_message(error_msg)
    
    def restart_audio_stream(self):
        """Redémarre le flux audio avec le nouveau périphérique"""
        # Fermer l'ancien flux s'il existe
        if self.stream is not None:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                print(f"Error closing previous stream: {str(e)}")
        
        # Créer un nouveau flux avec le périphérique sélectionné
        try:
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=self.current_device,
                frames_per_buffer=self.CHUNK
            )
            print(f"Successfully opened audio stream for device index {self.current_device}")
        except Exception as e:
            error_msg = f"Erreur lors de l'ouverture du périphérique audio: {str(e)}"
            print(error_msg)
            # Reset stream to None
            self.stream = None
            # Update UI to show error
            self.show_error_message(error_msg)
    
    def show_error_message(self, message):
        """Affiche un message d'erreur dans l'interface"""
        # Update the note display to show error
        self.detected_note_label.config(text="!", foreground=COLORS['error'])
        self.octave_label.config(text="Erreur périphérique")
        self.freq_label.config(text="--")
        self.cents_label.config(text=message[:20] + "..." if len(message) > 20 else message)
        
        # Reset the needle to center
        self.canvas.delete("needle")
        canvas_width = 250
        canvas_center = canvas_width // 2
        self.canvas.create_line(canvas_center, 30, canvas_center, 30, 
                              fill=COLORS['error'], width=3, tags="needle")

    def create_gui(self):
        # Création du cadre principal avec padding et background
        main_frame = ttk.Frame(self.root, padding="10", style='TFrame')
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure root grid weights for centering
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Configure main frame grid weights for centering
        main_frame.grid_columnconfigure(0, weight=1)
        for i in range(9):  # We have 9 rows in total
            main_frame.grid_rowconfigure(i, weight=1)
        
        # Création du sélecteur de périphérique audio avec style moderne
        device_frame = ttk.Frame(main_frame, style='TFrame')
        device_frame.grid(row=0, column=0, pady=5, sticky="ew")
        device_frame.grid_columnconfigure(0, weight=1)
        device_frame.grid_rowconfigure(0, weight=1)
        
        # Style the input label
        input_label = ttk.Label(device_frame, text="Entrée:", style='TLabel')
        input_label.grid(row=0, column=0, padx=5)
        
        self.input_devices = self.get_input_devices()
        device_names = [name for name, _ in self.input_devices]
        
        # Style the device combobox
        self.device_combo = ttk.Combobox(device_frame, 
                                       values=device_names, 
                                       width=30, 
                                       style='TCombobox',
                                       state='readonly')
        if device_names:
            self.device_combo.set(device_names[0])
            self.current_device = self.input_devices[0][1]
        self.device_combo.grid(row=0, column=1, padx=5, sticky="ew")
        self.device_combo.bind('<<ComboboxSelected>>', self.on_device_change)
        
        # Center frames for all elements
        note_frame = ttk.Frame(main_frame, style='TFrame')
        note_frame.grid(row=1, column=0, pady=(20,10), sticky="nsew")
        note_frame.grid_columnconfigure(0, weight=1)
        note_frame.grid_rowconfigure(0, weight=1)
        self.detected_note_label = ttk.Label(note_frame, text="--", font=("Arial", 100, "bold"), style='TLabel')
        self.detected_note_label.grid(row=0, column=0)
        
        octave_frame = ttk.Frame(main_frame, style='TFrame')
        octave_frame.grid(row=2, column=0, pady=5, sticky="nsew")
        octave_frame.grid_columnconfigure(0, weight=1)
        octave_frame.grid_rowconfigure(0, weight=1)
        self.octave_label = ttk.Label(octave_frame, text="Octave: --", font=("Arial", 20), style='TLabel')
        self.octave_label.grid(row=0, column=0)
        
        freq_frame = ttk.Frame(main_frame, style='TFrame')
        freq_frame.grid(row=3, column=0, pady=5, sticky="nsew")
        freq_frame.grid_columnconfigure(0, weight=1)
        freq_frame.grid_rowconfigure(0, weight=1)
        self.freq_label = ttk.Label(freq_frame, text="0 Hz", font=("Arial", 20), style='TLabel')
        self.freq_label.grid(row=0, column=0)
        
        cents_frame = ttk.Frame(main_frame, style='TFrame')
        cents_frame.grid(row=4, column=0, pady=5, sticky="nsew")
        cents_frame.grid_columnconfigure(0, weight=1)
        cents_frame.grid_rowconfigure(0, weight=1)
        self.cents_label = ttk.Label(cents_frame, text="± 0 cents", font=("Arial", 20), style='TLabel')
        self.cents_label.grid(row=0, column=0)
        
        # Création de l'indicateur d'accordage avec style moderne
        self.tuning_frame = ttk.Frame(main_frame, style='TFrame')
        self.tuning_frame.grid(row=5, column=0, pady=10, sticky="nsew")
        self.tuning_frame.grid_columnconfigure(0, weight=1)
        self.tuning_frame.grid_rowconfigure(0, weight=1)
        
        # Création du canevas pour l'affichage de l'aiguille avec fond sombre
        self.canvas = tk.Canvas(self.tuning_frame, width=250, height=60, bg=COLORS['secondary'])
        self.canvas.grid(row=0, column=0)
        
        # Dessin de la base de l'aiguille et des marqueurs
        self.draw_tuning_scale()
        
        # Création du sélecteur de cordes avec style moderne
        string_frame = ttk.Frame(main_frame, style='TFrame')
        string_frame.grid(row=6, column=0, pady=10, sticky="nsew")
        string_frame.grid_columnconfigure(0, weight=1)
        string_frame.grid_rowconfigure(0, weight=1)
        
        # Create an inner frame for the radio buttons to center them as a group
        string_buttons_frame = ttk.Frame(string_frame, style='TFrame')
        string_buttons_frame.grid(row=0, column=0)
        
        self.string_var = tk.StringVar(value="E2")  # Default to low E
        strings = [("E2", "E ⬇"), ("A2", "A"), ("D3", "D"), ("G3", "G"), ("B3", "B"), ("E4", "E ⬆")]  # (value, display_text)
        for value, display_text in strings:
            ttk.Radiobutton(string_buttons_frame, 
                          text=display_text, 
                          variable=self.string_var,
                          value=value, 
                          style='TRadiobutton').pack(side="left", padx=5)
        
        # Création du sélecteur de décalage d'accordage avec style moderne
        tuning_frame = ttk.Frame(main_frame, style='TFrame')
        tuning_frame.grid(row=7, column=0, pady=10, sticky="nsew")
        tuning_frame.grid_columnconfigure(0, weight=1)
        tuning_frame.grid_rowconfigure(0, weight=1)
        
        # Create an inner frame for the tuning controls to center them as a group
        tuning_controls_frame = ttk.Frame(tuning_frame, style='TFrame')
        tuning_controls_frame.grid(row=0, column=0)
        
        # Style the tuning controls
        ttk.Label(tuning_controls_frame, 
                 text="Décalage:", 
                 style='TLabel').pack(side="left", padx=5)
        
        self.offset_var = tk.StringVar(value="0")
        offset_combo = ttk.Combobox(tuning_controls_frame, 
                                  textvariable=self.offset_var, 
                                  width=3, 
                                  style='TCombobox',
                                  state='readonly',
                                  justify='center')
        offset_combo['values'] = [str(i) for i in range(-12, 13)]
        offset_combo.pack(side="left", padx=5)
        offset_combo.bind('<<ComboboxSelected>>', self.on_offset_change)
        
        ttk.Label(tuning_controls_frame, 
                 text="demi-tons", 
                 style='TLabel').pack(side="left", padx=5)
        
        # Style the quit button
        quit_frame = ttk.Frame(main_frame, style='TFrame')
        quit_frame.grid(row=8, column=0, pady=20, sticky="nsew")
        quit_frame.grid_columnconfigure(0, weight=1)
        quit_frame.grid_rowconfigure(0, weight=1)
        
        quit_button = ttk.Button(quit_frame, 
                               text="Quitter",
                               command=self.close,
                               style='Quit.TButton')  # Use the specific quit button style
        quit_button.grid(row=0, column=0, padx=10, pady=5)
        
        # Initialize audio stream with default device
        self.restart_audio_stream()
    
    def draw_tuning_scale(self):
        # Adjust canvas dimensions
        canvas_width = 250
        canvas_center = canvas_width // 2
        
        # Dessin de la ligne centrale
        self.canvas.create_line(canvas_center, 0, canvas_center, 60, fill=COLORS['text'], width=2)
        
        # Dessin des marqueurs d'échelle
        for i in range(-50, 51, 10):
            x = canvas_center + (i * 1.25)  # Reduced scale factor for smaller width
            height = 12 if i % 20 == 0 else 6
            self.canvas.create_line(x, 30-height, x, 30+height, fill=COLORS['text'])
            if i % 20 == 0 and i != 0:
                self.canvas.create_text(x, 50, text=str(i), fill=COLORS['text'], font=("Arial", 8))
    
    def frequency_to_note(self, frequency):
        if frequency <= 0:
            return "--", 0, 0
        
        # Calcul du numéro de note par rapport à A4
        note_number = 12 * math.log2(frequency / self.A4_FREQ)
        # Arrondi à la note la plus proche
        rounded_note = round(note_number)
        # Calcul de la déviation en cents
        cents = 100 * (note_number - rounded_note)
        
        # Calcul de l'octave et de la note
        octave = 4 + (rounded_note + 9) // 12
        note_index = (rounded_note + 9) % 12
        note_name = self.NOTES[note_index]
        
        return note_name, octave, cents
    
    def on_offset_change(self, event):
        try:
            self.semitone_offset = int(self.offset_var.get())
            self.update_display(self.last_frequency if hasattr(self, 'last_frequency') else 0)
        except ValueError:
            pass
    
    def process_audio(self):
        while self.running:
            if self.stream is None:
                time.sleep(0.1)
                continue
                
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.float32)
                
                # Exécution de la FFT
                fft_data = fft(audio_data)
                freqs = np.fft.fftfreq(len(fft_data), 1/self.RATE)
                
                # Recherche de la fréquence dominante
                magnitude_spectrum = np.abs(fft_data)
                peak_index = np.argmax(magnitude_spectrum)
                peak_freq = abs(freqs[peak_index])
                
                # Mise à jour uniquement si l'amplitude est significative (réduction du bruit)
                if magnitude_spectrum[peak_index] > 0.01:
                    self.last_frequency = peak_freq
                    self.root.after(0, self.update_display, peak_freq)
                
            except Exception as e:
                if self.running:
                    error_msg = f"Erreur lors du traitement audio: {str(e)}"
                    print(error_msg)
                    self.root.after(0, self.show_error_message, error_msg)
                time.sleep(0.1)  # Pause before retrying
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                print(f"Error closing stream during shutdown: {str(e)}")
    
    def update_display(self, frequency):
        # Obtention des informations de la note
        note, octave, cents = self.frequency_to_note(frequency)
        
        # Mise à jour des affichages
        self.freq_label.config(text=f"{frequency:.1f} Hz")
        self.detected_note_label.config(text=note)
        self.octave_label.config(text=f"Octave: {octave}")
        self.cents_label.config(text=f"± {abs(cents):.0f} cents")
        
        # Mise à jour de la position de l'aiguille
        self.canvas.delete("needle")
        canvas_width = 250
        canvas_center = canvas_width // 2
        needle_x = canvas_center + (cents * 1.25)  # Adjusted scale factor to match new width
        
        # Change needle color based on tuning accuracy
        if abs(cents) < 5:
            needle_color = COLORS['success']
            self.detected_note_label.config(foreground=COLORS['success'])
        elif abs(cents) < 15:
            needle_color = COLORS['warning']
            self.detected_note_label.config(foreground=COLORS['warning'])
        else:
            needle_color = COLORS['error']
            self.detected_note_label.config(foreground=COLORS['error'])
            
        self.canvas.create_line(canvas_center, 30, needle_x, 30, fill=needle_color, width=3, tags="needle")

    def close(self):
        """Arrêt correct de l'application"""
        print("Arrêt en cours...")
        
        # Signal d'arrêt du thread audio
        self.running = False
        
        try:
            # Attente de la fin du thread audio avec timeout court
            if self.audio_thread.is_alive():
                self.audio_thread.join(timeout=0.5)
                
            # Forcer l'arrêt de PyAudio même si le thread est toujours actif
            if hasattr(self, 'p') and self.p:
                try:
                    self.p.terminate()
                except:
                    pass
            
            # Destruction de la fenêtre
            if self.root:
                self.root.quit()
                self.root.destroy()
                
        except Exception as e:
            print(f"Erreur lors de l'arrêt: {e}")
        finally:
            # Forcer la sortie de l'application
            os._exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = GuitarTuner(root)
    root.mainloop() 