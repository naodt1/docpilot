# config.py
import os

# Ollama Configuration
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'phi3') # You can change this to a model you have pulled, e.g., 'llama2', 'mistral'

# Flask Configuration
FLASK_PORT = os.getenv('FLASK_PORT', 5000)

# File Types to Process (add/remove as needed)
# Text-based files that Ollama can directly analyze their content
TEXT_FILE_TYPES = [
    'txt', 'md', 'csv', 'json', 'xml', 'log', 'py', 'js', 'html', 'css', 'java',
    'c', 'cpp', 'h', 'hpp', 'php', 'rb', 'go', 'rs', 'sh', 'bat', 'ps1',
    'docx', 'pdf', # These will require text extraction logic
]

# File types to ignore (e.g., executables, system files)
IGNORE_FILE_TYPES = [
    'exe', 'dll', 'sys', 'ini', 'lnk', 'tmp', 'DS_Store',
]