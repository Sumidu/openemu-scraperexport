#!/usr/bin/env python3
"""
OpenEmu Cover Art Exporter

This script exports cover art from OpenEmu's database and organizes it into 
folders by console, with files named after their corresponding ROM files.

Features:
- Extract cover art from OpenEmu's database 
- Organize by console/system folders
- Rename files to match ROM names
- Optional image resizing with aspect ratio preservation
- High-quality resampling algorithms

Requirements:
- Python 3.6+
- Pillow (for image resizing): pip install Pillow

Usage Examples:
  python3 openemu_exporter.py                           # Export original size as PNG
  python3 openemu_exporter.py --width 256               # Resize to 256px width
  python3 openemu_exporter.py --width 256 --height 256  # Resize to 256x256
  python3 openemu_exporter.py --width 512 --no-aspect-ratio # Stretch to width
  python3 openemu_exporter.py --format jpg --quality 90 # Export as JPEG
  python3 openemu_exporter.py --format png --png-optimize # Optimized PNG
"""

import sqlite3
import os
import shutil
import urllib.parse
import argparse
from pathlib import Path
import sys
from typing import List, Tuple, Optional

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Export and organize OpenEmu cover art",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 openemu_exporter.py                           # Export original size as PNG
  python3 openemu_exporter.py --width 256               # Resize to 256px width, keep aspect ratio
  python3 openemu_exporter.py --width 256 --height 256  # Resize to 256x256 (may stretch)
  python3 openemu_exporter.py --width 512 --no-aspect-ratio # Resize width, stretch height
  python3 openemu_exporter.py --format jpg --quality 90 # Export as JPEG with 90% quality
  python3 openemu_exporter.py --format png --png-optimize # Export optimized PNG files
  python3 openemu_exporter.py --width 256 --format jpg  # Resize and convert to JPEG
        """
    )
    
    parser.add_argument('--width', type=int, help='Target width in pixels')
    parser.add_argument('--height', type=int, help='Target height in pixels') 
    parser.add_argument('--keep-aspect-ratio', action='store_true', default=True,
                       help='Keep aspect ratio when resizing (default: True)')
    parser.add_argument('--no-aspect-ratio', action='store_true',
                       help='Do not keep aspect ratio (stretch to fit dimensions)')
    parser.add_argument('--quality', type=int, default=95, choices=range(1, 101),
                       help='JPEG quality for resized images (1-100, default: 95)')
    parser.add_argument('--resample', choices=['lanczos', 'bicubic', 'bilinear', 'nearest'],
                       default='lanczos', help='Resampling algorithm (default: lanczos)')
    parser.add_argument('--format', choices=['png', 'jpg', 'jpeg'], default='png',
                       help='Output image format (default: png)')
    parser.add_argument('--png-optimize', action='store_true',
                       help='Optimize PNG files for smaller size (slower but smaller files)')
    
    args = parser.parse_args()
    
    # Handle conflicting aspect ratio flags
    if args.no_aspect_ratio:
        args.keep_aspect_ratio = False
    
    # Validate arguments
    if (args.width or args.height) and not PIL_AVAILABLE:
        parser.error("Image resizing requires the Pillow library. Install with: pip install Pillow")
    
    if args.height and not args.width and args.keep_aspect_ratio:
        parser.error("When using --height with --keep-aspect-ratio, you must also specify --width")
    
    return args

def resize_image(source_path: Path, dest_path: Path, width: Optional[int] = None, 
                height: Optional[int] = None, keep_aspect_ratio: bool = True,
                quality: int = 95, resample_method: str = 'lanczos', 
                output_format: str = 'png', png_optimize: bool = False) -> bool:
    """
    Resize an image and save it to the destination path.
    
    Args:
        source_path: Source image file path
        dest_path: Destination image file path
        width: Target width in pixels
        height: Target height in pixels
        keep_aspect_ratio: Whether to maintain aspect ratio
        quality: JPEG quality (1-100)
        resample_method: Resampling algorithm
        output_format: Output format ('png', 'jpg', 'jpeg')
        png_optimize: Optimize PNG files for size
        
    Returns:
        True if successful, False otherwise
    """
    if not PIL_AVAILABLE:
        # Fallback to simple copy if PIL not available
        shutil.copy2(source_path, dest_path)
        return True
    
    try:
        # Map resample method names to PIL constants
        resample_map = {
            'lanczos': Image.Resampling.LANCZOS,
            'bicubic': Image.Resampling.BICUBIC, 
            'bilinear': Image.Resampling.BILINEAR,
            'nearest': Image.Resampling.NEAREST
        }
        resample = resample_map.get(resample_method, Image.Resampling.LANCZOS)
        
        with Image.open(source_path) as img:
            # Handle image mode based on output format
            if output_format.lower() == 'png':
                # PNG supports transparency, so preserve it if present
                if img.mode in ('RGBA', 'LA'):
                    # Keep transparency for PNG
                    pass
                elif img.mode == 'P':
                    # Convert palette to RGBA to preserve transparency
                    img = img.convert('RGBA')
                elif img.mode not in ('RGB', 'RGBA'):
                    # Convert other modes to RGB
                    img = img.convert('RGB')
            else:
                # JPEG doesn't support transparency, convert to RGB
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        background.paste(img, mask=img.split()[-1])
                        img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
            
            original_width, original_height = img.size
            
            # Calculate new dimensions
            if width and height:
                if keep_aspect_ratio:
                    # Fit within the specified dimensions while keeping aspect ratio
                    img.thumbnail((width, height), resample)
                    new_width, new_height = img.size
                else:
                    # Stretch to exact dimensions
                    new_width, new_height = width, height
                    img = img.resize((new_width, new_height), resample)
            elif width:
                # Scale based on width, maintaining aspect ratio
                if keep_aspect_ratio:
                    ratio = width / original_width
                    new_height = int(original_height * ratio)
                    new_width = width
                else:
                    new_width = width
                    new_height = original_height
                img = img.resize((new_width, new_height), resample)
            elif height:
                # Scale based on height, maintaining aspect ratio
                if keep_aspect_ratio:
                    ratio = height / original_height
                    new_width = int(original_width * ratio)
                    new_height = height
                else:
                    new_width = original_width
                    new_height = height
                img = img.resize((new_width, new_height), resample)
            
            # Save with appropriate format and settings
            save_kwargs = {}
            if output_format.lower() == 'png':
                save_kwargs['optimize'] = png_optimize
                if png_optimize:
                    save_kwargs['compress_level'] = 9  # Maximum compression
            else:  # JPEG
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            
            img.save(dest_path, **save_kwargs)
            return True
            
    except Exception as e:
        print(f"❌ Error resizing image {source_path}: {e}")
        # Fallback to simple copy
        try:
            shutil.copy2(source_path, dest_path)
            return True
        except Exception:
            return False
    """Get the paths to OpenEmu's database and artwork folder."""
    home = Path.home()
    openemu_path = home / "Library" / "Application Support" / "OpenEmu" / "Game Library"
    
    database_path = openemu_path / "Library.storedata"
    artwork_path = openemu_path / "Artwork"
    export_path = home / "openemu_export"
    
    return database_path, artwork_path, export_path

