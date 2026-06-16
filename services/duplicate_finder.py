import os
import hashlib
from collections import defaultdict

def get_file_hash(file_path, chunk_size=8192):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None

def find_duplicates(folder_path, include_subdirs=True):
    """
    Find duplicate files by comparing MD5 hashes.
    
    Args:
        folder_path: Path to folder to scan
        include_subdirs: Whether to scan subdirectories
    
    Returns:
        dict: Contains duplicate_groups, total_duplicates, duplicate_size
    """
    result = {
        'duplicate_groups': [],
        'total_duplicates': 0,
        'duplicate_size': 0,
        'errors': []
    }
    
    if not os.path.exists(folder_path):
        result['errors'].append(f"Folder does not exist: {folder_path}")
        return result
    
    # First group files by size (fast filter)
    size_map = defaultdict(list)
    
    if include_subdirs:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    size_map[size].append(file_path)
                except Exception as e:
                    result['errors'].append(f"Cannot access {file_path}: {str(e)}")
    else:
        for item in os.listdir(folder_path):
            file_path = os.path.join(folder_path, item)
            if os.path.isfile(file_path):
                try:
                    size = os.path.getsize(file_path)
                    size_map[size].append(file_path)
                except Exception as e:
                    result['errors'].append(f"Cannot access {file_path}: {str(e)}")
    
    # Now compare files with same size using hash
    hash_map = defaultdict(list)
    
    for size, files in size_map.items():
        if len(files) < 2:
            continue
        
        for file_path in files:
            file_hash = get_file_hash(file_path)
            if file_hash:
                hash_map[(size, file_hash)].append(file_path)
    
    # Build duplicate groups (groups with 2+ files)
    for (size, file_hash), files in hash_map.items():
        if len(files) > 1:
            # Determine original (first file by modification time or just first)
            files_sorted = sorted(files, key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0)
            original = files_sorted[0]
            duplicates = files_sorted[1:]
            
            result['duplicate_groups'].append({
                'hash': file_hash,
                'size': size,
                'original': original,
                'duplicates': duplicates,
                'duplicate_count': len(duplicates)
            })
            result['total_duplicates'] += len(duplicates)
            result['duplicate_size'] += size * len(duplicates)
    
    return result

def delete_duplicates(duplicate_paths):
    """
    Delete specified duplicate files.
    
    Args:
        duplicate_paths: List of file paths to delete
    
    Returns:
        dict: Contains deleted_count, freed_space, errors
    """
    result = {
        'deleted_count': 0,
        'freed_space': 0,
        'errors': []
    }
    
    for file_path in duplicate_paths:
        try:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                os.remove(file_path)
                result['deleted_count'] += 1
                result['freed_space'] += size
        except Exception as e:
            result['errors'].append(f"Failed to delete {file_path}: {str(e)}")
    
    return result