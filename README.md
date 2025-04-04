# EXCEL FILE TRANSLATION TOOL GUIDE

## Introduction

This is an automatic tool for translating Excel file content between Vietnamese and Japanese, using the Gemini API.
This tool can translate text in cells and shapes within Excel files.

## Requirements

1. Python must be installed (Python 3.7 or higher is recommended).
2. Microsoft Excel must be installed (tool uses xlwings library which requires Excel).
3. This tool only works on Windows or macOS (xlwings requires Excel on these platforms).
4. Install the required libraries with the following command:

   ```
   pip install -r trans-excel-requirements.txt
   ```

   (This file will be created automatically when you run the program for the first time)

## API Setup

1. You need a Gemini API key. Save this key in a .env file with the following format:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
2. Place the .env file in the same directory as the trans-excel2.py file

## How to Use

1. Run the trans-excel2.py file for the first time to create the directory structure:

   ```
   python trans-excel2.py
   ```
2. Place the Excel files to be translated in the "input" folder
3. Run the program with optional parameters to specify the target language:

   - Translate from Vietnamese to Japanese (default):
     ```
     python trans-excel2.py --to ja
     ```
   - Translate from Japanese to Vietnamese:
     ```
     python trans-excel2.py --to vi
     ```
4. Translation results will be saved in the "output" folder

## Custom Language Pairs

To translate between languages other than Vietnamese and Japanese, follow these steps:

1. Open the trans-excel2.py file in a text editor
2. Locate the `translate_batch` function (around line 100)
3. Find the following line:
   ```python
   direction = "Vietnamese to Japanese" if target_lang == "ja" else "Japanese to Vietnamese"
   ```
4. Change this line to your desired language pair, for example:
   ```python
   direction = "English to Spanish" if target_lang == "es" else "Spanish to English"
   ```
5. Modify the main function's argument parser to accept your new language codes:
   ```python
   parser.add_argument('--to', choices=['es', 'en'], default='es',
                      help='Target language (es: Spanish, en: English). Default: es')
   ```
6. Update the language display in the program:
   ```python
   print(f"🎯 Target language: {'Spanish' if args.to == 'es' else 'English'}")
   ```
7. Save the file and run with your new language code:
   ```
   python trans-excel2.py --to es
   ```

For optimal translation results, you might also want to modify the default system prompt to specify expertise in your target languages.

## API Performance Customization

The default configuration is set to work with Gemini 2.0 Flash Lite model, which has rate limits in free tier. You can customize these settings based on your API provider and model:

1. **API Delay Adjustment** - The current delay between API calls is set to 2 seconds to avoid hitting rate limits:

   ```python
   # Find this line near the beginning of the script (around line 50)
   API_DELAY = 2  # Delay 2 seconds between API calls
   ```

   - For models with higher rate limits, you can reduce this value
   - For free tier APIs with stricter limits, you might need to increase this value
2. **Batch Size Adjustment** - The default batch size is 100 cells/shapes per API call:

   ```python
   # Find this line near the beginning of the script
   BATCH_SIZE = 100  # Maximum number of cells in a batch
   ```

   - Increase this value for more powerful models that can handle larger contexts
   - Decrease this value if you're getting context length errors or incomplete translations
3. **Using Different API Providers** - You can change the base URL to use other OpenAI-compatible API providers:

   ```python
   # Find this block in the script (around line 40)
   client = OpenAI(
       base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
       api_key=os.getenv("GEMINI_API_KEY"),
   )
   ```

   Examples for different providers:

   - For OpenAI:

     ```python
     client = OpenAI(
         base_url="https://api.openai.com/v1/",
         api_key=os.getenv("OPENAI_API_KEY"),
     )
     ```
   - For Azure OpenAI:

     ```python
     client = OpenAI(
         base_url=f"https://{your_azure_resource}.openai.azure.com/openai/deployments/{your_deployment}/",
         api_key=os.getenv("AZURE_OPENAI_API_KEY"),
         api_version="2023-05-15"
     )
     ```
4. **Model Selection** - Also update the model name to match your chosen provider:

   ```python
   # Find this in the translate_batch function
   model="gemini-2.0-flash-lite"  # Change to your model name
   ```

   Examples:

   - For OpenAI: "gpt-3.5-turbo" or "gpt-4"
   - For Anthropic: "claude-2" or "claude-instant-1"
   - For other providers, refer to their documentation for model names

Remember to update your environment variables in the .env file to match your chosen API provider.

## Customizing System Prompt for Other Industries

The default system prompt is optimized for IT and software development translations. If you need to translate content from other industries, you should customize the system prompt file:

1. Locate the `trans-excel-system-prompt.txt` file in your project directory (it's created automatically after first run)
2. Open it with a text editor
3. Modify the content to match your industry's specific requirements

Here's an example of how to customize the prompt for medical translations:

```
You are a professional medical translator specializing in healthcare, pharmaceuticals, and medical documentation. Follow these rules strictly:

1. Output ONLY the translation, nothing else
2. DO NOT include the original text in your response
3. DO NOT add any explanations or notes
4. Keep IDs, model numbers, and special characters unchanged
5. Use standard medical terminology appropriate for healthcare professionals
6. Preserve the original formatting (spaces, line breaks)
7. Use proper grammar and punctuation
8. Only keep unchanged: proper names, IDs, and medical codes
9. Translate all segments separated by "|||" and keep them separated with the same delimiter

For medical-specific terminology:
- Maintain consistency in medical terms
- Use correct anatomical and pharmaceutical terminology
- Preserve medical measurements, dosages, and units
- Keep drug names in their appropriate format
- Use industry-standard translations for medical concepts
- Preserve medical abbreviations and codes
```

Similarly, you can create custom prompts for other industries like legal, finance, marketing, etc., by adapting the instructions and terminology guidance to the specific field.

## Directory Structure

- /trans-excel2.py: Main program file
- /input/: Directory containing Excel files to be translated
- /output/: Directory containing translated Excel files
- /trans-excel-system-prompt.txt: File containing system prompt (will be created automatically)
- /trans-excel-requirements.txt: File containing library requirements (will be created automatically)
- /.env: File containing API key (needs to be created manually)

## Features

- Translates text content in Excel cells
- Translates text content in shapes such as TextBox, WordArt, etc.
- Preserves the original format of the Excel file
- Skips cells that only contain numbers, formulas, or very short content
- Processes multiple Excel files in a directory

## Notes

- The translation process may take time depending on the amount of content to be translated
- Translation quality depends on the Gemini API
- Do not edit Excel files while the program is running
- Excel must be installed as the tool uses xlwings to interact with Excel files
- The program will briefly open and close Excel in the background while processing files

## Troubleshooting

If you encounter errors:

1. Check if the API key is correctly set up in the .env file
2. Ensure all dependent libraries are installed
3. Check file and directory access permissions
