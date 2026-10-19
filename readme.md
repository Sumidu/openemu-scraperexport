# OpenEmu Cover Art Exporter

🎮 **Extract and organize cover art from OpenEmu with advanced resizing and format options**

A Python utility that exports cover art from OpenEmu's database and organizes it into console-specific folders with proper ROM-based filenames. Perfect for building custom game libraries, web frontends, or mobile collections.

## ✨ Features

- 📁 **Organized Export** - Automatically creates folders by gaming system
- 🏷️ **Smart Naming** - Files named after ROM titles (no more UUIDs!)
- 🖼️ **Format Options** - Export as PNG (lossless) or JPEG (smaller files)
- 📏 **Advanced Resizing** - Resize with aspect ratio preservation
- 🔧 **High Quality** - Multiple resampling algorithms for best results
- ⚡ **Batch Processing** - Process entire collection at once
- 🛡️ **Safe Operation** - Read-only access to OpenEmu database

## 📋 Requirements

- **macOS** with OpenEmu installed
- **Python 3.6+** (pre-installed on macOS)
- **Pillow** for image processing (optional but recommended)

## 🚀 Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Sumidu/openemu-scraperexport.git
cd openemu-scraperexport
```

2. **Install Pillow for image resizing (recommended):**
```bash
pip install Pillow
```

3. **Make sure OpenEmu has cover art:**
   - Open OpenEmu
   - Import your ROMs
   - Right-click games → "Download Cover Art"

## 🎯 Quick Start

```bash
# Export original cover art as PNG
python3 openemu_exporter.py

# Export resized to 256px width
python3 openemu_exporter.py --width 256

# Export as JPEG with custom quality
python3 openemu_exporter.py --width 256 --format jpg --quality 90

# Export games imported in the last 24 hours
python3 openemu-exporter.py --since 24h
```

## 📖 Usage Examples

### Basic Export
```bash
# Export all cover art maintaining original size and format
python3 openemu_exporter.py
```

### Resize Options
```bash
# Resize to 256px width, keep aspect ratio
python3 openemu_exporter.py --width 256

# Resize to exact 256x256 (may stretch)
python3 openemu_exporter.py --width 256 --height 256 --no-aspect-ratio

# Resize to 512px width with high quality
python3 openemu_exporter.py --width 512 --quality 98 --resample bicubic
```

### Format Options
```bash
# Export as optimized PNG files
python3 openemu_exporter.py --format png --png-optimize

# Export as JPEG with 85% quality
python3 openemu_exporter.py --format jpg --quality 85

# Convert to JPEG without resizing
python3 openemu_exporter.py --format jpg
```

### Date Filter
```bash
# Export games imported in the last 24 hours
python3 openemu-exporter.py --since 24h
```

`--since` accepts a positive duration in seconds (`s`), minutes (`m`), hours (`h`), or days (`d`), such as `30m`, `24h`, or `7d`. Filtering uses OpenEmu's **game import date** (`ZGAME.ZIMPORTDATE`), not an individual ROM's add date; ROMs linked to the same game share the game's date.

### Advanced Examples
```bash
# Perfect for web galleries: 256px JPEG
python3 openemu_exporter.py --width 256 --format jpg --quality 90

# High-quality archive: optimized PNG
python3 openemu_exporter.py --width 512 --format png --png-optimize

# Mobile-friendly: small JPEG files
python3 openemu_exporter.py --width 128 --format jpg --quality 80
```

## ⚙️ Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--width WIDTH` | Target width in pixels | Original |
| `--height HEIGHT` | Target height in pixels | Original |
| `--keep-aspect-ratio` | Maintain aspect ratio when resizing | `True` |
| `--no-aspect-ratio` | Stretch to fit exact dimensions | `False` |
| `--format {png,jpg,jpeg}` | Output image format | `png` |
| `--quality 1-100` | JPEG quality percentage | `95` |
| `--png-optimize` | Optimize PNG files for smaller size | `False` |
| `--resample {lanczos,bicubic,bilinear,nearest}` | Resampling algorithm | `lanczos` |
| `--since DURATION` | Export games imported within a relative window, e.g. `24h` | All dates |
| `--help` | Show help message | - |