def connect_to_database(db_path: Path) -> Optional[sqlite3.Connection]:
    """Connect to the OpenEmu SQLite database."""
    try:
        if not db_path.exists():
            print(f"❌ Database not found at: {db_path}")
            return None
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except sqlite3.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

def diagnose_database(conn: sqlite3.Connection) -> None:
    """Diagnose the database to understand its structure and content."""
    print("\n🔍 Database diagnostic:")
    
    # Check basic counts
    tables_to_check = ['ZROM', 'ZGAME', 'ZIMAGE', 'ZSYSTEM']
    for table in tables_to_check:
        try:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} records")
        except sqlite3.Error as e:
            print(f"   {table}: Error - {e}")
    
    # Check key relationships
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM ZROM WHERE ZLOCATION IS NOT NULL")
        roms_with_location = cursor.fetchone()[0]
        print(f"   ROMs with location: {roms_with_location}")
        
        cursor = conn.execute("SELECT COUNT(*) FROM ZGAME WHERE ZBOXIMAGE IS NOT NULL")
        games_with_images = cursor.fetchone()[0]
        print(f"   Games with cover art: {games_with_images}")
        
        # Show sample ROM locations
        cursor = conn.execute("SELECT ZLOCATION FROM ZROM WHERE ZLOCATION IS NOT NULL LIMIT 3")
        locations = cursor.fetchall()
        if locations:
            print(f"   Sample ROM locations:")
            for loc in locations:
                decoded = urllib.parse.unquote(loc[0]) if loc[0] else "None"
                print(f"     - {decoded}")
                
    except sqlite3.Error as e:
        print(f"   Error in diagnostic: {e}")

