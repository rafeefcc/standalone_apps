# 🎞️ Simple File‑Server with ZIP‑download

A lightweight HTTP server written in **Python 3** that

* serves a directory of files (videos, images, documents, …) with a modern,
  responsive UI,
* lets the user select multiple files,
* streams a **ZIP** archive containing the selected files without creating any
  temporary files on disk,
* supports video preview directly in the browser,
* works on Windows, macOS and Linux.

---

## Table of Contents
1. [Features](#features)  
2. [Prerequisites](#prerequisites)  
3. [Installation](#installation)  
4. [Configuration](#configuration)  
5. [Running the server](#running-the-server)  
6. [How it works](#how-it-works)  
7. [Troubleshooting](#troubleshooting)  
8. [License](#license)  

---

## Features
- **Zero‑dependency** – only the Python standard library is used.
- Modern UI (grid view, icons, breadcrumbs, video modal, progress bar).
- Selection bar appears only when files are selected.
- ZIP creation is performed **entirely in memory**, so no large temporary files.
- Built‑in safety check – the server will never serve files outside of the
  configured `SERVE_DIRECTORY`.
- Works behind a firewall / LAN; can be accessed from other devices on the same network.

---

## Prerequisites
- **Python 3.8+** (the script uses `SimpleHTTPRequestHandler` and `socketserver` from the std‑lib).
- No external packages are required.

---

## Installation

```bash
# 1️⃣  Clone the repository (or just copy the files)
git clone https://github.com/your‑username/file‑server‑zip.git
cd file-server-zip

# 2️⃣  (Optional) Create a virtual environment – not required but tidy
python -m venv .venv
# Activate it
#   Windows: .venv\Scripts\activate
#   macOS/Linux: source .venv/bin/activate

# 3️⃣  Nothing else to install – all dependencies are in the std‑lib.
