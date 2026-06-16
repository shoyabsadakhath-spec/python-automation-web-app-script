import os
import glob
from pathlib import Path

# Default temporary file patterns
DEFAULT_PATTERNS = ['*.tmp', '*.temp', '*.log', '*.cache', '*.swp', '*.bak', '*.~*']

def find_temp_files(folder_path, patterns=None, include_subdirs=True):
    """
    Find temporary files matching patterns.
    
    Args:
        folder_path: Path to scan
        patterns: List of glob patterns (e.g., ['*.tmp', '*.log'])
        include_subdirs: Whether to scan subdirectories
    
    Returns:
        dict: Contains files list with paths and sizes
    """
    if patterns is None:
        patterns = DEFAULT_PATTERNS
    
    result = {
        'files': [],
        'total_size': 0,
        'errors': []
    }
    
    if not os.path.exists(folder_path):
        result['errors'].append(f"Folder does not exist: {folder_path}")
        return result
    
    try:
        if include_subdirs:
            for pattern in patterns:
                # Recursive glob
                for file_path in glob.glob(os.path.join(folder_path, '**', pattern), recursive=True):
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        result['files'].append({
                            'path': file_path,
                            'name': os.path.basename(file_path),
                            'size': size,
                            'size_mb': round(size / (1024 * 1024), 2)
                        })
                        result['total_size'] += size
        else:
            for pattern in patterns:
                for file_path in glob.glob(os.path.join(folder_path, pattern)):
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        result['files'].append({
                            'path': file_path,
                            'name': os.path.basename(file_path),
                            'size': size,
                            'size_mb': round(size / (1024 * 1024), 2)
                        })
                        result['total_size'] += size
    except Exception as e:
        result['errors'].append(f"Error scanning files: {str(e)}")
    
    return result

def delete_files(file_paths):
    """
    Delete specified files.
    
    Args:
        file_paths: List of file paths to delete
    
    Returns:
        dict: Contains deleted_count, freed_space, errors
    """
    result = {
        'deleted_count': 0,
        'freed_space': 0,
        'errors': []
    }
    
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                os.remove(file_path)
                result['deleted_count'] += 1
                result['freed_space'] += size
        except Exception as e:
            result['errors'].append(f"Failed to delete {file_path}: {str(e)}")
    
    return result

def clean_temp_files(folder_path, patterns=None, include_subdirs=True):
    """
    Find and delete temporary files in one operation.
    
    Returns:
        dict: Contains deleted_count, freed_space, errors
    """
    find_result = find_temp_files(folder_path, patterns, include_subdirs)
    
    if find_result['errors']:
        return {
            'deleted_count': 0,
            'freed_space': 0,
            'errors': find_result['errors']
        }
    
    file_paths = [f['path'] for f in find_result['files']]
    return delete_files(file_paths)