## 📁 Output Structure

The script creates an organized folder structure in your home directory:

```
~/openemu_export/
├── Game Boy Advance/
│   ├── Legend of Zelda, The - A Link to the Past.png
│   ├── Metroid - Fusion.png
│   └── Pokemon - Emerald Version.png
├── Super Nintendo/
│   ├── Super Metroid.png
│   ├── F-Zero.png
│   └── Legend of Zelda, The - A Link to the Past.png
└── Nintendo - Nintendo Entertainment System/
    ├── Super Mario Bros.png
    ├── Legend of Zelda, The.png
    └── Metroid.png
```

## 💡 Format Comparison

| Format | Pros | Cons | Best For |
|--------|------|------|----------|
| **PNG** | Lossless quality, transparency support | Larger files | Archival, transparency needed |
| **JPEG** | Small files, adjustable quality | Lossy compression, no transparency | Web, mobile, storage-limited |

## 🔧 Technical Details

### Database Access
- Reads from OpenEmu's SQLite database: `~/Library/Application Support/OpenEmu/Game Library/Library.storedata`
- Maps ROM files to cover art via game relationships
- Handles URL-encoded file paths correctly

### Image Processing
- Uses Pillow for high-quality image operations
- Supports transparency preservation (PNG) or conversion (JPEG)
- Multiple resampling algorithms for optimal quality
- Smart aspect ratio handling

### Safety
- **Read-only** database access - never modifies OpenEmu data
- Graceful error handling for missing files
- Fallback to original files if processing fails

## 🐛 Troubleshooting

### "No ROM cover art mappings found"
- Make sure OpenEmu has downloaded cover art for your games
- Try right-clicking games in OpenEmu → "Download Cover Art"
- Verify OpenEmu has been run at least once

### "Pillow library not found"
```bash
pip install Pillow
# or
pip3 install Pillow
```

### Images appear stretched
- Use `--keep-aspect-ratio` (default) to maintain proportions
- Or specify only width OR height, not both

### Large file sizes
- Use JPEG format: `--format jpg --quality 80`
- Or optimize PNG: `--format png --png-optimize`

## 🤝 Contributing

Contributions are welcome! Please feel free to:

- 🐛 Report bugs
- 💡 Suggest features  
- 🔧 Submit pull requests
- 📖 Improve documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenEmu Team** - For creating an amazing emulation platform
- **Pillow Contributors** - For excellent image processing capabilities
- **Gaming Community** - For preserving gaming history

## 📊 Example Output

```
🎮 OpenEmu Cover Art Exporter
========================================
✅ Pillow library available for image resizing

📂 Database: ~/Library/Application Support/OpenEmu/Game Library/Library.storedata
🖼️  Artwork: ~/Library/Application Support/OpenEmu/Game Library/Artwork  
📤 Export to: ~/openemu_export

🔍 Using corrected query with ZLOCATION...
✅ Found 24 ROM-cover art mappings!

📋 Sample mappings found:
   1. Legend of Zelda, The - A Link to the Past... -> The Legend of Zelda: A Link to the Past & Four Swords (Game Boy Advance)
   2. F-ZERO (U) [!] -> F-Zero (Super Nintendo)
   3. Metroid Fusion -> Metroid: Fusion (Game Boy Advance)

🔧 Resizing images: width=256px (keeping aspect ratio)
   Format: PNG, Resampling: lanczos

📁 Created export directory: ~/openemu_export
✅ Game Boy Advance/Legend of Zelda, The - A Link to the Past.png (resized)
✅ Super Nintendo/F-Zero.png (resized)
✅ Game Boy Advance/Metroid Fusion.png (resized)

📊 Export Summary:
   Total ROMs in database: 24
   Successfully copied: 24
   Images resized: 24
   Missing cover art: 0
   Systems processed: 3
   Export location: ~/openemu_export

🎮 Systems found:
   - Game Boy Advance: 12 files
   - Super Nintendo: 8 files  
   - Nintendo - Nintendo Entertainment System: 4 files

✨ Export completed successfully!
```

---

**Made with ❤️ for the retro gaming community**