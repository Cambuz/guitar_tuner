# Guitar Tuner

A modern, user-friendly guitar tuner application built with Python. This application provides real-time pitch detection and visual feedback to help you tune your guitar accurately.

## Features

- Real-time pitch detection
- Visual tuning meter with cents deviation
- Support for all guitar strings (E2 to E4)
- Multiple input device support (USB audio interfaces)
- Tuning offset adjustment (-12 to +12 semitones)
- Modern dark theme interface
- Error handling and device compatibility checks
- Bluetooth device filtering (to avoid compatibility issues)

## Requirements

- Python 3.8 or higher
- PortAudio v19 (required for PyAudio)

### Required Python Packages
```
numpy==1.24.3
pyaudio==0.2.13
scipy==1.10.1
matplotlib==3.7.1
```

## Installation

1. First, install PortAudio:

   **Windows:**
   - PortAudio is included with PyAudio installation

   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt-get install portaudio19-dev python3-pyaudio
   ```

   **macOS:**
   ```bash
   brew install portaudio
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/Cambuz/guitar_tuner.git
   cd guitar_tuner
   ```

3. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

4. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Connect your audio input device (microphone or audio interface)

2. Run the application:
   ```bash
   python guitar_tuner.py
   ```

3. Select your input device from the dropdown menu

4. Play a string on your guitar, and the tuner will:
   - Display the detected note
   - Show the octave
   - Display the frequency
   - Indicate how many cents sharp or flat the note is
   - Show a visual meter for fine-tuning

### String Selection
- Low E (E2) ⬇
- A (A2)
- D (D3)
- G (G3)
- B (B3)
- High E (E4) ⬆

### Tuning Adjustment
You can adjust the reference pitch using the semitone offset selector (-12 to +12 semitones).

## Troubleshooting

1. **No input devices shown:**
   - Check if your audio device is properly connected
   - Ensure your device drivers are up to date
   - Try reconnecting the device

2. **Application crashes:**
   - Make sure you're using a compatible audio device
   - Check if another application is using the audio device
   - Try selecting a different input device

3. **Poor pitch detection:**
   - Reduce background noise
   - Ensure your input device is close to the sound source
   - Check if your input device's gain/volume is set appropriately

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