def get_rom_cover_mappings(conn: sqlite3.Connection) -> List[Tuple[str, str, str, str]]:
    """
    Get mappings of ROM files to their cover art UUIDs and system names.
    Returns: List of (rom_filename, cover_uuid, game_title, system_name) tuples
    """
    
    # Use the correct relationship: ZROM.ZGAME -> ZGAME.ZBOXIMAGE -> ZIMAGE.Z_PK
    # And use ZLOCATION instead of ZFILENAME since ZFILENAME is NULL
    query = """
    SELECT 
        r.ZLOCATION as rom_location,
        i.ZRELATIVEPATH as cover_uuid,
        COALESCE(g.ZGAMETITLE, g.ZNAME) as game_title,
        COALESCE(s.ZLASTLOCALIZEDNAME, s.ZSHORTNAME, s.ZSYSTEMIDENTIFIER) as system_name
    FROM ZROM r
    JOIN ZGAME g ON r.ZGAME = g.Z_PK
    JOIN ZIMAGE i ON g.ZBOXIMAGE = i.Z_PK  
    JOIN ZSYSTEM s ON g.ZSYSTEM = s.Z_PK
    WHERE i.ZRELATIVEPATH IS NOT NULL 
    AND i.ZRELATIVEPATH != ''
    AND r.ZLOCATION IS NOT NULL
    ORDER BY s.ZSHORTNAME, g.ZGAMETITLE;
    """
    
    try:
        print(f"🔍 Using corrected query with ZLOCATION...")
        cursor = conn.execute(query)
        results = cursor.fetchall()
        
        if results:
            print(f"✅ Found {len(results)} ROM-cover art mappings!")
            # Process the results to extract filename from location
            processed_results = []
            for row in results:
                rom_location = row['rom_location']
                # Extract filename from URL-encoded path
                rom_filename = extract_filename_from_location(rom_location)
                processed_results.append((
                    rom_filename, 
                    row['cover_uuid'], 
                    row['game_title'], 
                    row['system_name']
                ))
            return processed_results
        else:
            print(f"❌ No results found")
            return []
                
    except sqlite3.Error as e:
        print(f"❌ Database query error: {e}")
        return []

def extract_filename_from_location(location: str) -> str:
    """
    Extract filename from URL-encoded location path.
    Examples:
    - "Game%20Boy%20Advance/Legend%20of%20Zelda,%20The%20..." -> "Legend of Zelda, The ..."
    - "Super%20Nintendo%20(SNES)/f-zero.sfc" -> "f-zero.sfc"
    """
    import urllib.parse
    
    if not location:
        return "Unknown"
    
    try:
        # URL decode the location
        decoded_location = urllib.parse.unquote(location)
        
        # Extract filename (part after last slash)
        if '/' in decoded_location:
            filename = decoded_location.split('/')[-1]
        else:
            filename = decoded_location
        
        # Handle truncated filenames (ending with ...)
        if filename.endswith('...'):
            # Remove the ... for cleaner names
            filename = filename[:-3].strip()
        
        return filename if filename else "Unknown"
        
    except Exception as e:
        print(f"⚠️  Error processing location '{location}': {e}")
        return "Unknown"

def sanitize_filename(filename: str) -> str:
    """Remove or replace characters that aren't safe for filenames."""
    # Replace problematic characters with safe alternatives
    replacements = {
        '/': '-',
        '\\': '-',
        ':': '-',
        '*': '',
        '?': '',
        '"': '',
        '<': '',
        '>': '',
        '|': '-'
    }
    
    for old, new in replacements.items():
        filename = filename.replace(old, new)
    
    return filename.strip()

def get_rom_name_without_extension(rom_filename: str) -> str:
    """Extract ROM name without file extension."""
    if not rom_filename:
        return "Unknown"
    
    # Use pathlib to properly handle the extension removal
    name = Path(rom_filename).stem
    return name if name else rom_filename

