#!/usr/bin/env bash
set -e
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
echo ""
echo "Setup complete. Start the app with:  source venv/bin/activate && python run.py"
