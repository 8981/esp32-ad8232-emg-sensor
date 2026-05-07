# ESP32 + AD8232 EMG Sensor Integration

This project implements an **EMG (Electromyography)** monitoring system using **three AD8232 sensors** and an **ESP32** microcontroller. While the AD8232 is traditionally used for ECG, this project applies digital signal processing to extract muscle activity data without hardware modifications.

## Features
- **Real-time Signal Capture**: High-speed analog sampling using ESP32 ADC.
- **Digital Envelope Extraction**: Uses Exponential Moving Average (EMA) to calculate muscle contraction strength.
- **Three-channel EMG Capture**: Reads analog EMG signals from three AD8232 modules using ESP32 ADC pins GPIO36, GPIO39, and GPIO34.
- **Lead-Off Detection Pins Reserved**: LO+/LO− pins are connected for all three sensors and can be used to detect whether electrodes are properly attached.
- **Serial Plotter Ready**: Optimized for visualization in Arduino IDE.

## Hardware Connections (ESP32 DevKit V1)

This project uses **three AD8232 modules** connected to one ESP32.  
Each AD8232 sensor has its own analog output pin and optional lead-off detection pins.

| AD8232 Pin | Sensor 1 → ESP32 | Sensor 2 → ESP32 | Sensor 3 → ESP32 | Logic/Function |
| :--- | :--- | :--- | :--- | :--- |
| **3.3V** | **3V3** | **3V3** | **3V3** | Power supply. Use strictly 3.3V |
| **GND** | **GND** | **GND** | **GND** | Common ground |
| **OUTPUT** | **GPIO36 (ADC1_CH0 / VP)** | **GPIO39 (ADC1_CH3 / VN)** | **GPIO34 (ADC1_CH6)** | Analog EMG signal |
| **LO+** | **GPIO19** | **GPIO21** | **GPIO23** | Lead-off detection + |
| **LO−** | **GPIO18** | **GPIO22** | **GPIO25** | Lead-off detection − |

![Wiring Diagram](images/setup.jpg)
![Bandage EMG Electrodes](images/bandage_emg_electrodes.jpg)

> **Important:** All three AD8232 modules must share the same **GND** with the ESP32.  
> The AD8232 modules must be powered from **3.3V**, not 5V.

> **Note:** If using a breadboard, ensure that the power rails (+ and -) are bridged between the top and bottom sections to provide consistent power to the ESP32 and all AD8232 modules.

## Electrode Placement
For optimal muscle sensing:
1. **Red/Yellow (Inputs)**: Place along the muscle fibers (e.g., bicep) about 2-5cm apart.
2. **Green/Black (Reference)**: Place on a "bony" area with no muscle activity (e.g., elbow or kneecap).

## Software Configuration
- **Baud Rate**: 115200
- **ADC Resolution**: 12-bit (0 - 4095)
- **Filtering**: The code removes the DC offset (~2048) and applies an absolute value filter with EMA smoothing.

## How to Run
1. Clone this repository.
2. Open the `.ino` file in Arduino IDE.
3. Select **DOIT ESP32 DEVKIT V1** as your board.
4. Upload and open **Serial Plotter** (Ctrl+Shift+L).

## License
MIT License
