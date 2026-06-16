import os
from collections import defaultdict
from pathlib import Path

def analyze_folder(folder_path, include_subdirs=True):
    """
    Analyze folder structure and generate statistics.
    
    Args:
        folder_path: Path to analyze
        include_subdirs: Whether to include subdirectories
    
    Returns:
        dict: Contains detailed statistics
    """
    result = {
        'total_files': 0,
        'total_folders': 0,
        'total_size': 0,
        'total_size_mb': 0,
        'total_size_gb': 0,
        'largest_files': [],
        'extension_distribution': defaultdict(int),
        'extension_sizes': defaultdict(int),
        'errors': []
    }
    
    if not os.path.exists(folder_path):
        result['errors'].append(f"Folder does not exist: {folder_path}")
        return result
    
    try:
        if include_subdirs:
            for root, dirs, files in os.walk(folder_path):
                result['total_folders'] += len(dirs)
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        result['total_files'] += 1
                        result['total_size'] += size
                        
                        # Get file extension
                        _, ext = os.path.splitext(file)
                        ext = ext.lower() if ext else 'no_extension'
                        result['extension_distribution'][ext] += 1
                        result['extension_sizes'][ext] += size
                        
                        # Track largest files (keep top 10)
                        result['largest_files.append']({
                            'name': file,
                            'path': file_path,
                            'size': size,
                            'size_mb': round(size / (1024 * 1024), 2)
                        })
                        # Keep only top 10
                        result['largest_files'] = sorted(
                            result['largest_files'], 
                            key=lambda x: x['size'], 
                            reverse=True
                        )[:10]
                    except Exception as e:
                        result['errors'].append(f"Error processing {file_path}: {str(e)}")
        else:
            # Only top level
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path):
                    result['total_folders'] += 1
                elif os.path.isfile(item_path):
                    try:
                        size = os.path.getsize(item_path)
                        result['total_files'] += 1
                        result['total_size'] += size
                        
                        _, ext = os.path.splitext(item)
                        ext = ext.lower() if ext else 'no_extension'
                        result['extension_distribution'][ext] += 1
                        result['extension_sizes'][ext] += size
                        
                        result['largest_files'].append({
                            'name': item,
                            'path': item_path,
                            'size': size,
                            'size_mb': round(size / (1024 * 1024), 2)
                        })
                    except Exception as e:
                        result['errors'].append(f"Error processing {item_path}: {str(e)}")
            
            result['largest_files'] = sorted(
                result['largest_files'], 
                key=lambda x: x['size'], 
                reverse=True
            )[:10]
        
        # Convert total size to MB/GB
        result['total_size_mb'] = round(result['total_size'] / (1024 * 1024), 2)
        result['total_size_gb'] = round(result['total_size'] / (1024 * 1024 * 1024), 2)
        
        # Convert extension distribution to lists for charting
        result['extension_list'] = [
            {'ext': ext, 'count': count, 'size_mb': round(result['extension_sizes'][ext] / (1024 * 1024), 2)}
            for ext, count in result['extension_distribution'].items()
        ]
        result['extension_list'].sort(key=lambda x: x['count'], reverse=True)
        
    except Exception as e:
        result['errors'].append(f"Analysis failed: {str(e)}")
    
    return result