# ClipboardQT

## Overview
A PyQt5 application that monitors clipboard, sends text to a QTBatch translation server, and displays translated results.

## Features
- Real-time clipboard monitoring
- Translation of clipboard text
- Simple, clean UI

## Prerequisites
- Python 3.8+
- PyQt5
- requests
- pyperclip

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python main.py
```

## Configuration
- Translation Server URL: Configured in `ClipboardQT.py`
- Monitoring interval: 1 second (adjustable in `ClipboardQT.py`)

## Notes
- Requires a running translation server at specified URL
- Automatically detects clipboard changes
- Manual translation trigger available
