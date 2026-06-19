#!/bin/bash
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "Starting the AI Personal Assistant..."
streamlit run src/core/ui.py