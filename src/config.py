MAX_DISPLAY_SIZE = 300000

DEFAULT_IGNORE_PATTERNS = [
    '*.pyc', '*.pyo', '*.pyd', '__pycache__',  # Python
    'node_modules', 'bower_components',        # JavaScript
    '.git', '.svn', '.hg', '.gitignore',      # Version control
    '*.svg', '*.png', '*.jpg', '*.jpeg', '*.gif', # Images
    'venv', '.venv', 'env',                   # Virtual environments
    '.idea', '.vscode',                       # IDEs
    '*.log', '*.bak', '*.swp', '*.tmp',      # Temporary files
    '.DS_Store',                             # macOS
    'Thumbs.db',                             # Windows
    'build', 'dist',                         # Build directories
    '*.egg-info',                           # Python egg info
    '*.so', '*.dylib', '*.dll',             # Compiled libraries
    'package-lock.json', 'yarn.lock',        # Package lock files
    'pnpm-lock.yaml', 'npm-shrinkwrap.json', # More package lock files
    'LICENSE', 'LICENSE.*', 'COPYING',       # License files
    'LICENCE', 'LICENCE.*',                  # Alternative spelling
    'COPYING.*', 'COPYRIGHT',                # More license-related files
    'AUTHORS', 'AUTHORS.*',                  # Author files
    'CONTRIBUTORS', 'CONTRIBUTORS.*',        # Contributor files
    'THANKS', 'THANKS.*',                    # Acknowledgment files
    'CHANGELOG', 'CHANGELOG.*',              # Change logs
    'CONTRIBUTING', 'CONTRIBUTING.*'         # Contribution guidelines
]