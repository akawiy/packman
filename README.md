# 🗂 Packman

**Packman (Packing Manager)** is a tool for packing files and folders of any size into a single `.pkd` archive

- 🌍 **Cross-platform:** works on Windows, Linux, and macOS
- 🕘 **Preserves timestamps:** stores creation and modification dates and restores them during unpacking (platform-dependent)
- 🛡 **Integrity-first:** validates .pkd files to detect corruption at any stage (including automatic checks after packing and before unpacking)
- ⚡ **Memory-efficient:** processes files in chunks instead of loading everything into RAM

## 📄 Format

### Header

Each archive starts with metadata:

- **Magic** (`PKMN`, format identifier) — 4 bytes
- **Version** — 1 byte
  - `0x02`: v1.2.0

### Content

Each file or folder is stored as an entry:

- **Item type** — 1 byte
  - `0x00`: file
  - `0x01`: folder
- **Item name size (N)** — 1 byte
- **Item name** — N bytes
- **Creation date and time** (Unix timestamp in seconds) — 8 bytes
- **Modification date and time** (Unix timestamp in seconds) — 8 bytes
- _If item is a file:_
  - **Content size (M)** — 8 bytes
  - **Content** — M bytes
- _If item is a folder:_
  - **Number of items inside** — 4 bytes
- **Checksum** (SHA-256 hash of all the bytes above, used to detect corruption of each entry) — 32 bytes

## 🔨 Build

### 1. Install Python

Download and install Python 3.12+ from [python.org/downloads](https://python.org/downloads)

### 2. Create virtual environment (optional)

Create a virtual environment to isolate the project's dependencies:

```bash
python -m venv venv
```

Then activate it:

**Windows:**

```bash
venv\Scripts\activate
```

**Linux / macOS:**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run from source

```bash
python main.py <command>
```

You can find the list of available commands in the **Usage** section below

### 5. Build executable (optional, recommended for better usability)

If you want a standalone binary:

```bash
pip install pyinstaller
pyinstaller -i "NONE" --onefile main.py --name packman
```

Output will be located in the `dist` directory

## 📋 Usage

Once you have `packman` / `packman.exe`, you can use the following commands:

### 📦 Packing

Pack a file or folder:

```bash
packman pack <input path>
```

Optionally specify an output path:

```bash
packman pack <input path> -o <output path>
```

Output must end with `.pkd`; by default, the file is created in current directory with the same name as input

### 📂 Unpacking

```bash
packman unpack <input path>
```

Optionally specify an output path:

```bash
packman unpack <input path> -o <output path>
```

**⚠️ If the output path already exists, files may be overwritten permanently!**

### ✅ Validating

Check archive integrity without unpacking:

```bash
packman validate <input path>
```

- Verifies checksums
- Validates file tree structure

### ℹ️ Version info

```bash
packman version
```

Displays the current version and release date

## 📌 Notes

- While modification timestamp is always preserved, creation timestamp support depends on the operating system:
  - **Windows:** tested, supported
  - **Linux and MacOS:** not tested, partially supported
- Archive validation is strict — even a **single byte** change will **invalidate** the archive. Recovery may be possible, but the program doesn't support it.
- Despite providing a working solution with no intention to corrupt your data, project author does not guarantee the integrity of your files after using the program. **Use at your own risk!**

**Not vibecoded, made by Vladimir Polischuk**