def find_cover_art_file(artwork_path: Path, uuid_name: str) -> Optional[Path]:
    """Find the actual cover art file in the artwork folder."""
    # Try with common image extensions
    extensions = ['', '.png', '.jpg', '.jpeg', '.gif', '.tiff', '.bmp', '.webp']
    
    # First try exact match (no extension)
    exact_path = artwork_path / uuid_name
    if exact_path.exists() and exact_path.is_file():
        return exact_path
    
    # Try with extensions
    for ext in extensions[1:]:  # Skip empty extension since we tried exact match
        test_path = artwork_path / f"{uuid_name}{ext}"
        if test_path.exists() and test_path.is_file():
            return test_path
    
    # Try without extension if uuid_name already has one
    if '.' in uuid_name:
        base_name = uuid_name.rsplit('.', 1)[0]
        for ext in extensions:
            test_path = artwork_path / f"{base_name}{ext}"
            if test_path.exists() and test_path.is_file():
                return test_path
    
    return None

def create_export_structure(export_path: Path, mappings: List[Tuple[str, str, str, str]], 
                          artwork_path: Path, args) -> None:
    """Create the export folder structure and copy/resize files."""
    
    # Create main export directory
    export_path.mkdir(exist_ok=True)
    print(f"📁 Created export directory: {export_path}")
    
    # Show resize settings if applicable
    if args.width or args.height:
        resize_info = []
        if args.width:
            resize_info.append(f"width={args.width}px")
        if args.height:
            resize_info.append(f"height={args.height}px")
        aspect_info = "keeping aspect ratio" if args.keep_aspect_ratio else "stretching to fit"
        print(f"🔧 Resizing images: {', '.join(resize_info)} ({aspect_info})")
        if PIL_AVAILABLE:
            format_info = args.format.upper()
            if args.format.lower() == 'png' and args.png_optimize:
                format_info += " (optimized)"
            elif args.format.lower() in ['jpg', 'jpeg']:
                format_info += f" (quality {args.quality}%)"
            print(f"   Format: {format_info}, Resampling: {args.resample}")
        else:
            print("   ⚠️  PIL not available - images will be copied without resizing")
    else:
        print(f"🔧 Output format: {args.format.upper()}")
    
    # Determine file extension based on format
    if args.format.lower() == 'png':
        file_extension = '.png'
    else:  # jpg or jpeg
        file_extension = '.jpg'
    # Track statistics
    total_files = len(mappings)
    copied_files = 0
    resized_files = 0
    missing_files = 0
    systems_processed = set()
    
    for i, (rom_filename, cover_uuid, game_title, system_name) in enumerate(mappings):
        if not cover_uuid or not system_name:
            continue
            
        # Create system folder
        system_folder = export_path / sanitize_filename(system_name)
        system_folder.mkdir(exist_ok=True)
        systems_processed.add(system_name)
        
        # Find the source cover art file
        source_file = find_cover_art_file(artwork_path, cover_uuid)
        if not source_file:
            print(f"⚠️  Missing cover art for {rom_filename} (UUID: {cover_uuid})")
            missing_files += 1
            continue
        
        # Create destination filename
        rom_name = get_rom_name_without_extension(rom_filename)
        safe_rom_name = sanitize_filename(rom_name)
        dest_filename = f"{safe_rom_name}{file_extension}"
        dest_path = system_folder / dest_filename
        
        # Copy/resize the file
        try:
            if args.width or args.height:
                # Resize the image
                success = resize_image(
                    source_file, dest_path,
                    width=args.width,
                    height=args.height, 
                    keep_aspect_ratio=args.keep_aspect_ratio,
                    quality=args.quality,
                    resample_method=args.resample,
                    output_format=args.format,
                    png_optimize=args.png_optimize
                )
                if success:
                    resized_files += 1
                    copied_files += 1
                    print(f"✅ {system_name}/{dest_filename} (resized)")
                else:
                    print(f"❌ Failed to resize {rom_filename}")
                    missing_files += 1
            else:
                # Convert format even if not resizing
                if PIL_AVAILABLE and args.format.lower() != 'png':
                    success = resize_image(
                        source_file, dest_path,
                        output_format=args.format,
                        quality=args.quality,
                        png_optimize=args.png_optimize
                    )
                    if success:
                        copied_files += 1
                        print(f"✅ {system_name}/{dest_filename} (converted)")
                    else:
                        print(f"❌ Failed to convert {rom_filename}")
                        missing_files += 1
                else:
                    # Just copy the original file
                    shutil.copy2(source_file, dest_path)
                    copied_files += 1
                    print(f"✅ {system_name}/{dest_filename}")
                    
        except Exception as e:
            print(f"❌ Failed to process {rom_filename}: {e}")
            missing_files += 1
    
    # Print summary
    print(f"\n📊 Export Summary:")
    print(f"   Total ROMs in database: {total_files}")
    print(f"   Successfully copied: {copied_files}")
    if resized_files > 0:
        print(f"   Images resized: {resized_files}")
    print(f"   Missing cover art: {missing_files}")
    print(f"   Systems processed: {len(systems_processed)}")
    print(f"   Export location: {export_path}")
    
    if systems_processed:
        print(f"\n🎮 Systems found:")
        for system in sorted(systems_processed):
            system_folder = export_path / sanitize_filename(system)
            # Count files with the chosen extension
            file_pattern = f"*{file_extension}"
            file_count = len(list(system_folder.glob(file_pattern)))
            print(f"   - {system}: {file_count} files")

