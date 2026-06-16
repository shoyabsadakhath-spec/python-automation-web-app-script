import os
import logging
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from functools import wraps

# Import services
from services import renamer, sorter, duplicate_finder, cleaner, analyzer

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Database setup
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'automation.db')

def init_database():
    """Initialize SQLite database with required tables"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Activity logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            folder_path TEXT,
            details TEXT,
            files_affected INTEGER DEFAULT 0,
            space_saved INTEGER DEFAULT 0
        )
    ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Insert default settings if not exists
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('default_folder', ''))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", ('theme', 'light'))
    
    conn.commit()
    conn.close()

# Logging setup
LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'app.log')
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def log_activity(action, status, folder_path=None, details=None, files_affected=0, space_saved=0):
    """Log activity to both file and database"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # File logging
    log_message = f"{action} - {status}"
    if details:
        log_message += f" - {details}"
    if status == 'SUCCESS':
        logging.info(log_message)
    else:
        logging.error(log_message)
    
    # Database logging
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO activity_logs (timestamp, action, status, folder_path, details, files_affected, space_saved)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, action, status, folder_path, details[:500] if details else '', files_affected, space_saved))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Failed to log to database: {str(e)}")

def get_setting(key, default=''):
    """Get a setting from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default
    except:
        return default

def save_setting(key, value):
    """Save a setting to database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Failed to save setting: {str(e)}")
        return False

