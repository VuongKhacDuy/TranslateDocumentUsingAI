.PHONY: setup run run-ja run-vi clean help init-env

help:
	@echo "Available commands:"
	@echo "  make setup    - Install required dependencies"
	@echo "  make init-env - Create .env file (requires GEMINI_API_KEY input)"
	@echo "  make run      - Run with default settings (Vietnamese to Japanese)"
	@echo "  make run-ja   - Run translation to Japanese"
	@echo "  make run-vi   - Run translation to Vietnamese"
	@echo "  make clean    - Clean up generated files"

setup-env:
	@if not exist .env (echo Creating .env file... && \
		echo LLM_MODEL=deepseek-coder-33b-instruct > .env && \
		echo OPENAI_API_KEY=your_openai_key_here >> .env && \
		echo GEMINI_API_KEY=your_google_key_here >> .env && \
		echo DEEPSEEK_API_KEY=your_deepseek_key_here >> .env && \
		echo HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here >> .env && \
		echo VECTOR_DB_TYPE=chroma >> .env && \
		echo VECTOR_DB_PATH=./data/vectordb >> .env && \
		echo DEBUG=True >> .env && \
		echo LOG_LEVEL=INFO >> .env && \
		echo .env file created successfully!) else (echo .env file already exists, skipping creation...)

setup: setup-env
	@echo "Setting up virtual environment..."
	python -m venv venv
	@echo "Activating virtual environment and installing dependencies..."
	.\venv\Scripts\activate && python.exe -m pip install --upgrade pip && pip install -r trans-excel-requirements.txt
	@echo "Setup complete! Remember to activate the virtual environment before running:"
	@echo "  .\venv\Scripts\activate"

run:
	@echo "IMPORTANT: Make sure you have activated the virtual environment!"
	@echo "To activate: .\venv\Scripts\activate"
	@echo "Starting Streamlit application..."
	.\venv\Scripts\activate && streamlit run src/presentation/streamlit_app.py

run-ja:
	@echo "IMPORTANT: Make sure you have activated the virtual environment!"
	@echo "To activate: .\venv\Scripts\activate"
	@echo "Starting Streamlit application..."
	.\venv\Scripts\activate && streamlit run src/presentation/streamlit_app.py

run-vi:
	@echo "IMPORTANT: Make sure you have activated the virtual environment!"
	@echo "To activate: .\venv\Scripts\activate"
	@echo "Starting Streamlit application..."
	.\venv\Scripts\activate && streamlit run src/presentation/streamlit_app.py

clean:
	@if exist "output\*" del /Q "output\*"
	@if exist "__pycache__" rmdir /S /Q "__pycache__"
	@if exist ".env" del /Q ".env"