import os
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

class Translator:
    def __init__(self, model_type="gemini"):
        # Load environment variables
        load_dotenv()
        
        self.model_type = model_type
        if model_type == "gemini":
            self.client = OpenAI(
                api_key=os.getenv("GEMINI_API_KEY"),
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            )
            self.model_name = "gemini-2.5-flash"
        else:  # OpenAI GPT
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url="https://api.openai.com/v1/"
            )
            self.model_name = "gpt-3.5-turbo"
            
        self.batch_size = 100
        self.api_delay = 2

    def translate_batch(self, texts: list, target_lang: str) -> list:
        """Translate a batch of texts"""
        if not texts:
            return []

        # Read system prompt from file
        script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        prompt_file = os.path.join(script_dir, "trans-excel-system-prompt.txt")
        
        # Check if the prompt file exists
        if os.path.exists(prompt_file):
            with open(prompt_file, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
        else:
            system_prompt = self._get_default_prompt()
            # Create default prompt file
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(system_prompt)
            print(f"📝 Default prompt file created at: {prompt_file}")

        # Use a more unique separator to avoid conflicts
        separator = "▼▲▼SPLIT_HERE▼▲▼"
        # Clean texts to avoid separator conflicts
        cleaned_texts = [text.replace(separator, " ") for text in texts]
        combined_text = separator.join(cleaned_texts)

        # Updated translation direction logic
        if target_lang == "en":
            direction = "Vietnamese to English"
        elif target_lang == "ja":
            direction = "Vietnamese to Japanese"
        elif target_lang == "vi":
            direction = "Japanese to Vietnamese"
        else:
            # Default fallback for unexpected target languages
            direction = f"to {target_lang}"
            
        user_prompt = f"Translate the following text from {direction}, keeping segments separated by '{separator}':\n\n{combined_text}"

        try:
            # Call translation API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
            )
            
            # Split translation result
            translated_text = response.choices[0].message.content
            if not translated_text:
                print("❌ Empty response from translation API")
                return texts

            translated_parts = translated_text.split(separator)

            # Handle mismatched parts with better error recovery
            if len(translated_parts) != len(cleaned_texts):
                print(f"⚠️ Number of translated parts ({len(translated_parts)}) doesn't match number of original texts ({len(cleaned_texts)})")
                
                # Try to fix common issues
                if len(translated_parts) == 1 and len(cleaned_texts) > 1:
                    # AI returned everything as one block, try to split by common patterns
                    single_text = translated_parts[0]
                    # Try splitting by double newlines first
                    parts = [p.strip() for p in single_text.split('\n\n') if p.strip()]
                    if len(parts) != len(cleaned_texts):
                        # Try splitting by single newlines
                        parts = [p.strip() for p in single_text.split('\n') if p.strip()]
                    
                    if len(parts) == len(cleaned_texts):
                        translated_parts = parts
                        print("✅ Successfully recovered translation structure")
                    else:
                        # Last resort: return original texts
                        print("❌ Could not recover translation structure, returning original texts")
                        return texts
                        
                elif len(translated_parts) < len(cleaned_texts):
                    # Fill missing parts with original text
                    translated_parts.extend(texts[len(translated_parts):])
                    print(f"⚠️ Filled {len(texts) - len(translated_parts)} missing translations with original text")
                else:
                    # Trim excess parts
                    translated_parts = translated_parts[:len(cleaned_texts)]
                    print(f"⚠️ Trimmed {len(translated_parts) - len(cleaned_texts)} excess translations")

            # Delay to avoid API limits
            time.sleep(self.api_delay)
            return translated_parts

        except Exception as e:
            print(f"❌ Translation error: {str(e)}")
            return texts

    def _get_default_prompt(self) -> str:
        """Get default system prompt"""
        return """You are a professional academic and technical translator. Follow these rules strictly:
                1. Output ONLY the translation, nothing else
                2. DO NOT include the original text in your response
                3. DO NOT add any explanations or notes
                4. Keep IDs, model numbers, and special characters unchanged
                5. Use formal, academic language and technical terminology
                6. Maintain academic writing style and formal tone
                7. Use standard technical and scientific terminology
                8. Preserve technical accuracy in translations
                9. Keep mathematical and scientific notations unchanged
                10. Use proper academic/technical formatting
                11. Translate all segments separated by "▼▲▼SPLIT_HERE▼▲▼" and keep them separated with the EXACT same delimiter
                12. For technical terms, use industry-standard translations
                13. Maintain formal register and professional tone throughout
                14. CRITICAL: You must output exactly the same number of segments as the input, separated by the delimiter
                15. Do not merge segments or split them differently than the input"""