def get_dashboard_stats():
    """Get statistics for dashboard display"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Total operations
        cursor.execute("SELECT COUNT(*) FROM activity_logs")
        total_ops = cursor.fetchone()[0]
        
        # Success rate
        cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE status = 'SUCCESS'")
        success_ops = cursor.fetchone()[0]
        success_rate = round((success_ops / total_ops * 100), 1) if total_ops > 0 else 0
        
        # Total space cleaned
        cursor.execute("SELECT SUM(space_saved) FROM activity_logs")
        space_cleaned = cursor.fetchone()[0] or 0
        
        # Total files affected
        cursor.execute("SELECT SUM(files_affected) FROM activity_logs")
        files_affected = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_operations': total_ops,
            'success_rate': success_rate,
            'space_cleaned_mb': round(space_cleaned / (1024 * 1024), 2),
            'files_affected': files_affected
        }
    except Exception as e:
        logging.error(f"Failed to get dashboard stats: {str(e)}")
        return {
            'total_operations': 0,
            'success_rate': 0,
            'space_cleaned_mb': 0,
            'files_affected': 0
        }

# Routes
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/renamer', methods=['GET', 'POST'])
def renamer_page():
    if request.method == 'POST':
        folder_path = request.form.get('folder_path', '').strip()
        prefix = request.form.get('prefix', '')
        suffix = request.form.get('suffix', '')
        numbering = request.form.get('numbering') == 'on'
        start_num = int(request.form.get('start_num', 1))
        remove_special = request.form.get('remove_special') == 'on'
        include_subdirs = request.form.get('include_subdirs') == 'on'
        
        # Validation
        if not folder_path:
            flash('Please enter a folder path', 'error')
            return redirect(url_for('renamer_page'))
        
        if not os.path.exists(folder_path):
            flash(f'Folder does not exist: {folder_path}', 'error')
            return redirect(url_for('renamer_page'))
        
        try:
            # Perform rename operation
            result = renamer.rename_files(
                folder_path, prefix, suffix, numbering, 
                start_num, remove_special, include_subdirs
            )
            
            # Log activity
            status = 'SUCCESS' if len(result['errors']) == 0 else 'PARTIAL'
            details = f"Renamed {result['renamed_count']} files. Errors: {len(result['errors'])}"
            log_activity('RENAME_FILES', status, folder_path, details, result['renamed_count'])
            
            if result['renamed_count'] > 0:
                flash(f'Successfully renamed {result["renamed_count"]} files!', 'success')
            if result['errors']:
                for error in result['errors'][:5]:  # Show first 5 errors
                    flash(error, 'error')
                    
        except Exception as e:
            log_activity('RENAME_FILES', 'ERROR', folder_path, str(e))
            flash(f'Error during rename operation: {str(e)}', 'error')
        
        return redirect(url_for('renamer_page'))
    
    default_folder = get_setting('default_folder')
    return render_template('renamer.html', default_folder=default_folder)

@app.route('/sorter', methods=['GET', 'POST'])
def sorter_page():
    if request.method == 'POST':
        folder_path = request.form.get('folder_path', '').strip()
        include_subdirs = request.form.get('include_subdirs') == 'on'
        
        if not folder_path:
            flash('Please enter a folder path', 'error')
            return redirect(url_for('sorter_page'))
        
        if not os.path.exists(folder_path):
            flash(f'Folder does not exist: {folder_path}', 'error')
            return redirect(url_for('sorter_page'))
        
        try:
            result = sorter.sort_files(folder_path, include_subdirs)
            
            status = 'SUCCESS' if len(result['errors']) == 0 else 'PARTIAL'
            details = f"Sorted {result['sorted_count']} files. Categories: {result['category_stats']}"
            log_activity('SORT_FILES', status, folder_path, details, result['sorted_count'])
            
            if result['sorted_count'] > 0:
                flash(f'Successfully sorted {result["sorted_count"]} files!', 'success')
            if result['errors']:
                for error in result['errors'][:5]:
                    flash(error, 'error')
                    
        except Exception as e:
            log_activity('SORT_FILES', 'ERROR', folder_path, str(e))
            flash(f'Error during sort operation: {str(e)}', 'error')
        
        return redirect(url_for('sorter_page'))
    
    default_folder = get_setting('default_folder')
    return render_template('sorter.html', default_folder=default_folder)

@app.route('/duplicates', methods=['GET', 'POST'])
def duplicates_page():
    duplicates_data = None
    folder_path = ''
    
    if request.method == 'POST':
        action = request.form.get('action')
        folder_path = request.form.get('folder_path', '').strip()
        
        if action == 'scan':
            if not folder_path:
                flash('Please enter a folder path', 'error')
                return redirect(url_for('duplicates_page'))
            
            if not os.path.exists(folder_path):
                flash(f'Folder does not exist: {folder_path}', 'error')
                return redirect(url_for('duplicates_page'))
            
            try:
                duplicates_data = duplicate_finder.find_duplicates(folder_path, True)
                log_activity('FIND_DUPLICATES', 'SUCCESS', folder_path, 
                            f"Found {duplicates_data['total_duplicates']} duplicate files", 
                            duplicates_data['total_duplicates'])
                
                if duplicates_data['total_duplicates'] == 0:
                    flash('No duplicate files found!', 'success')
                    
            except Exception as e:
                log_activity('FIND_DUPLICATES', 'ERROR', folder_path, str(e))
                flash(f'Error finding duplicates: {str(e)}', 'error')
                
        elif action == 'delete':
            duplicate_paths = request.form.getlist('duplicate_paths')
            if duplicate_paths:
                try:
                    result = duplicate_finder.delete_duplicates(duplicate_paths)
                    log_activity('DELETE_DUPLICATES', 'SUCCESS', folder_path,
                                f"Deleted {result['deleted_count']} duplicate files",
                                result['deleted_count'], result['freed_space'])
                    flash(f'Successfully deleted {result["deleted_count"]} duplicate files. Freed {round(result["freed_space"]/(1024*1024),2)} MB', 'success')
                except Exception as e:
                    log_activity('DELETE_DUPLICATES', 'ERROR', folder_path, str(e))
                    flash(f'Error deleting duplicates: {str(e)}', 'error')
            else:
                flash('No files selected for deletion', 'warning')
            
            return redirect(url_for('duplicates_page'))
    
    default_folder = get_setting('default_folder')
    return render_template('duplicates.html', duplicates_data=duplicates_data, folder_path=folder_path, default_folder=default_folder)

@app.route('/cleanup', methods=['GET', 'POST'])
def cleanup_page():
    temp_files = None
    folder_path = ''
    
    if request.method == 'POST':
        action = request.form.get('action')
        folder_path = request.form.get('folder_path', '').strip()
        patterns = request.form.get('patterns', '').strip()
        include_subdirs = request.form.get('include_subdirs') == 'on'
        
        pattern_list = [p.strip() for p in patterns.split(',')] if patterns else cleaner.DEFAULT_PATTERNS
        
        if not folder_path:
            flash('Please enter a folder path', 'error')
            return redirect(url_for('cleanup_page'))
        
        if not os.path.exists(folder_path):
            flash(f'Folder does not exist: {folder_path}', 'error')
            return redirect(url_for('cleanup_page'))
        
        if action == 'scan':
            try:
                temp_files = cleaner.find_temp_files(folder_path, pattern_list, include_subdirs)
                if temp_files['errors']:
                    for error in temp_files['errors']:
                        flash(error, 'error')
                elif len(temp_files['files']) == 0:
                    flash('No temporary files found matching the patterns.', 'info')
                else:
                    flash(f'Found {len(temp_files["files"])} temporary files (Total size: {round(temp_files["total_size"]/(1024*1024),2)} MB)', 'success')
            except Exception as e:
                flash(f'Error scanning files: {str(e)}', 'error')
                
        elif action == 'clean':
            try:
                result = cleaner.clean_temp_files(folder_path, pattern_list, include_subdirs)
                log_activity('CLEANUP_TEMP', 'SUCCESS' if len(result['errors']) == 0 else 'PARTIAL',
                            folder_path, f"Deleted {result['deleted_count']} files",
                            result['deleted_count'], result['freed_space'])
                flash(f'Cleaned {result["deleted_count"]} files. Freed {round(result["freed_space"]/(1024*1024),2)} MB', 'success')
                if result['errors']:
                    for error in result['errors']:
                        flash(error, 'error')
            except Exception as e:
                log_activity('CLEANUP_TEMP', 'ERROR', folder_path, str(e))
                flash(f'Error cleaning files: {str(e)}', 'error')
            
            return redirect(url_for('cleanup_page'))
    
    default_folder = get_setting('default_folder')
    return render_template('cleanup.html', temp_files=temp_files, folder_path=folder_path, default_folder=default_folder)

@app.route('/analytics', methods=['GET', 'POST'])
def analytics_page():
    analysis_result = None
    folder_path = ''
    
    if request.method == 'POST':
        folder_path = request.form.get('folder_path', '').strip()
        include_subdirs = request.form.get('include_subdirs') == 'on'
        
        if not folder_path:
            flash('Please enter a folder path', 'error')
            return redirect(url_for('analytics_page'))
        
        if not os.path.exists(folder_path):
            flash(f'Folder does not exist: {folder_path}', 'error')
            return redirect(url_for('analytics_page'))
        
        try:
            analysis_result = analyzer.analyze_folder(folder_path, include_subdirs)
            log_activity('ANALYZE_FOLDER', 'SUCCESS', folder_path, 
                        f"Found {analysis_result['total_files']} files, {analysis_result['total_folders']} folders")
            
            if analysis_result['errors']:
                for error in analysis_result['errors']:
                    flash(error, 'error')
        except Exception as e:
            log_activity('ANALYZE_FOLDER', 'ERROR', folder_path, str(e))
            flash(f'Error analyzing folder: {str(e)}', 'error')
    
    default_folder = get_setting('default_folder')
    return render_template('analytics.html', analysis=analysis_result, folder_path=folder_path, default_folder=default_folder)

@app.route('/logs')
def logs_page():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Build query with search
    query = "SELECT * FROM activity_logs"
    params = []
    if search:
        query += " WHERE action LIKE ? OR details LIKE ? OR folder_path LIKE ?"
        search_param = f"%{search}%"
        params = [search_param, search_param, search_param]
    
    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    
    # Get total count for pagination
    count_query = "SELECT COUNT(*) FROM activity_logs"
    if search:
        count_query += " WHERE action LIKE ? OR details LIKE ? OR folder_path LIKE ?"
        cursor.execute(count_query, [search_param, search_param, search_param])
    else:
        cursor.execute(count_query)
    total = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('logs.html', logs=logs, page=page, total=total, per_page=per_page, search=search)

@app.route('/export-logs')
def export_logs():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activity_logs ORDER BY timestamp DESC")
    logs = cursor.fetchall()
    conn.close()
    
    # Create CSV content
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Timestamp', 'Action', 'Status', 'Folder Path', 'Details', 'Files Affected', 'Space Saved (bytes)'])
    
    for log in logs:
        writer.writerow(log)
    
    output.seek(0)
    return send_file(
        StringIO(output.getvalue()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='automation_logs.csv'
    )

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    if request.method == 'POST':
        default_folder = request.form.get('default_folder', '').strip()
        theme = request.form.get('theme', 'light')
        
        save_setting('default_folder', default_folder)
        save_setting('theme', theme)
        
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings_page'))
    
    default_folder = get_setting('default_folder')
    theme = get_setting('theme', 'light')
    
    return render_template('settings.html', default_folder=default_folder, theme=theme)

# Initialize database on startup
init_database()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)