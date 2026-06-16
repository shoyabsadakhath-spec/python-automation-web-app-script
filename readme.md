# Python Automation Script

A powerful web-based automation tool for file operations including renaming, sorting, duplicate detection, cleanup, and analytics. Built with Flask and modern UI.

## Features

### Core Modules
- **File Renamer**: Batch rename files with prefixes, suffixes, numbering, and special character removal
- **File Sorter**: Automatically organize files into categories (Images, Documents, Videos, Audio, Archives, Programs)
- **Duplicate Finder**: Detect duplicate files using hash comparison with deletion options
- **Cleanup Center**: Remove temporary files (.tmp, .log, .cache, etc.)
- **Folder Analyzer**: Generate detailed statistics with charts (file distribution, largest files)
- **Activity Logs**: Track all operations with search and export functionality

### Dashboard Features
- Real-time statistics (operations count, success rate, space cleaned)
- Professional UI with dark/light mode
- Responsive design for all devices
- Toast notifications and loading indicators
- Interactive charts with Chart.js

## Technology Stack

- **Backend**: Python 3, Flask, SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js
- **Libraries**: OS, shutil, hashlib, pathlib, logging

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Steps

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/PythonAutomationScript.git
cd PythonAutomationScript