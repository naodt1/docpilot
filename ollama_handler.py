# ollama_handler.py
import ollama
from config import OLLAMA_HOST, OLLAMA_MODEL

class OllamaHandler:
    def __init__(self, host=OLLAMA_HOST, model=OLLAMA_MODEL):
        self.client = ollama.Client(host=host)
        self.model = model

    def analyze_content(self, content: str) -> dict:
        """
        Analyzes file content using Ollama to determine its category and suggest a new name.
        """
        # Expanded and refined category rules
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
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                format='json' # Request JSON output from Ollama
            )
            # Ollama's chat response structure: response['message']['content']
            import json
            return json.loads(response['message']['content'])
        except Exception as e:
            print(f"Error communicating with Ollama: {e}")
            return {"category": "Miscellaneous", "new_name_suggestion": None}

    # You might want more specific analysis functions later
    def suggest_rename(self, content: str, current_name: str) -> str:
        """
        Suggests a new name for a file based on its content.
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
            response = self.client.chat(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
            )
            # Ollama's chat response structure: response['message']['content']
            return response['message']['content'].strip()
        except Exception as e:
            print(f"Error suggesting rename with Ollama: {e}")
            return current_name

# Example Usage (for testing)
if __name__ == "__main__":
    ollama_h = OllamaHandler()
    test_content = "This document contains my monthly budget for July 2025, including income and expenses."
    analysis = ollama_h.analyze_content(test_content)
    print(f"Analysis: {analysis}")

    code_content = "def calculate_factorial(n):\n    if n == 0: return 1\n    else: return n * calculate_factorial(n-1)"
    code_analysis = ollama_h.analyze_content(code_content)
    print(f"Code Analysis: {code_analysis}")

    rename_suggestion = ollama_h.suggest_rename(test_content, "budget_doc")
    print(f"Rename Suggestion: {rename_suggestion}")