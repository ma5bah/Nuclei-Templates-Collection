import os
import shutil
from pathlib import Path

SOURCE_DIRS = [
    "~/nuclei-templates",
    "~/nucleihub-templates",
    "./community-templates"
]

MASTER_DIR = "~/master_nuclei"
CHUNK_SIZE = 100
VALID_EXT = {".yaml", ".yml"}


def expand(path):
    return Path(path).expanduser().resolve()


def gather_files(source_dirs):
    """Yield template files recursively."""
    for base in source_dirs:
        base_path = expand(base)
        for root, dirs, files in os.walk(base_path):
            for f in files:
                p = Path(root) / f
                if p.suffix.lower() in VALID_EXT:
                    yield p


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def move_files_to_master(files, master_dir):
    """Move files to a flat master directory."""
    master_dir = expand(master_dir)
    ensure_dir(master_dir)

    for f in files:
        f = f.resolve()

        target = master_dir / f.name
        counter = 1
        while target.exists():
            target = master_dir / f"{f.stem}_{counter}{f.suffix}"
            counter += 1

        shutil.move(str(f), target)


def chunk_master_directory(master_dir, chunk_size):
    master = expand(master_dir)

    all_files = sorted([p for p in master.iterdir() if p.is_file()])
    total = len(all_files)

    chunk_index = 1
    for i in range(0, total, chunk_size):
        chunk_dir = master / f"chunk_{chunk_index}"
        ensure_dir(chunk_dir)

        for f in all_files[i:i + chunk_size]:
            shutil.move(str(f), chunk_dir / f.name)

        chunk_index += 1


def main():
    files = gather_files(SOURCE_DIRS)
    move_files_to_master(files, MASTER_DIR)
    chunk_master_directory(MASTER_DIR, CHUNK_SIZE)


if __name__ == "__main__":
    main()
