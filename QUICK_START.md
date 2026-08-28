# 🚀 ESP32 EMG System - Quick Start Guide

## ⚡ 5-Minute Setup

### What You'll Need
```
✅ ESP32 microcontroller
✅ 3x AD8232 EMG sensors
✅ USB cable
✅ Python 3.9+ (Windows)
✅ WSL2 with Ubuntu (for ROS2)
```

---

## Step 1: Hardware Assembly (5 min)

**Wiring Checklist**:
```
[ ] Connect ESP32 GND to all sensor GND
[ ] Connect 3.3V power to all sensors (NOT 5V!)
[ ] GPIO36 ← Sensor 1 OUTPUT
[ ] GPIO39 ← Sensor 2 OUTPUT
[ ] GPIO34 ← Sensor 3 OUTPUT
[ ] USB cable: ESP32 to Windows COM3
```

**Electrode Placement**:
- Sensor 1, 2: 2-5cm apart on target muscle
- Sensor 3: Reference on low-activity area (elbow)

> See [ARCHITECTURE.md → Hardware](ARCHITECTURE.md#hardware-connections-esp32-devkit-v1) for detailed diagram

---

## Step 2: Firmware Upload (3 min)

```bash
# 1. Open Arduino IDE
# 2. File → Open → firmware/esp32_emg_v2/esp32-ad8232-emg-sensor.ino
# 3. Tools → Board → ESP32 Dev Module
# 4. Tools → Upload Speed → 921600
# 5. Tools → Port → COM3
# 6. Sketch → Upload

# Verify: Tools → Serial Monitor (115200 baud)
# You should see: idx,m1,s1,a1,p1,m2,s2,a2,p2,m3,s3,a3,p13,label
```

---

## Step 3: Python Setup (2 min)

```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pyserial scikit-learn joblib opencv-python numpy pandas paho-mqtt

# Test connection
python scripts/serial_check_wsl.py
```

---

## Step 4: First Prediction (5 min)

```bash
# Terminal 1: Record REST/FIST gestures
python scripts/record/record_rest_fist_v2.py
# Follow prompts - alternate between REST and FIST, 10 cycles

# Terminal 2: Train model
python scripts/train/train_and_save.py
# Output: model/rest_fist_model_v2.joblib (95%+ accuracy)

# Terminal 3: Real-time prediction
python scripts/predict/online_predict.py
# Output: REST/FIST predictions in real-time
```

✅ **Done!** You now have a working EMG-to-prediction system.

---

## Next Steps

### Want Gazebo Simulation?
```bash
# WSL2 Ubuntu terminal
cd ros2_ws
colcon build
source install/setup.bash
ros2 run emg_gripper_control emg_listener

# In separate terminal: gazebo
gazebo --verbose path/to/gripper.world
```

### Want Real Robotic Hand?
```bash
# Attach STServo to COM4
# WSL2 Ubuntu
python real_hand/emg_to_real_hand_bridge.py

# Gripper will open/close with your EMG predictions
```

### Want Cloud Telemetry (Grafana)?
```bash
cd cloud_iot
docker-compose up -d

# Open http://localhost:3000
# Login: admin / admin
# Create dashboard with InfluxDB datasource
```

---

## 📚 Documentation Map

| Need | Location |
|------|----------|
| **Complete Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md) |
| **Setup Guide** | [README.md → Setup & Installation](README.md#-setup--installation) |
| **Troubleshooting** | [ARCHITECTURE.md → Troubleshooting](ARCHITECTURE.md#troubleshooting-guide) |
| **Quick Reference** | [ARCHITECTURE.md → Quick Reference Tables](ARCHITECTURE.md#quick-reference-tables) |
| **FAQ** | [ARCHITECTURE.md → FAQ](ARCHITECTURE.md#faq) |
| **Hardware Wiring** | [ARCHITECTURE.md → Hardware Layer](ARCHITECTURE.md#1-hardware-layer) |
| **Firmware Details** | [ARCHITECTURE.md → Firmware Layer](ARCHITECTURE.md#2-firmware-layer) |
| **ML Models** | [ARCHITECTURE.md → Component Details](ARCHITECTURE.md#component-details) |
| **ROS2 Integration** | [README.md → Advanced Usage](README.md#-advanced-usage) |
| **Cloud IoT Setup** | [README.md → Docker Stack](README.md#5️⃣-cloud-iot-stack-docker) |

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| **"COM port not found"** | Install CH340 drivers: https://sparks.gogo.co.nz/ch340.html |
| **"Garbage in serial monitor"** | Check baud rate is 115200 |
| **"Permission denied /dev/ttyACM0"** | `sudo usermod -a -G dialout $USER` |
| **"USB device not found in WSL2"** | See [WSL2 USB Forwarding](ARCHITECTURE.md#wsl2-usb-forwarding) |
| **"ImportError: No module named 'sklearn'"** | `pip install scikit-learn` |

For more issues, see [ARCHITECTURE.md → Troubleshooting Guide](ARCHITECTURE.md#troubleshooting-guide).

---

## 📊 Key Performance Metrics

```
Sampling Rate:        500 Hz (2ms period)
Feature Window:       50 ms (25 samples)
ML Inference:         < 5 ms
End-to-End Latency:   ~ 25 ms
Accuracy (REST/FIST): 95%+ (after training)
Real-time Accuracy:   92-94% (with smoothing)
```

---

## 🎯 Common Workflows

### Workflow 1: Just Testing EMG Capture
```bash
python scripts/serial_check_wsl.py
# Displays raw EMG features from ESP32
```

### Workflow 2: Train & Predict Locally
```bash
python scripts/record/record_rest_fist_v2.py
python scripts/train/train_and_save.py
python scripts/predict/online_predict.py
```

### Workflow 3: Gazebo Gripper Control
```bash
# Terminal 1: Gazebo
gazebo --verbose path/to/gripper.world

# Terminal 2: ROS2 (WSL2)
source ros2_ws/install/setup.bash
ros2 run emg_gripper_control emg_listener
```

### Workflow 4: Real Robotic Hand + Vision
```bash
# Terminal 1: Vision tracking (Windows)
python real_hand/vision_object_tracker_udp_windows.py

# Terminal 2: Hand bridge (WSL2)
python real_hand/emg_to_real_hand_bridge.py

# Terminal 3: EMG node (WSL2)
ros2 run emg_gripper_control emg_listener
```

### Workflow 5: Full Cloud IoT Stack
```bash
# Terminal 1: Docker services
cd cloud_iot && docker-compose up -d

# Terminal 2: EMG prediction with MQTT publishing
python scripts/predict/online_predict.py

# Terminal 3: Monitor Grafana
# http://localhost:3000
```

---

## 📋 Checklist: Getting Started

- [ ] **Hardware Ready**
  - [ ] ESP32 connected via USB
  - [ ] 3x AD8232 sensors wired
  - [ ] Electrodes placed on arm
  
- [ ] **Firmware Uploaded**
  - [ ] Arduino IDE configured
  - [ ] Sketch uploaded to ESP32
  - [ ] Serial monitor shows data at 115200 baud
  
- [ ] **Python Environment**
  - [ ] Virtual environment created
  - [ ] Dependencies installed
  - [ ] Serial connection test passed
  
- [ ] **First Prediction**
  - [ ] Training data recorded (REST/FIST)
  - [ ] Model trained successfully
  - [ ] Real-time prediction working
  
- [ ] **Next Level** (Optional)
  - [ ] [ ] ROS2 workspace built
  - [ ] [ ] Gazebo simulation running
  - [ ] [ ] Real robotic hand connected
  - [ ] [ ] Docker stack deployed

---

## 💡 Pro Tips

1. **Serial Issues?** → Always close Arduino IDE Serial Monitor before running Python scripts
2. **Low Accuracy?** → Record 1000+ samples per gesture type
3. **High Latency?** → Reduce smoothing parameters or upgrade hardware
4. **WSL2 USB?** → Use `usbipd list` to find device bus ID, then `usbipd attach --wsl --busid <id>`
5. **Grafana Dashboards?** → Set refresh rate to 1s for real-time data

---

## 📞 Getting Help

1. **Quick questions?** → Check [FAQ section](ARCHITECTURE.md#faq)
2. **Setup problems?** → See [Setup & Installation](README.md#-setup--installation)
3. **Not working?** → Check [Troubleshooting Guide](ARCHITECTURE.md#troubleshooting-guide)
4. **Details wanted?** → Read [ARCHITECTURE.md](ARCHITECTURE.md)
5. **Code examples?** → Check [Usage Examples](README.md#-usage-examples)

---

**Start Now** → [README.md](README.md) | [ARCHITECTURE.md](ARCHITECTURE.md) | [Scripts](scripts/)

Good luck! 🎯🤖
