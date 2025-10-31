import os
import sys

# Replicate the path logic from streamlit_app.py
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print("project_root:", project_root)

# Check if the translation_service.py file exists at the expected path
expected_path = os.path.join(project_root, "src", "application", "translation_service.py")
print("expected_path:", expected_path)
print("File exists:", os.path.exists(expected_path))

# Print sys.path
print("sys.path[:5]:", sys.path[:5])