def get_openemu_paths() -> Tuple[Path, Path, Path]:
    """Get the paths to OpenEmu's database and artwork folder."""
    home = Path.home()
    openemu_path = home / "Library" / "Application Support" / "OpenEmu" / "Game Library"
    
    database_path = openemu_path / "Library.storedata"
    artwork_path = openemu_path / "Artwork"
    export_path = home / "openemu_export"
    
    return database_path, artwork_path, export_path

def main():
    """Main function to orchestrate the export process."""
    # Parse command line arguments
    args = parse_arguments()
    
    print("🎮 OpenEmu Cover Art Exporter")
    print("=" * 40)
    
    # Show PIL availability for resizing
    if args.width or args.height:
        if PIL_AVAILABLE:
            print("✅ Pillow library available for image resizing")
        else:
            print("❌ Pillow library not found - install with: pip install Pillow")
            print("   Images will be copied without resizing")
        print()
    
    # Get paths
    db_path, artwork_path, export_path = get_openemu_paths()
    
    # Verify paths exist
    if not db_path.exists():
        print(f"❌ OpenEmu database not found at: {db_path}")
        print("   Make sure OpenEmu is installed and has been run at least once.")
        return
    
    if not artwork_path.exists():
        print(f"❌ Artwork folder not found at: {artwork_path}")
        print("   Make sure you have downloaded some cover art in OpenEmu.")
        return
    
    print(f"📂 Database: {db_path}")
    print(f"🖼️  Artwork: {artwork_path}")
    print(f"📤 Export to: {export_path}")
    print()
    
    # Connect to database
    conn = connect_to_database(db_path)
    if not conn:
        return
    
    try:
        # Get ROM to cover art mappings
        print("🔍 Reading OpenEmu database...")
        mappings = get_rom_cover_mappings(conn)
        
        if not mappings:
            print("❌ No ROM cover art mappings found in database.")
            print("💡 This might mean:")
            print("   - No cover art has been downloaded yet")
            print("   - Cover art exists but relationships are structured differently")
            print("   - ROMs were imported without cover art lookup enabled")
            print("\n🔧 Running diagnostic to understand the database structure...")
            diagnose_database(conn)
            return
        
        print(f"📋 Found {len(mappings)} ROM(s) with cover art")
        
        # Show a few examples
        if mappings:
            print("\n📋 Sample mappings found:")
            for i, (rom_filename, cover_uuid, game_title, system_name) in enumerate(mappings[:5]):
                print(f"   {i+1}. {rom_filename} -> {game_title} ({system_name})")
            if len(mappings) > 5:
                print(f"   ... and {len(mappings) - 5} more")
        print()
        
        # Create export structure and copy files
        print("📁 Creating export structure...")
        create_export_structure(export_path, mappings, artwork_path, args)
        
    finally:
        conn.close()
    
    print(f"\n✨ Export completed successfully!")
    print(f"   Check your export folder: {export_path}")
    
    # Show installation reminder if resizing was requested but PIL unavailable
    if (args.width or args.height) and not PIL_AVAILABLE:
        print(f"\n💡 To enable image resizing, install Pillow:")
        print(f"   pip install Pillow")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Export cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)