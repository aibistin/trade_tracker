"""
Schwab API client factory using schwab-py.

Setup (one-time interactive browser login):
    python -c "from lib.schwab_client import login; login()"

After initial login the token is saved to data/schwab_token.json and
refreshed automatically on subsequent calls.

Required environment variables:
    SCHWAB_API_KEY     — App key from developer.schwab.com
    SCHWAB_APP_SECRET  — App secret from developer.schwab.com
    SCHWAB_CALLBACK_URL — Callback URL registered with the app (default: https://127.0.0.1:8182)
"""

import logging
import os

log = logging.getLogger(__name__)

TOKEN_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'schwab_token.json')
TOKEN_PATH = os.path.normpath(TOKEN_PATH)

_CALLBACK_DEFAULT = 'https://127.0.0.1:8182'


def _credentials():
    api_key = os.environ.get('SCHWAB_API_KEY', '')
    app_secret = os.environ.get('SCHWAB_APP_SECRET', '')
    callback_url = os.environ.get('SCHWAB_CALLBACK_URL', _CALLBACK_DEFAULT)
    if not api_key or not app_secret:
        raise EnvironmentError(
            'SCHWAB_API_KEY and SCHWAB_APP_SECRET must be set in the environment.'
        )
    return api_key, app_secret, callback_url


def get_client():
    """Return an authenticated schwab client, loading from the saved token file."""
    import schwab
    api_key, app_secret, _ = _credentials()
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(
            f'Schwab token not found at {TOKEN_PATH}. Run `python -c "from lib.schwab_client import login; login()"` first.'
        )
    return schwab.auth.client_from_token_file(TOKEN_PATH, api_key, app_secret)


def login(interactive=False):
    """One-time OAuth browser login. Saves token to TOKEN_PATH.

    interactive=False skips schwab-py's "press ENTER" stdin prompts so the
    flow works when stdin is not a TTY; the browser opens automatically.
    """
    import schwab
    api_key, app_secret, callback_url = _credentials()
    log.info(f'Starting Schwab OAuth login flow. Callback URL: {callback_url}')
    client = schwab.auth.client_from_login_flow(
        api_key=api_key,
        app_secret=app_secret,
        callback_url=callback_url,
        token_path=TOKEN_PATH,
        interactive=interactive,
    )
    log.info(f'Login successful. Token saved to {TOKEN_PATH}')
    return client
