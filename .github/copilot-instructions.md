# AI Coding Agent Instructions

## Project Overview
This is a **multi-modal document translation service** supporting Excel, PDF, Word, and CSV files using AI translation APIs (Gemini/GPT). The system uses **Clean Architecture** with domain-driven design patterns and provides both Streamlit web UI and command-line interfaces.

## Architecture & Core Patterns

### Clean Architecture Layers
- **Domain** (`src/domain/`): Core business logic - `Translator` class handles API abstraction
- **Application** (`src/application/`): Use cases - `TranslationService` orchestrates file processing  
- **Infrastructure** (`src/infrastructure/`): External concerns - `FileHandler` manages I/O operations
- **Presentation** (`src/presentation/`): UI layer - Streamlit app with modular pages

### Key Design Decisions
- **API Abstraction**: Single `Translator` class supports multiple providers (Gemini, OpenAI) via OpenAI-compatible interface
- **Batch Processing**: Text extraction → batch translation → content replacement preserves formatting
- **File Format Preservation**: Uses `xlwings` for Excel, maintains original formatting while updating content
- **Separator Pattern**: Uses `|||` delimiter for batch translations to maintain text boundaries

## Critical Developer Workflows

### Setup & Environment
```bash
make setup          # Creates venv, installs deps, sets up .env template
make run            # Launches Streamlit app on localhost:8501
```

### API Configuration
- **Gemini**: `GEMINI_API_KEY` in `.env` → uses Google's OpenAI-compatible endpoint
- **OpenAI**: `OPENAI_API_KEY` in `.env` → standard OpenAI API
- **System Prompts**: Customizable via `trans-excel-system-prompt.txt` (auto-generated)

### File Processing Pipeline
1. Upload → `FileHandler.save_uploaded_file()` 
2. Extract → `FileHandler.extract_text()` (format-specific extractors)
3. Translate → `Translator.translate_batch()` (batch API calls with rate limiting)
4. Save → `TranslationService._save_translated_content()` (preserves formatting)

## Project-Specific Conventions

### File Handling Patterns
- **Excel Processing**: Always use `xlwings.App(visible=False)` with proper cleanup in try/finally
- **Batch Size**: Default 100 items per API call (`self.batch_size = 100`)
- **Rate Limiting**: 2-second delays between API calls (`self.api_delay = 2`)
- **Path Management**: Input files → `input/`, outputs → `output/` with `-translated` suffix

### Translation Flow
```python
# Standard translation pattern
texts = self.file_handler.extract_text(input_path)
translated_texts = self.translator.translate_batch(texts, target_lang)
self._save_translated_content(input_path, output_path, translated_texts)
```

### Error Handling Strategy
- **Graceful Degradation**: API failures return original text
- **Excel Dependencies**: Requires Microsoft Excel on Windows/macOS (xlwings limitation)
- **File Conflicts**: Auto-handles existing files with overwrite logic

## Language & Model Support

### Supported Languages
- `"vi"` → Vietnamese
- `"ja"` → Japanese  
- `"en"` → English

### Model Configuration
```python
# Gemini (default)
model_type="gemini" → "gemini-2.5-flash-preview-05-20"
# OpenAI
model_type="gpt" → "gpt-3.5-turbo"
```

## Integration Points

### Streamlit Architecture
- **Main App**: `src/presentation/streamlit_app.py` (signal handling, session state)
- **Page Modules**: `src/presentation/pages/` (file_translation.py, text_translation.py)
- **State Management**: Uses `st.session_state` for navigation

### External Dependencies
- **xlwings**: Excel manipulation (requires Excel installation)
- **PyPDF2**: PDF text extraction
- **python-docx**: Word document processing
- **pandas**: CSV handling
- **streamlit**: Web interface

### System Prompt Customization
Located at `trans-excel-system-prompt.txt` - customizable for different domains (IT, medical, legal, etc.). Auto-generated on first run with IT/software focus.

## Key Files to Reference
- `src/domain/translator.py` - API abstraction and batch processing logic
- `src/application/translation_service.py` - Main orchestration workflow
- `src/infrastructure/file_handler.py` - Format-specific text extraction patterns
- `Makefile` - Standard development commands and environment setup