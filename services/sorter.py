import os
import shutil
from pathlib import Path

# Define file category mappings
CATEGORIES = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico'],
    'Documents': ['.pdf', '.docx', '.doc', '.txt', '.md', '.rtf', '.odt', '.xlsx', '.xls', '.pptx', '.ppt'],
    'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'],
    'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
    'Programs': ['.py', '.js', '.html', '.css', '.java', '.c', '.cpp', '.exe', '.msi', '.sh', '.bat'],
    'Others': []  # Default category for unmatched extensions
}

def sort_files(folder_path, include_subdirs=False):
    """
    Sort files into category folders based on extensions.
    
    Args:
        folder_path: Path to folder containing files
        include_subdirs: Whether to process files in subdirectories
    
    Returns:
        dict: Contains sorted_count, errors, and category_stats
    """
    result = {
        'sorted_count': 0,
        'errors': [],
        'category_stats': {},
        'details': []
    }
    
    if not os.path.exists(folder_path):
        result['errors'].append(f"Folder does not exist: {folder_path}")
        return result
    
    # Initialize category stats
    for category in CATEGORIES.keys():
        result['category_stats'][category] = 0
    
    # Collect files to sort
    files_to_sort = []
    if include_subdirs:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                files_to_sort.append(os.path.join(root, file))
    else:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                files_to_sort.append(item_path)
    
    for file_path in files_to_sort:
        try:
            # Get file extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Find category for this extension
            category = 'Others'
            for cat, extensions in CATEGORIES.items():
                if ext in extensions:
                    category = cat
                    break
            
            # Create category folder if it doesn't exist
            category_path = os.path.join(folder_path, category)
            if not os.path.exists(category_path):
                os.makedirs(category_path)
            
            # Move file to category folder
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(category_path, file_name)
            
            # Handle duplicate filenames
            if os.path.exists(dest_path):
                base, ext_part = os.path.splitext(file_name)
                counter = 1
                while os.path.exists(os.path.join(category_path, f"{base}_{counter}{ext_part}")):
                    counter += 1
                dest_path = os.path.join(category_path, f"{base}_{counter}{ext_part}")
            
            shutil.move(file_path, dest_path)
            result['sorted_count'] += 1
            result['category_stats'][category] += 1
            result['details'].append({
                'file': file_name,
                'category': category,
                'status': 'success'
            })
            
        except Exception as e:
            result['errors'].append(f"Failed to sort {os.path.basename(file_path)}: {str(e)}")
            result['details'].append({
                'file': os.path.basename(file_path),
                'category': None,
                'status': 'error',
                'error': str(e)
            })
    
    return result