# 🗂 Packman

**Packman (Packing Manager)** is a console tool for packing files and folders of any size into a single `.pkd` archive

- 🌍 **Cross-platform:** designed to work on Windows, Linux and macOS
- ⚡ **Memory-efficient:** processes big files in chunks instead of loading everything into RAM
- 🔒 **Secure:** has an optional build-in strong encryption with a 256-bit key
- 🛡 **Integrity-first:** can validate packed files to detect corruption at any stage, and does it automatically after packing and before unpacking
- 🔗 **1-to-1 preservation:** stores hidden flag, creation and modification dates and assigns them to each file and folder during unpacking ([platform-dependent](#notes))

## 🔍 Navigation:

- [📄 Format](#format)
  - [#️⃣ Header](#header)
  - [🏷️ Entries](#entries)
- [🔨 Build](#build)
  - [1. Install Python](#install-python)
  - [2. Create virtual environment](#create-virtual-environment)
  - [3. Install dependencies](#install-dependencies)
  - [4. Run from source](#run-from-source)
  - [5. Build executable](#build-executable)
- [📋 Usage](#usage)
  - [📦 Pack](#pack)
  - [📂 Unpack](#unpack)
  - [✅ Validate](#validate)
  - [ℹ️ Version info](#version-info)
- [📌 Notes](#notes)

<a name="format"></a>
## 📄 Format

<a name="header"></a>
### #️⃣ Header

Each archive starts with metadata:

- **Format identifier** (`.PKD`) — 4 bytes
- **Version and flags** — 1 byte
  - **Version** — 7 bits
    - `0`: v1.0.0 (never appears)
    - `1`: v1.1.0 (never appears)
    - `2`: v1.2.0
    - `3`: v1.3.0
  - **Is-encrypted flag** — 1 bit

<a name="entries"></a>
### 🏷️ Entries

Each file or folder is stored as an entry:

- **Type and flags** — 1 byte
  - **Type** — 7 bits
    - `0`: file
    - `1`: folder
  - **Is-hidden flag** — 1 bit
- **Name size (N)** — 1 byte
- **Name** — N bytes
- **Creation date and time** (Unix timestamp in seconds) — 8 bytes
- **Modification date and time** (Unix timestamp in seconds) — 8 bytes
- _If file:_
  - **Content size (M)** — 8 bytes
  - **Content** — M bytes
- _If folder:_
  - **Number of items inside** — 4 bytes
- **Checksum** (SHA-256 hash of all the bytes above, used to detect corruption of each entry individually) — 32 bytes

🔒 During encryption header is never touched, only entries are affected

<a name="build"></a>
## 🔨 Build

If you aren't planning to modify the program, you can download the compiled executable for **Windows** from the [Releases](https://github.com/akawiy/packman/releases) tab (or click [here](https://github.com/akawiy/packman/releases/download/latest/packman.exe) to download the latest `packman.exe` right away)

<a name="install-python"></a>
### 1. Install Python

Download and install Python 3.12+ from [python.org/downloads](https://python.org/downloads)

<a name="create-virtual-environment"></a>
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

<a name="install-dependencies"></a>
### 3. Install dependencies

```bash
pip install -r requirements.txt
```

<a name="run-from-source"></a>
### 4. Run from source

```bash
python main.py <command>
```

You can find the list of available commands in the **Usage** section below

<a name="build-executable"></a>
### 5. Build executable (optional, recommended for better usability)

If you want a standalone binary:

```bash
pip install pyinstaller
pyinstaller -i "NONE" --onefile main.py --name packman
```

Output will be located in the `dist` folder

<a name="usage"></a>
## 📋 Usage

Once you have `packman` / `packman.exe`, you can use the following commands:

<a name="pack"></a>
### 📦 Pack

```bash
packman pack <input path> [-o <output path>] [-k <encryption key>]
```

Argument descriptions:

- **Input path** — absolute or relative path to the file or folder you want to pack
- **Output path** _(optional)_ — absolute or relative path to the output file (name included, must end with .pkd); by default, the file is created in the current directory with the same name as input
- **Encryption key** _(optional)_ — either value or path to `.key` file; the key must be represented as 64-digit hexadecimal, a file where the key is saved directly in bytes will be rejected

<a name="unpack"></a>
### 📂 Unpack

```bash
packman unpack <input path> [-o <output path>] [-k <decryption key>]
```

Argument descriptions:

- **Input path** — absolute or relative path to the file you want to upack (must end with `.pkd`)
- **Output path** _(optional)_ — absolute or relative path to the output file or folder (name included); by default, the file is created in the current directory with the same name as input
- **Decryption key** _(required for encrypted archives only)_ — either value or path to `.key` file; the key must be represented as 64-digit hexadecimal, a file where the key is saved directly in bytes will be rejected

**⚠️ If the output path already exists, some of your files inside may be permanently overwritten!**

<a name="validate"></a>
### ✅ Validate

Check archive integrity without unpacking
- Verifies checksums
- Validates file tree structure

```bash
packman validate <input path> [-k <decryption key>]
```

Argument descriptions:

- **Input path** — absolute or relative path to the file you want to upack (must end with `.pkd`)
- **Decryption key** _(required for encrypted archives only)_ — either value or path to `.key` file; the key must be represented as 64-digit hexadecimal, a file where the key is saved directly in bytes will be rejected

<a name="version-info"></a>
### ℹ️ Version info

Displays the current version and release date

```bash
packman version
```

<a name="notes"></a>
## 📌 Notes

- While Packman supports modification timestamp on all operating systems, creation timestamp preservation is partially supported on Linux and macOS, while assigning is unsupported entirely due to OS limitations.
- Hidden items packed on Windows or macOS and unpacked on Linux won't be hidden unless their name starts with a dot. Similarly, if item's name starts with a dot, it will appear hidden on Linux and macOS in any case, even if it wasn't hidden on Windows. That's because Windows stores hidden flag as an internal attribute, Linux considers item hidden if its name starts with a dot, and macOS considers item hidden in both of these scenarios.
- Archive validation is strict — even a **single byte change** will **invalidate** the archive. Recovery may be possible, but the program doesn't support it.
- Despite providing a working solution with no intention to corrupt your data, project author does not guarantee the integrity of your files after using the program. **Use at your own risk!**

**Not vibecoded, made by Vladimir Polischuk**
