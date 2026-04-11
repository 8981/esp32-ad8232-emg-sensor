# ESP32 + AD8232 EMG Sensor Integration

This project implements an **EMG (Electromyography)** monitoring system using the **AD8232** sensor and an **ESP32** microcontroller. While the AD8232 is traditionally used for ECG, this project applies digital signal processing to extract muscle activity data without hardware modifications.

## Features
- **Real-time Signal Capture**: High-speed analog sampling using ESP32 ADC.
- **Digital Envelope Extraction**: Uses Exponential Moving Average (EMA) to calculate muscle contraction strength.
- **Lead-Off Detection**: Monitors if electrodes are properly attached via GPIO 18/19.
- **Serial Plotter Ready**: Optimized for visualization in Arduino IDE.

## Hardware Connections (ESP32 DevKit V1)


| AD8232 Pin | ESP32 Pin | Logic/Function |
| :--- | :--- | :--- |
| **3.3V** | **3V3** | Power (Strictly 3.3V) |
| **GND** | **GND** | Common Ground |
| **OUTPUT** | **GPIO 36 (VP)** | Analog Signal (ADC1_CH0) |
| **LO-** | **GPIO 18** | Leads-off Detect - |
| **LO+** | **GPIO 19** | Leads-off Detect + |

![Wiring Diagram](images/setup.jpg)

> **Note:** If using a breadboard, ensure that the power rails (+ and -) are bridged between the top and bottom sections to provide consistent power to both the ESP32 and the AD8232.

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
