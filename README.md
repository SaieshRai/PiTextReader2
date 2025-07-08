# PiTextReader v3 - Intelligent OCR Text-to-Speech System for Raspberry Pi

## Overview

**PiTextReader v3** is the latest and most advanced version of the Raspberry Pi-based OCR-to-speech system. This assistive device captures printed text, applies OCR, corrects image orientation automatically, and reads the content aloud using a Text-to-Speech engine. It is built for **visually impaired users**, offering a reliable, offline, button-operated experience.

> ✅ This version significantly improves on the **previous two iterations** by introducing **automatic orientation detection**, **error handling**, and **better image resolution support**, resulting in higher OCR accuracy and a more robust user experience.

---

## Key Enhancements Over Previous Versions

| Feature                        | Version 1                          | Version 2                              | **Version 3 (Current)**                        |
|-------------------------------|------------------------------------|----------------------------------------|------------------------------------------------|
| **Image Capture**             | `libcamera-still` CLI              | OpenCV live capture                    | ✅ OpenCV with Full HD (1920x1080) support      |
| **Image Processing**          | ❌ None                            | Grayscale + thresholding               | ✅ Rotation correction using Tesseract          |
| **OCR**                       | Tesseract CLI                      | pytesseract                            | ✅ CLI + Orientation-aware OCR                 |
| **Speech Feedback**           | Flite                              | Flite                                  | ✅ Error-aware speech feedback                  |
| **TTS Interrupt**             | Thread-based                       | Thread-based                           | ✅ Thread-based, stable                         |
| **Logging**                   | Basic                              | Improved                               | ✅ Extensive error reporting + orientation logs |
| **Error Handling**            | Minimal                            | Basic (file existence check)           | ✅ Full handling of empty/no-text OCR results   |
| **Text File Validation**      | ❌ No checks                        | ✅ Checked                              | ✅ Enforced with fallback prompts               |

> 🧠 The most notable addition in this version is **image orientation detection** using Tesseract's `--psm 0` mode, improving OCR accuracy when images are not aligned properly.

---

## Features

- 📷 Capture high-resolution images via OpenCV
- 🔄 Automatically correct image orientation before OCR
- 🧠 Extract text using Tesseract OCR
- 🧼 Clean text for better speech quality using `sed`
- 🔊 Play audio with flite and interrupt on button press
- 📍 LED and button-based interface for ease of use
- 🧵 Background thread to stop speech
- 🪵 Debug logs stored in `debug.log`

---

## Setup Instructions

### Hardware

- Raspberry Pi (with camera module or USB webcam)
- GPIO-connected push button (pin 24)
- LED (pin 18, optional)
- Speaker or headphone output

### Software

Install dependencies:

```bash
sudo apt update
sudo apt install flite tesseract-ocr alsa-utils
pip install opencv-python numpy
```

Enable the camera using:

```bash
sudo raspi-config
# Enable camera and reboot
```

---

## Usage

Run the application with:

```bash
sudo python3 pitextreader.py
```

- Press the button to capture and read text.
- LED turns off during processing and lights up when ready.
- Press again during speech to interrupt.

---

## File Structure

```
PiTextReader/
├── sounds/
│   └── camera-shutter.wav
├── debug.log
└── pitextreader.py  # (This version)
```

---


