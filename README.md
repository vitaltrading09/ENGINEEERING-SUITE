# ⚡ Engineering Calculator Suite — Solareff

A desktop application for electrical engineering calculations, PV system design,
screen-capture reporting, and engineering reference guides.

Built with **Python 3** and **PyQt6**.

---

## Included Tools

| Tool | Description |
|---|---|
| **Voltage Drop** | SANS 10142 voltage drop calculation (3 methods) |
| **Cable CCC & Derating** | Current-carrying capacity with derating factors |
| **Short Circuit Current** | IEC 60909 fault-current calculator |
| **Gland Size & BOQ** | Cable gland sizing and bill of quantities |
| **PV System Design** | String sizing + panel layout & stringing |
| **Screen Report Builder** | Capture screenshots and export a branded PDF / Word report |
| **Datasheet Library** | Searchable library of cable, inverter and panel datasheets |
| **Engineering Guides** | Reference guides for SANS / NRS / IEC standards |

---

## Requirements

- **Python 3.11 or newer** — download from [python.org](https://www.python.org/downloads/)
- Windows 10/11 (primary), Linux and macOS supported

---

## Quick Start

### Windows

1. Install Python 3.11+ — tick **"Add Python to PATH"** during installation
2. Clone or download this repository
3. Double-click **`setup.bat`**

That's it. `setup.bat` creates a virtual environment, installs all dependencies,
and launches the app in one step.

**After the first setup**, just double-click **`run.bat`** to start the app.

---

### Linux / macOS

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/engineering-suite.git
cd engineering-suite

# First-time setup (creates venv + installs deps + launches app)
chmod +x setup.sh run.sh
./setup.sh

# Every time after that
./run.sh
```

---

## Manual Setup (any platform)

If you prefer to manage the environment yourself:

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate it
#    Windows:
.venv\Scripts\activate
#    Linux / macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python main.py
```

---

## Dependencies

All dependencies are listed in `requirements.txt` and installed automatically
by the setup scripts.

| Package | Purpose |
|---|---|
| `PyQt6` | UI framework |
| `qtawesome` | Icons |
| `reportlab` | PDF report generation |
| `python-docx` | Word report generation |
| `Pillow` | Screen capture (Screen Report Builder) |
| `openpyxl` | Excel cable data import |
| `ezdxf` | DXF drawing export (PV Layout) |
| `requests` | Datasheet download |

---

## Folder Structure

```
engineering-suite/
├── main.py                  # Entry point — run this
├── requirements.txt         # Python dependencies
├── setup.bat                # Windows: first-time setup + launch
├── run.bat                  # Windows: launch (after setup)
├── setup.sh                 # Linux/macOS: first-time setup + launch
├── run.sh                   # Linux/macOS: launch (after setup)
│
├── app/                     # Shell: sidebar, header, theme, window
├── calculators/             # One sub-package per calculator tool
│   ├── voltage_drop/
│   ├── cable_ccc/
│   ├── short_circuit/
│   ├── gland_size/
│   ├── pv_combined/         # PV String Sizing + Layout
│   └── screen_report/       # Screen capture & report builder
│
├── datasheet_library/       # Datasheet browser widget + PDF files
├── guides/                  # Engineering reference guides (Markdown)
└── utils/                   # Shared export utilities
```

---

## Screen Report Builder — Session Files

The Screen Report Builder can save sessions as `.srp.json` files so you can
close the app and continue a report later.  These files are excluded from
version control by `.gitignore` — they are personal user data.

---

## License

Internal — Solareff Engineering.  All rights reserved.
