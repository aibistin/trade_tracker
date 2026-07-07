#!/usr/bin/env python3
"""
One-time Schwab OAuth login. Opens a browser; complete the Schwab sign-in there.
The token is saved to data/schwab_token.json and auto-refreshed afterwards.

Usage:
    python bin/schwab_login.py
"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from lib.schwab_client import login, TOKEN_PATH

if __name__ == '__main__':
    if os.path.exists(TOKEN_PATH):
        print(f'Token already exists at {TOKEN_PATH} — nothing to do.')
        print('Delete it and re-run this script if you need to re-authenticate.')
        sys.exit(0)
    login()
    print(f'\nLogin complete. Token saved to {TOKEN_PATH}')
