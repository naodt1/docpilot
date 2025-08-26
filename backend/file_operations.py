# file_operations.py
import os
import shutil
import mimetypes
import magic # python-magic
from config import TEXT_FILE_TYPES, IGNORE_FILE_TYPES

# Attempt to import document parsers
try:
    from docx import Document
except ImportError:
    Document = None
    print("python-docx not installed. DOCX file content will not be extracted.")

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
    print("PyPDF2 not installed. PDF file content will not be extracted.")

class FileOperations:
    def __init__(self):
        # Define custom MIME type mappings for common file extensions
        custom_mimetypes = [
            ('.txt', 'text/plain'),
            ('.md', 'text/markdown'),
            ('.csv', 'text/csv'),
            ('.json', 'application/json'),
            ('.xml', 'application/xml'),
            ('.log', 'text/plain'),
            ('.py', 'text/x-python'),
            ('.js', 'application/javascript'),
            ('.html', 'text/html'),
            ('.css', 'text/css'),
            ('.java', 'text/x-java-source'),
            ('.c', 'text/x-c'),
            ('.cpp', 'text/x-c++src'),
            ('.h', 'text/x-chdr'),
            ('.hpp', 'text/x-c++hdr'),
            ('.php', 'application/x-php'),
            ('.rb', 'application/x-ruby'),
            ('.go', 'text/x-go'),
            ('.rs', 'text/x-rust'),
            ('.sh', 'application/x-sh'),
            ('.bat', 'application/x-msdos-batch'),
            ('.ps1', 'application/x-powershell'),
            ('.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            ('.pdf', 'application/pdf'),
        ]

        # Register each custom mimetype with the mimetypes module
        for ext, mime_type in custom_mimetypes:
            mimetypes.add_type(mime_type, ext)


    def get_file_type(self, file_path: str) -> str:
        """Return the MIME type of a file using python-magic; fallback to mimetypes."""
        try:
            return magic.from_file(file_path, mime=True)
        except Exception as e:
            print(f"Error determining MIME type for {file_path}: {e}")
            return mimetypes.guess_type(file_path)[0] or "application/octet-stream"


    def read_file_content(self, file_path: str) -> str:
        """
        Extracts text content from supported files.
        For DOCX and PDF files, uses specialized libraries to extract text.
        Returns an empty string if the file type is unsupported or unreadable.
        """
        file_extension = os.path.splitext(file_path)[1].lstrip('.').lower()
        mime_type = self.get_file_type(file_path)

        # Check if file is a text file or recognized text MIME type
        if file_extension in TEXT_FILE_TYPES or 'text/' in mime_type:
            try:
                if file_extension == 'docx' and Document:
                    # Extract text from DOCX paragraphs
                    doc = Document(file_path)
                    return "\n".join([paragraph.text for paragraph in doc.paragraphs])
                elif file_extension == 'pdf' and PyPDF2:
                    # Extract text from PDF pages, handling encrypted PDFs
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        if reader.is_encrypted:
                            try:
                                # Attempt to decrypt with empty password
                                reader.decrypt('')
                            except Exception as decrypt_e:
                                print(f"Could not decrypt PDF {file_path}: {decrypt_e}")
                                return ""  # Return empty if decryption fails
                        text = ""
                        for page_num in range(len(reader.pages)):
                            text += reader.pages[page_num].extract_text() or ""
                        return text
                else:
                    # Read other text files with UTF-8 encoding, ignoring errors
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
            except Exception as e:
                print(f"Could not read content from {file_path}: {e}")
                return ""
        return ""

    def move_file(self, source_path: str, destination_folder: str, new_name: str = None) -> bool:
        """
        Moves a file to the specified folder, optionally renaming it.
        Creates the destination folder if it doesn't exist.
        Handles filename conflicts by appending a number suffix.
        """
        try:
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)

            base_name, ext = os.path.splitext(os.path.basename(source_path))
            final_name = f"{new_name}{ext}" if new_name else os.path.basename(source_path)
            destination_path = os.path.join(destination_folder, final_name)

            # Append a counter to filename if a conflict exists
            counter = 1
            while os.path.exists(destination_path):
                name_without_ext, ext = os.path.splitext(final_name)
                destination_path = os.path.join(
                    destination_folder,
                    f"{name_without_ext}_{counter}{ext}"
                )
                counter += 1

            shutil.move(source_path, destination_path)
            print(f"Moved '{source_path}' to '{destination_path}'")
            return True
        except Exception as e:
            print(f"Error moving file {source_path}: {e}")
            return False

    def get_files_in_directory(self, directory: str) -> list[str]:
        """
        Recursively lists all files in a directory, excluding files with ignored extensions.
        """
        files = []
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_extension = os.path.splitext(filename)[1].lstrip('.').lower()
                if file_extension not in IGNORE_FILE_TYPES:
                    files.append(file_path)
        return files

# Example usage for local testing
if __name__ == "__main__":
    # Setup test environment with sample files
    if not os.path.exists("test_files"):
        os.makedirs("test_files")

    with open("test_files/document.txt", "w") as f:
        f.write("This is a test document about project planning.")
    with open("test_files/script.py", "w") as f:
        f.write("print('Hello, World!')\n# This is a simple Python script.")

    file_ops = FileOperations()
    print("\nFiles in test_files:")
    for f_path in file_ops.get_files_in_directory("test_files"):
        print(f_path)
        content = file_ops.read_file_content(f_path)
        print(f"  Content (first 100 chars): {content[:100]}...")

    # Move a test file to a new directory with a new name
    target_folder = "organized_files/TestCategory"
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    file_to_move = "test_files/document.txt"
    if os.path.exists(file_to_move):
        success = file_ops.move_file(file_to_move, target_folder, new_name="Project_Plan_Summary")
        print(f"\nMove successful: {success}")