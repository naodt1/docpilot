# DocPilot

<img src="assets/logo.jpg" alt="DocPilot Logo" width="30" height="30">

**DocPilot is your personal AI-powered document assistant.** It uses a local large language model (LLM) to provide a private and powerful way to interact with your documents, all from the comfort of your desktop.

***

## ✨ Features

* **Local-First AI:** Powered by Ollama, DocPilot runs entirely on your local machine, ensuring your data remains private and secure.
* **Intuitive UI:** An elegant and user-friendly desktop interface built with **Electron**, **JavaScript**, and **Tailwind CSS**.
* **Flexible LLMs:** By default, DocPilot uses the lightweight `phi3` model, but you can easily switch to any other model supported by Ollama (like `mistral`) by simply changing a setting in the backend's config file.
* **Monorepo Structure:** All code is managed in a single repository for a unified development experience.

![App Demo](assets/docpilotgify.gif)

***

## 🚀 Getting Started

### Prerequisites

To run DocPilot, you must have the following installed on your machine:

1.  **[Node.js](https://nodejs.org/)**: Includes `npm`, which is required for the frontend.
2.  **[Python 3.x](https://www.python.org/downloads/)**: Required for the backend.
3.  **[Ollama](https://ollama.com/)**: The core engine for the AI. You must install Ollama and, at a minimum, pull the `phi3` model to get started.

    ```bash
    ollama pull phi3
    ```

### Installation

Follow these steps to get your local copy of DocPilot up and running.

1.  **Clone the Repository**

    ```bash
    git clone [https://github.com/your-username/docpilot.git](https://github.com/your-username/docpilot.git)
    cd docpilot
    ```

2.  **Install Dependencies**

    You need to install dependencies for both the frontend and backend.
    * **Frontend (Electron.js)**

        ```bash
        cd frontend
        npm install
        ```
    * **Backend (Python Flask)**

        ```bash
        cd ../backend
        pip install -r requirements.txt
        ```

3.  **Start the Application**

    Return to the monorepo root directory and run the unified start command.

    ```bash
    cd ..
    npm start
    ```

    This command uses `concurrently` to launch both the Electron frontend and the Flask backend at the same time.

![App Screenshot](assets/screenshot.png)

***

## 💻 Usage

After running `npm start`, the DocPilot desktop application will launch.

1.  **Select a Model:** By default, DocPilot uses `phi3`. To change the model, open the backend's config file and update the model name.
2.  **Load a Document:** Use the app's interface to upload a document.
3.  **Chat:** Begin asking questions about your document, and the local AI will provide answers.

***

## 🛠️ Development

This project uses a monorepo structure. You can manage each part of the application independently.

* To run **only the frontend**: `npm run start-frontend`
* To run **only the backend**: `npm run start-backend`

## 📄 License

This project is licensed under the MIT License.
