MAX_DISPLAY_SIZE = 300000
MAX_FILE_SIZE = 10000000
TMP_BASE_PATH = "../tmp"
CLONE_TIMEOUT = 20

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
    'COPYING.*', 'COPYRIGHT',                # More license-related files
    'AUTHORS', 'AUTHORS.*',                  # Author files
    'CONTRIBUTORS', 'CONTRIBUTORS.*',        # Contributor files
    'THANKS', 'THANKS.*',                    # Acknowledgment files
    'CHANGELOG', 'CHANGELOG.*',              # Change logs
    'CONTRIBUTING', 'CONTRIBUTING.*'         # Contribution guidelines
]

EXAMPLE_REPOS = [
    {"name": "Gitingest", "url": "https://github.com/cyclotruc/gitingest"},
    {"name": "FastAPI", "url": "https://github.com/tiangolo/fastapi"},
    {"name": "Ollama", "url": "https://github.com/ollama/ollama"},
    {"name": "Flask", "url": "https://github.com/pallets/flask"},
    {"name": "Tldraw", "url": "https://github.com/tldraw/tldraw"},
    {"name": "Linux", "url": "https://github.com/torvalds/linux"},
]