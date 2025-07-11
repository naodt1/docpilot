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
        # Define your custom MIME type mappings
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

        # Add each custom mimetype using mimetypes.add_type
        # Note: add_type expects mimetype first, then extension
        for ext, mime_type in custom_mimetypes:
            mimetypes.add_type(mime_type, ext)


    def get_file_type(self, file_path: str) -> str:
        """Determines the file's MIME type using python-magic."""
        try:
            return magic.from_file(file_path, mime=True)
        except Exception as e:
            print(f"Error determining MIME type for {file_path}: {e}")
            return mimetypes.guess_type(file_path)[0] or "application/octet-stream"


    def read_file_content(self, file_path: str) -> str:
        """
        Reads content from supported text files and extracts text from DOCX/PDF.
        Returns an empty string for unsupported or binary files.
        """
        file_extension = os.path.splitext(file_path)[1].lstrip('.').lower()
        mime_type = self.get_file_type(file_path)

        # Basic check for file types Ollama can likely handle by content
        if file_extension in TEXT_FILE_TYPES or 'text/' in mime_type:
            try:
                if file_extension == 'docx' and Document:
                    doc = Document(file_path)
                    return "\n".join([paragraph.text for paragraph in doc.paragraphs])
                elif file_extension == 'pdf' and PyPDF2:
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        # Handle potential for encrypted PDFs
                        if reader.is_encrypted:
                            try:
                                # Try with empty password, or handle user input for password
                                reader.decrypt('')
                            except Exception as decrypt_e:
                                print(f"Could not decrypt PDF {file_path}: {decrypt_e}")
                                return "" # Return empty if decryption fails

                        for page_num in range(len(reader.pages)):
                            text += reader.pages[page_num].extract_text() or ""
                        return text
                else: # For other text-based files
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
            except Exception as e:
                print(f"Could not read content from {file_path}: {e}")
                return ""
        return ""

    def move_file(self, source_path: str, destination_folder: str, new_name: str = None) -> bool:
        """
        Moves a file to a new folder, optionally renaming it.
        Creates the destination folder if it doesn't exist.
        """
        try:
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)

            base_name, ext = os.path.splitext(os.path.basename(source_path))
            if new_name:
                final_name = f"{new_name}{ext}"
            else:
                final_name = os.path.basename(source_path)

            destination_path = os.path.join(destination_folder, final_name)

            # Handle potential name conflicts by adding a number
            counter = 1
            original_destination_path = destination_path
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
        Lists all files in a given directory, ignoring specified file types.
        """
        files = []
        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_extension = os.path.splitext(filename)[1].lstrip('.').lower()
                if file_extension not in IGNORE_FILE_TYPES:
                    files.append(file_path)
        return files

# Example Usage (for testing)
if __name__ == "__main__":
    # Create some dummy files for testing
    if not os.path.exists("test_files"):
        os.makedirs("test_files")

    with open("test_files/document.txt", "w") as f:
        f.write("This is a test document about project planning.")
    with open("test_files/script.py", "w") as f:
        f.write("print('Hello, World!')\n# This is a simple Python script.")
    # You'd need to create actual .docx and .pdf files to test their extraction
    # and ensure python-docx and PyPDF2 are installed.

    file_ops = FileOperations()
    print("\nFiles in test_files:")
    for f_path in file_ops.get_files_in_directory("test_files"):
        print(f_path)
        content = file_ops.read_file_content(f_path)
        print(f"  Content (first 100 chars): {content[:100]}...")

    # Test moving a file
    if not os.path.exists("organized_files/TestCategory"):
        os.makedirs("organized_files/TestCategory")
    file_to_move = "test_files/document.txt"
    if os.path.exists(file_to_move):
        success = file_ops.move_file(file_to_move, "organized_files/TestCategory", new_name="Project_Plan_Summary")
        print(f"\nMove successful: {success}")

    # Clean up (optional)
    # shutil.rmtree("test_files")
    # shutil.rmtree("organized_files")