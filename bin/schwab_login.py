#!/usr/bin/env python3
"""
One-time Schwab OAuth login. Opens a browser; complete the Schwab sign-in there.
The token is saved to data/schwab_token.json and auto-refreshed afterwards.

Usage:
    python bin/schwab_login.py            # First-time login
    python bin/schwab_login.py --force    # Discard an existing (e.g. expired/revoked) token and log in again
"""

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from lib.schwab_client import login, TOKEN_PATH


def main(force=False):
    if os.path.exists(TOKEN_PATH):
        if not force:
            print(f'Token already exists at {TOKEN_PATH} — nothing to do.')
            print('Re-run with --force to discard it and log in again.')
            return
        os.remove(TOKEN_PATH)
        print(f'Removed existing token at {TOKEN_PATH}.')

    login()
    print(f'\nLogin complete. Token saved to {TOKEN_PATH}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='One-time Schwab OAuth login')
    parser.add_argument('--force', action='store_true',
                        help='Discard an existing token and log in again')
    args = parser.parse_args()
    main(force=args.force)
