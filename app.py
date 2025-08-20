# FILEPILOT_BACKEND/main.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import json

from ollama_handler import OllamaHandler
from file_operations import FileOperations
from config import FLASK_PORT

# Initialize Flask app and enable CORS for cross-origin requests (important for Electron communication)
app = Flask(__name__)
CORS(app)

# Initialize handlers for Ollama AI interactions and file operations
ollama_handler = OllamaHandler()
file_operations = FileOperations()

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify that the backend is running.
    
    Returns:
        JSON response indicating the status and a message.
    """
    return jsonify({"status": "healthy", "message": "Python backend is running."}), 200

@app.route('/save_schedule', methods=['POST'])
def save_schedule():
    """
    Saves scheduling information posted by the client.
    
    Expects JSON payload with:
        - directory (str): Directory to schedule operations on.
        - schedule_type (str): Type of schedule (e.g., 'daily', 'weekly').
        - schedule_time (str): Time for the scheduled task.
        - rename_files (bool): Whether to rename files during scheduled operation.
    
    Returns:
        JSON response indicating success or failure of saving the schedule.
    """
    data = request.json
    directory = data.get('directory')
    schedule_type = data.get('schedule_type')
    schedule_time = data.get('schedule_time')
    rename_files = data.get('rename_files')

    if not all([directory, schedule_type]):
        # Required scheduling info missing
        return jsonify({'status': 'error', 'message': 'Missing schedule data.'}), 400

    print(f"Received schedule: Dir='{directory}', Type='{schedule_type}', Time='{schedule_time}', Rename='{rename_files}'")

    try:
        # Append schedule data as JSON line to schedules.json
        with open('schedules.json', 'a') as f:
            f.write(json.dumps(data) + '\n')
        return jsonify({'status': 'success', 'message': 'Schedule saved successfully.'})
    except Exception as e:
        # Handle file write errors
        return jsonify({'status': 'error', 'message': f'Failed to save schedule: {str(e)}'}), 500


@app.route('/analyze_file_for_suggestions', methods=['POST'])
def analyze_file_for_suggestions():
    """
    Analyzes the content of a specified file to provide suggestions.
    
    Expects JSON payload with:
        - file_path (str): Path to the file to analyze.
    
    Returns:
        JSON response with analysis results or error message.
    """
    data = request.json
    file_path = data.get('file_path')

    if not file_path or not os.path.exists(file_path):
        # File path invalid or file missing
        return jsonify({"status": "error", "message": "File not found or invalid path."}), 400

    try:
        # Read file content for analysis
        file_content = file_operations.read_file_content(file_path)
        # Use Ollama AI to analyze content
        analysis = ollama_handler.analyze_content(file_content)
        return jsonify({"status": "success", "analysis": analysis}), 200
    except Exception as e:
        # Log and return analysis failure
        print(f"Error analyzing file {file_path}: {e}")
        return jsonify({"status": "error", "message": f"Failed to analyze file: {str(e)}"}), 500

@app.route('/manual_file_action', methods=['POST'])
def manual_file_action():
    """
    Performs manual file operations such as moving or renaming files.
    
    Expects JSON payload with:a
        - action_type (str): Either 'move' or 'rename'.
        - original_path (str): Current full path of the file.
        - target_path (str): For 'move', the new directory path; for 'rename', the new full file path.
    
    Returns:
        JSON response indicating success or failure, and the new file path if successful.
    """
    data = request.json
    action_type = data.get('action_type')
    original_path = data.get('original_path')
    target_path = data.get('target_path')

    if not action_type or not original_path or not target_path:
        # Missing required parameters
        return jsonify({"status": "error", "message": "Missing action type, original path, or target path."}), 400
    if not os.path.exists(original_path):
        # Original file must exist to proceed
        return jsonify({"status": "error", "message": "Original file not found."}), 404

    try:
        success = False
        message = ""
        if action_type == 'move':
            # Move file to target directory, no rename
            target_directory = target_path
            success = file_operations.move_file(original_path, target_directory, None)
            message = "File moved successfully." if success else "Failed to move file."
        elif action_type == 'rename':
            # Rename file to target path
            success = file_operations.rename_file(original_path, target_path)
            message = "File renamed successfully." if success else "Failed to rename file."
        else:
            # Invalid action type specified
            return jsonify({"status": "error", "message": "Invalid action type."}), 400

        if success:
            return jsonify({"status": "success", "message": message, "new_path": target_path}), 200
        else:
            # Operation failed without exception
            return jsonify({"status": "error", "message": message}), 500
    except Exception as e:
        # Catch unexpected errors during file operations
        print(f"Error performing manual action {action_type} on {original_path}: {e}")
        return jsonify({"status": "error", "message": f"Error performing action: {str(e)}"}), 500

@app.route('/analyze_and_organize', methods=['POST'])
def analyze_and_organize():
    """
    Analyzes files in a source directory and organizes them into categorized folders 
    within a specified destination base directory. Optionally renames files based on analysis.
    
    Expects JSON payload with:
        - source_directory (str): Directory containing files to organize.
        - destination_base_directory (str): Base directory where categorized folders will be created.
        - rename_files (bool, optional): Whether to rename files based on suggestions.
    
    Returns:
        JSON response summarizing processed files and any errors encountered.
    """
    data = request.json
    source_directory = data.get('source_directory')
    destination_base_directory = data.get('destination_base_directory')
    rename_files = data.get('rename_files', False)

    if not source_directory or not destination_base_directory:
        return jsonify({"status": "error", "message": "Missing source or destination directory."}), 400
    if not os.path.isdir(source_directory):
        # Ensure source directory exists and is accessible
        return jsonify({"status": "error", "message": f"Source directory '{source_directory}' does not exist."}), 400

    processed_files = []
    errors = []

    # Retrieve list of files to process
    files_to_process = file_operations.get_files_in_directory(source_directory)

    for file_path in files_to_process:
        try:
            # Read each file's content
            file_content = file_operations.read_file_content(file_path)
            # Analyze content for category and new name suggestion
            analysis = ollama_handler.analyze_content(file_content)

            category = analysis.get("category", "Miscellaneous")
            new_name_suggestion = analysis.get("new_name_suggestion")

            # Destination folder based on category
            final_destination_folder = os.path.join(destination_base_directory, category)

            original_base_name, ext = os.path.splitext(os.path.basename(file_path))
            final_new_name = None
            if rename_files and new_name_suggestion:
                # Clean and format suggested new name
                cleaned_name = re.sub(r'[^\w\s.-]', '', new_name_suggestion).strip()
                cleaned_name = re.sub(r'\s+', '_', cleaned_name)
                if cleaned_name:
                    final_new_name = cleaned_name.lower()

            # Move (and optionally rename) file to destination folder
            success = file_operations.move_file(file_path, final_destination_folder, final_new_name)

            if success:
                processed_files.append({
                    "original_path": file_path,
                    "new_path": os.path.join(final_destination_folder, (final_new_name if final_new_name else original_base_name) + ext),
                    "category": category,
                    "renamed": bool(final_new_name)
                })
            else:
                errors.append({"file": file_path, "message": "Failed to move file."})

        except Exception as e:
            # Log individual file errors but continue processing others
            errors.append({"file": file_path, "message": str(e)})

    return jsonify({
        "status": "success",
        "processed_count": len(processed_files),
        "error_count": len(errors),
        "processed_files": processed_files,
        "errors": errors
    }), 200

@app.route('/auto_organize_in_place', methods=['POST'])
def auto_organize_in_place():
    """
    Analyzes and organizes files directly within the specified source directory,
    creating categorized subfolders as needed. Optionally renames files.
    
    Expects JSON payload with:
        - source_directory (str): Directory to organize in place.
        - rename_files (bool, optional): Whether to rename files based on suggestions.
    
    Returns:
        JSON response summarizing processed files and any errors encountered.
    """
    data = request.json
    source_directory = data.get('source_directory')
    rename_files = data.get('rename_files', False)

    if not source_directory:
        return jsonify({"status": "error", "message": "Missing directory to auto-organize."}), 400
    if not os.path.isdir(source_directory):
        # Validate directory existence and accessibility
        return jsonify({"status": "error", "message": f"Directory '{source_directory}' does not exist or is not accessible."}), 400

    processed_files = []
    errors = []

    # List files in source directory
    files_to_process = file_operations.get_files_in_directory(source_directory)

    for file_path in files_to_process:
        try:
            # Read file content for analysis
            file_content = file_operations.read_file_content(file_path)
            # Analyze content for category and renaming suggestions
            analysis = ollama_handler.analyze_content(file_content)

            category = analysis.get("category", "Miscellaneous")
            new_name_suggestion = analysis.get("new_name_suggestion")

            # Destination folder is a subfolder in source directory
            final_destination_folder = os.path.join(source_directory, category)

            original_base_name, ext = os.path.splitext(os.path.basename(file_path))
            final_new_name = None
            if rename_files and new_name_suggestion:
                # Sanitize and format new name
                cleaned_name = re.sub(r'[^\w\s.-]', '', new_name_suggestion).strip()
                cleaned_name = re.sub(r'\s+', '_', cleaned_name)
                if cleaned_name:
                    final_new_name = cleaned_name.lower()

            # Move and optionally rename file within source directory
            success = file_operations.move_file(file_path, final_destination_folder, final_new_name)

            if success:
                processed_files.append({
                    "original_path": file_path,
                    "new_path": os.path.join(final_destination_folder, (final_new_name if final_new_name else original_base_name) + ext),
                    "category": category,
                    "renamed": bool(final_new_name)
                })
            else:
                errors.append({"file": file_path, "message": "Failed to move file."})

        except Exception as e:
            # Continue processing other files despite errors
            errors.append({"file": file_path, "message": str(e)})

    return jsonify({
        "status": "success",
        "processed_count": len(processed_files),
        "error_count": len(errors),
        "processed_files": processed_files,
        "errors": errors
    }), 200

@app.route('/get_file_content', methods=['POST'])
def get_file_content():
    """
    Retrieves the content of a specified file.
    
    Expects JSON payload with:
        - file_path (str): Path to the file.
    
    Returns:
        JSON response with file content or error if file not found.
    """
    data = request.json
    file_path = data.get('file_path')

    if not file_path or not os.path.exists(file_path):
        # File must exist to return content
        return jsonify({"status": "error", "message": "File not found."}), 404

    # Read and return file content
    content = file_operations.read_file_content(file_path)
    return jsonify({"status": "success", "content": content}), 200

@app.route('/list_files', methods=['POST'])
def list_files_in_directory():
    """
    Lists all files within a specified directory.
    
    Expects JSON payload with:
        - directory_path (str): Path to the directory.
    
    Returns:
        JSON response with list of files or error if directory not found.
    """
    data = request.json
    directory_path = data.get('directory_path')

    if not directory_path or not os.path.isdir(directory_path):
        # Directory must exist to list files
        return jsonify({"status": "error", "message": "Directory not found."}), 404

    # Retrieve and return list of files
    files = file_operations.get_files_in_directory(directory_path)
    return jsonify({"status": "success", "files": files}), 200

if __name__ == '__main__':
    print(f"Starting Flask backend on port {FLASK_PORT}...")
    app.run(port=FLASK_PORT, debug=True)  # debug=True for development, disable in production