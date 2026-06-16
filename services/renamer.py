import os
import re
import shutil
from pathlib import Path

def rename_files(folder_path, prefix='', suffix='', numbering=True, start_num=1, 
                 remove_special=True, include_subdirs=False):
    """
    Rename files in the specified folder with various options.
    
    Args:
        folder_path: Path to folder containing files
        prefix: String to add at beginning of filename
        suffix: String to add before extension
        numbering: Whether to add sequential numbers
        start_num: Starting number if numbering is True
        remove_special: Whether to remove special characters
        include_subdirs: Whether to process subdirectories
    
    Returns:
        dict: Contains renamed_count, errors, and details list
    """
    result = {
        'renamed_count': 0,
        'errors': [],
        'details': []
    }
    
    if not os.path.exists(folder_path):
        result['errors'].append(f"Folder does not exist: {folder_path}")
        return result
    
    # Collect files to rename
    files_to_rename = []
    if include_subdirs:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                files_to_rename.append(os.path.join(root, file))
    else:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                files_to_rename.append(item_path)
    
    # Sort files for consistent numbering
    files_to_rename.sort()
    
    for idx, file_path in enumerate(files_to_rename):
        try:
            directory = os.path.dirname(file_path)
            old_name = os.path.basename(file_path)
            name, ext = os.path.splitext(old_name)
            
            # Create new name based on options
            new_name = name
            
            if remove_special:
                # Remove special characters except spaces, dots, underscores, hyphens
                new_name = re.sub(r'[^\w\s\.\-]', '', new_name)
                new_name = re.sub(r'\s+', '_', new_name)  # Replace spaces with underscores
            
            if prefix:
                new_name = prefix + new_name
            
            if suffix:
                new_name = new_name + suffix
            
            if numbering:
                number = start_num + idx
                new_name = f"{new_name}_{number:03d}"
            
            new_name = new_name + ext
            new_path = os.path.join(directory, new_name)
            
            # Handle duplicate names
            if os.path.exists(new_path) and new_path != file_path:
                base, ext = os.path.splitext(new_name)
                counter = 1
                while os.path.exists(os.path.join(directory, f"{base}_{counter}{ext}")):
                    counter += 1
                new_name = f"{base}_{counter}{ext}"
                new_path = os.path.join(directory, new_name)
            
            # Rename the file
            os.rename(file_path, new_path)
            result['renamed_count'] += 1
            result['details'].append({
                'old': old_name,
                'new': new_name,
                'path': directory,
                'status': 'success'
            })
            
        except Exception as e:
            result['errors'].append(f"Failed to rename {old_name}: {str(e)}")
            result['details'].append({
                'old': old_name,
                'new': None,
                'path': directory,
                'status': 'error',
                'error': str(e)
            })
    
    return result