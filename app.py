# FILEPILOT_BACKEND/main.py
from flask import Flask, request, jsonify
from flask_cors import CORS # For Electron development, allow CORS
import os
import re # Added for cleaning up suggested file names
import json

from ollama_handler import OllamaHandler
from file_operations import FileOperations
from config import FLASK_PORT

app = Flask(__name__)
CORS(app) # Enable CORS for all routes (important for Electron communication)

ollama_handler = OllamaHandler()
file_operations = FileOperations()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint for health checking the Flask backend."""
    return jsonify({"status": "healthy", "message": "Python backend is running."}), 200

@app.route('/save_schedule', methods=['POST'])
def save_schedule():
    data = request.json
    directory = data.get('directory')
    schedule_type = data.get('schedule_type')
    schedule_time = data.get('schedule_time')
    rename_files = data.get('rename_files')

    if not all([directory, schedule_type]):
        return jsonify({'status': 'error', 'message': 'Missing schedule data.'}), 400

    # --- IMPORTANT: Implement your actual scheduling logic here ---
    # This is where you would integrate with APScheduler or similar.
    # For a simple example, you might just log it or save to a config file.
    print(f"Received schedule: Dir='{directory}', Type='{schedule_type}', Time='{schedule_time}', Rename='{rename_files}'")

    # Example of saving to a simple config file (for demonstration, not robust for production)
    try:
        with open('schedules.json', 'a') as f: # Append mode
            f.write(json.dumps(data) + '\n')
        # If using APScheduler, you'd add/replace the job here.
        # scheduler.add_job(...)
        return jsonify({'status': 'success', 'message': 'Schedule saved successfully.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save schedule: {str(e)}'}), 500


@app.route('/analyze_file_for_suggestions', methods=['POST'])
def analyze_file_for_suggestions():
    data = request.json
    file_path = data.get('file_path')

    if not file_path or not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "File not found or invalid path."}), 400

    try:
        file_content = file_operations.read_file_content(file_path)
        analysis = ollama_handler.analyze_content(file_content)
        return jsonify({"status": "success", "analysis": analysis}), 200
    except Exception as e:
        print(f"Error analyzing file {file_path}: {e}")
        return jsonify({"status": "error", "message": f"Failed to analyze file: {str(e)}"}), 500

# NEW ROUTE: Perform manual move/rename actions (used by Manual tab)
@app.route('/manual_file_action', methods=['POST'])
def manual_file_action():
    data = request.json
    action_type = data.get('action_type') # 'move' or 'rename'
    original_path = data.get('original_path')
    target_path = data.get('target_path') # For move: new destination path, for rename: new full path with name

    if not action_type or not original_path or not target_path:
        return jsonify({"status": "error", "message": "Missing action type, original path, or target path."}), 400
    if not os.path.exists(original_path):
        return jsonify({"status": "error", "message": "Original file not found."}), 404

    try:
        success = False
        message = ""
        if action_type == 'move':
            # target_path here is the new directory
            target_directory = target_path
            success = file_operations.move_file(original_path, target_directory, None) # No rename for move action itself
            message = "File moved successfully." if success else "Failed to move file."
        elif action_type == 'rename':
            # target_path here is the new full file path (dir + new_name + ext)
            success = file_operations.rename_file(original_path, target_path)
            message = "File renamed successfully." if success else "Failed to rename file."
        else:
            return jsonify({"status": "error", "message": "Invalid action type."}), 400

        if success:
            return jsonify({"status": "success", "message": message, "new_path": target_path}), 200
        else:
            return jsonify({"status": "error", "message": message}), 500
    except Exception as e:
        print(f"Error performing manual action {action_type} on {original_path}: {e}")
        return jsonify({"status": "error", "message": f"Error performing action: {str(e)}"}), 500

# Kept the original /analyze_and_organize route for now, as you asked for *another* route.
# If you decide this route is no longer needed, you can remove it.
@app.route('/analyze_and_organize', methods=['POST'])
def analyze_and_organize():
    """
    Analyzes and organizes files from a source to a specified base destination directory.
    This route will still work if you decide to use it from other interfaces.
    """
    data = request.json
    source_directory = data.get('source_directory')
    destination_base_directory = data.get('destination_base_directory') # Still expects this for this route
    rename_files = data.get('rename_files', False)

    if not source_directory or not destination_base_directory:
        return jsonify({"status": "error", "message": "Missing source or destination directory."}), 400
    if not os.path.isdir(source_directory):
        return jsonify({"status": "error", "message": f"Source directory '{source_directory}' does not exist."}), 400

    processed_files = []
    errors = []

    files_to_process = file_operations.get_files_in_directory(source_directory)

    for file_path in files_to_process:
        try:
            file_content = file_operations.read_file_content(file_path)
            analysis = ollama_handler.analyze_content(file_content)

            category = analysis.get("category", "Miscellaneous")
            new_name_suggestion = analysis.get("new_name_suggestion")

            final_destination_folder = os.path.join(destination_base_directory, category)

            original_base_name, ext = os.path.splitext(os.path.basename(file_path))
            final_new_name = None
            if rename_files and new_name_suggestion:
                # Clean up suggested name: remove invalid chars, replace spaces with underscores
                cleaned_name = re.sub(r'[^\w\s.-]', '', new_name_suggestion).strip() # Allow letters, numbers, spaces, periods, hyphens
                cleaned_name = re.sub(r'\s+', '_', cleaned_name) # Replace multiple spaces with single underscore
                if cleaned_name:
                    final_new_name = cleaned_name.lower()

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
            errors.append({"file": file_path, "message": str(e)})

    return jsonify({
        "status": "success",
        "processed_count": len(processed_files),
        "error_count": len(errors),
        "processed_files": processed_files,
        "errors": errors
    }), 200

# NEW ROUTE: For in-place automated organization
@app.route('/auto_organize_in_place', methods=['POST'])
def auto_organize_in_place():
    """
    Analyzes and organizes files directly within the specified source directory,
    creating categorized subfolders as needed.
    """
    data = request.json
    source_directory = data.get('source_directory') # Now this is the primary directory for organization
    rename_files = data.get('rename_files', False)

    if not source_directory:
        return jsonify({"status": "error", "message": "Missing directory to auto-organize."}), 400
    if not os.path.isdir(source_directory):
        return jsonify({"status": "error", "message": f"Directory '{source_directory}' does not exist or is not accessible."}), 400

    processed_files = []
    errors = []

    files_to_process = file_operations.get_files_in_directory(source_directory)

    for file_path in files_to_process:
        try:
            file_content = file_operations.read_file_content(file_path)
            analysis = ollama_handler.analyze_content(file_content)

            category = analysis.get("category", "Miscellaneous")
            new_name_suggestion = analysis.get("new_name_suggestion")

            # The destination folder is now within the source directory itself
            final_destination_folder = os.path.join(source_directory, category)

            original_base_name, ext = os.path.splitext(os.path.basename(file_path))
            final_new_name = None
            if rename_files and new_name_suggestion:
                # Clean up suggested name: remove invalid chars, replace spaces with underscores
                cleaned_name = re.sub(r'[^\w\s.-]', '', new_name_suggestion).strip() # Allow letters, numbers, spaces, periods, hyphens
                cleaned_name = re.sub(r'\s+', '_', cleaned_name) # Replace multiple spaces with single underscore
                if cleaned_name:
                    final_new_name = cleaned_name.lower()

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
    """Retrieves the content of a specified file."""
    data = request.json
    file_path = data.get('file_path')

    if not file_path or not os.path.exists(file_path):
        return jsonify({"status": "error", "message": "File not found."}), 404

    content = file_operations.read_file_content(file_path)
    return jsonify({"status": "success", "content": content}), 200

@app.route('/list_files', methods=['POST'])
def list_files_in_directory():
    """Lists files within a specified directory."""
    data = request.json
    directory_path = data.get('directory_path')

    if not directory_path or not os.path.isdir(directory_path):
        return jsonify({"status": "error", "message": "Directory not found."}), 404

    files = file_operations.get_files_in_directory(directory_path)
    return jsonify({"status": "success", "files": files}), 200

if __name__ == '__main__':
    print(f"Starting Flask backend on port {FLASK_PORT}...")
    app.run(port=FLASK_PORT, debug=True) # debug=True for development, turn off in production