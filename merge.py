import os
import shutil
import hashlib
from pathlib import Path

SOURCE_DIRS = [
    "~/nucleihub-templates",
    "./community-templates"
]
MASTER_DIR = "~/master_nuclei"
CHUNK_SIZE = 2500
VALID_EXT = {".yaml", ".yml"}

def expand(path):
    return Path(path).expanduser().resolve()

def get_file_hash(filepath):
    """Calculate SHA-512 hash of filename + content to detect duplicates."""
    hash_sha512 = hashlib.sha512()
    
    # Include filename and extension in hash
    hash_sha512.update(filepath.name.encode('utf-8'))
    
    # Include file content in hash
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha512.update(chunk)
    
    return hash_sha512.hexdigest()

def gather_files(source_dirs):
    """Collect all template files recursively."""
    files = []
    for base in source_dirs:
        base_path = expand(base)
        if not base_path.exists():
            print(f"⚠️  Warning: Directory not found: {base_path}")
            continue
        
        print(f"📂 Scanning: {base_path}")
        for root, dirs, filenames in os.walk(base_path):
            for f in filenames:
                p = Path(root) / f
                if p.suffix.lower() in VALID_EXT:
                    files.append(p)
    
    print(f"✓ Found {len(files)} YAML/YML files")
    return files

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def move_files_to_master(files, master_dir):
    """Move files to a flat master directory, avoiding duplicates."""
    master_dir = expand(master_dir)
    ensure_dir(master_dir)
    
    # Track file hashes to detect duplicates
    seen_hashes = {}
    moved = 0
    skipped = 0
    
    for f in files:
        f = f.resolve()
        
        # Calculate hash to detect duplicate content
        try:
            file_hash = get_file_hash(f)
        except Exception as e:
            print(f"❌ Error reading {f.name}: {e}")
            continue
        
        # Skip if we've already seen this exact content
        if file_hash in seen_hashes:
            print(f"⏭️  Skipping duplicate: {f.name} (same as {seen_hashes[file_hash]})")
            skipped += 1
            continue
        
        # Find unique filename
        target = master_dir / f.name
        counter = 1
        while target.exists():
            target = master_dir / f"{f.stem}_{counter}{f.suffix}"
            counter += 1
        
        # Move file
        try:
            shutil.move(str(f), target)
            seen_hashes[file_hash] = target.name
            moved += 1
            if moved % 100 == 0:
                print(f"  Moved {moved} files...")
        except Exception as e:
            print(f"❌ Error moving {f.name}: {e}")
    
    print(f"\n✓ Moved {moved} files to {master_dir}")
    print(f"⏭️  Skipped {skipped} duplicates")
    return moved

def chunk_master_directory(master_dir, chunk_size):
    """Split master directory into chunks by moving files."""
    master = expand(master_dir)
    all_files = sorted([p for p in master.iterdir() if p.is_file()])
    total = len(all_files)
    
    if total == 0:
        print("⚠️  No files found in master directory to chunk")
        return
    
    print(f"\n📦 Moving files into chunks of {chunk_size} each...")
    chunk_index = 1
    
    for i in range(0, total, chunk_size):
        chunk_dir = master / f"chunk_{chunk_index}"
        ensure_dir(chunk_dir)
        
        chunk_files = all_files[i:i + chunk_size]
        for f in chunk_files:
            shutil.move(str(f), chunk_dir / f.name)
        
        print(f"  ✓ Chunk {chunk_index}: {len(chunk_files)} files moved")
        chunk_index += 1
    
    print(f"\n✓ Created {chunk_index - 1} chunks in {master}")
    print(f"   All files moved from root into chunk subdirectories")

if __name__ == "__main__":
    print("=" * 60)
    print("Nuclei Template Organizer")
    print("=" * 60)
    
    # Gather all files first (convert generator to list)
    files = gather_files(SOURCE_DIRS)
    
    if not files:
        print("\n❌ No YAML/YML files found in source directories!")
        print("   Please check that the directories exist and contain files.")
        exit(1)
    
    # Move files to master directory
    moved_count = move_files_to_master(files, MASTER_DIR)
    
    if moved_count > 0:
        # Create chunks
        chunk_master_directory(MASTER_DIR, CHUNK_SIZE)
        print("\n" + "=" * 60)
        print("✓ Complete!")
        print("=" * 60)
    else:
        print("\n❌ No files were moved. Please check permissions and paths.")
