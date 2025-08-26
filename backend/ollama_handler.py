# ollama_handler.py
import ollama
import subprocess
from config import OLLAMA_HOST, OLLAMA_MODEL

class OllamaHandler:
    """
    Handler class for interacting with the Ollama API to analyze file content and suggest file names.
    """

    def __init__(self, host=OLLAMA_HOST, model=OLLAMA_MODEL):
        """
        Initialize the Ollama client with the specified host and model.
        Ensures the required model is available locally.

        Args:
            host (str): The Ollama server host.
            model (str): The Ollama model to use.
        """
        self.client = ollama.Client(host=host)
        self.model = model
        self.ensure_model()

    def ensure_model(self):
        """
        Ensure the specified Ollama model is pulled and ready for use.
        Pulls the model via subprocess; logs errors if any occur.
        """
        try:
            # Use subprocess to pull the model to ensure it's downloaded locally
            subprocess.run(["ollama", "pull", self.model], check=True)
            print(f"Ollama model '{self.model}' is ready.")
        except Exception as e:
            # Log any errors during model pulling; client may fail if model is missing
            print(f"Error pulling model '{self.model}': {e}")

    def analyze_content(self, content: str) -> dict:
        """
        Analyze the given file content to determine its category and suggest a new file name.

        Args:
            content (str): The textual content of the file to analyze.

        Returns:
            dict: A dictionary with keys 'category' (str) and 'new_name_suggestion' (str or None).
                  If category is 'Miscellaneous', 'new_name_suggestion' will be None.
        """
        category_rules = """
        - 'Business': Business plans, reports, proposals, meeting minutes, strategies, marketing materials.
            - Name Suggestion: Focus on type and topic (e.g., 'Q3 Business Review', 'Marketing Strategy Plan').
        - 'Code': Programming source code (Python, JavaScript, C++, Java, etc.), scripts, configuration files, algorithms.
            - Name Suggestion: Based on function, language, or project part (e.g., 'Python API Handler', 'Web Component Logic', 'Database Schema').
        - 'Creative': Articles, stories, poems, scripts (film/play), design briefs, artistic concepts, personal journals.
            - Name Suggestion: Reflect the creative work's title or main theme (e.g., 'SciFi Short Story Draft', 'Poetry Collection Ideas').
        - 'Data': Spreadsheets, CSVs, JSON, XML, database dumps, statistical reports, analytical data sets.
            - Name Suggestion: Describe the data's content or source (e.g., 'Sales Data Q1', 'Customer Survey Results', 'Website Traffic Log').
        - 'Education': Lecture notes, assignments, research papers, study guides, course materials, educational articles.
            - Name Suggestion: Based on subject, course, or assignment (e.g., 'Calculus Lecture 5', 'History Essay Civil War', 'Biology Study Notes').
        - 'Financial': Budgets, invoices, receipts, expense reports, tax documents, bank statements, investment summaries.
            - Name Suggestion: Specific to the financial transaction/period (e.g., 'Monthly Budget July 2025', 'Invoice Client X', 'Tax Returns 2024').
        - 'Images': Descriptions or metadata about images, image lists, photo albums (not the image data itself).
            - Name Suggestion: Describe the subject or event (e.g., 'Vacation Photos Italy', 'Product Shots Catalog').
        - 'Legal': Contracts, agreements, policies, legal briefs, court documents, terms of service.
            - Name Suggestion: Reflect parties and type of document (e.g., 'Client Service Agreement', 'NDA Draft').
        - 'Logs': System logs, application logs, error reports, debugging output.
            - Name Suggestion: Reflect origin and date/time (e.g., 'Server Error Log 2025-07-10', 'App Crash Report').
        - 'Personal': Resumes, cover letters, personal notes, health records, medical information, diaries, family documents.
            - Name Suggestion: Specific and personal (e.g., 'My Resume Updated', 'Doctor Visit Summary', 'Family Photo Album Notes').
        - 'Presentations': Outlines, scripts, or content for slideshows/presentations.
            - Name Suggestion: Title of presentation (e.g., 'Annual Sales Pitch', 'Project Status Meeting Slides').
        - 'Miscellaneous': For content that is empty, too brief, cannot be clearly identified, or does not fit any other category.
            - Name Suggestion: In this case, `new_name_suggestion` MUST be `null`.
        """

        prompt = f"""
        You are a highly skilled AI assistant specializing in file organization. Your primary task is to carefully analyze the provided "File Content" and assign it the single most appropriate category from the predefined list below. In addition, you must suggest a concise and descriptive new file name (without extension) that accurately reflects the content.

        **Predefined Categories & Naming Guidelines:**
        {category_rules.strip()}

        **Output Format:**
        Your response MUST be a valid JSON object. Do not include any extra text, comments, or markdown outside the JSON.
        The JSON object MUST contain exactly these two keys:
        - `"category"`: (string) The determined category (e.g., 'Code', 'Financial', 'Business').
        - `"new_name_suggestion"`: (string or null) A suggested new file name (maximum 7 words, no file extension). If the category is 'Miscellaneous', this value MUST be `null`.

        ---
        File Content to Analyze:
        {content}
        ---
        """
        try:
            # Send the prompt to Ollama API requesting JSON output for easier parsing
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                format='json'  # Request JSON output from Ollama
            )
            import json
            # Parse and return the JSON response from Ollama
            return json.loads(response['message']['content'])
        except Exception as e:
            # On failure, log error and return default category with no suggestion
            print(f"Error communicating with Ollama: {e}")
            return {"category": "Miscellaneous", "new_name_suggestion": None}

    def suggest_rename(self, content: str, current_name: str) -> str:
        """
        Suggest a new, concise, and descriptive file name based on file content.

        Args:
            content (str): The textual content of the file.
            current_name (str): The current file name (without extension) used as fallback.

        Returns:
            str: A suggested new file name (max 7 words, no extension). Returns current_name if unable to suggest.
        """
        prompt = f"""
                You are a file naming assistant. Your goal is to generate a new, highly descriptive, and concise name for a file based on its content.

                **Guidelines:**
                - The new name MUST be no more than 7 words.
                - The new name MUST NOT include any file extension.
                - Focus on the main topic, purpose, or key entities described in the file content.
                - If the content is too generic, short, or does not provide enough information for a meaningful new name, you MAY suggest the provided `current_name`.
                - The output MUST be ONLY the suggested file name. DO NOT include any other text, explanations, or markdown.

                ---
                Current File Name (for context, but focus on content): '{current_name}'
                File Content:
                {content}
                ---
                """
        try:
            # Request a simple text response with the suggested new name
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
            )
            # Return the text content of the response as the new file name suggestion
            return response['message']['content'].strip()
        except Exception as e:
            # On failure, log error and fallback to current name
            print(f"Error suggesting rename with Ollama: {e}")
            return current_name

if __name__ == "__main__":
    # Quick local testing block - can be removed or commented out in production
    ollama_h = OllamaHandler()
    test_content = "This document contains my monthly budget for July 2025, including income and expenses."
    analysis = ollama_h.analyze_content(test_content)
    print(f"Analysis: {analysis}")

    code_content = "def calculate_factorial(n):\n    if n == 0: return 1\n    else: return n * calculate_factorial(n-1)"
    code_analysis = ollama_h.analyze_content(code_content)
    print(f"Code Analysis: {code_analysis}")

    rename_suggestion = ollama_h.suggest_rename(test_content, "budget_doc")
    print(f"Rename Suggestion: {rename_suggestion}")