---
title: INSTALLATION
slug: installation
lang: en
project: Cryptoix-python
domain: https://github.com/Cryptoix-Dev/cryptoix-python
generated_by: agenter
---
## Prerequisites

Before installing the `cryptoix-python` SDK, ensure your development environment satisfies the following requirements:

- **Python Runtime**: Python `3.8` or higher. Verify your installation by running:
  ```bash
  python --version
  ```
- **Package Installer**: `pip` (bundled with modern Python installations) and standard library modules (`venv`).
- **Git**: Required if you plan to install the SDK directly from the source repository.

---

## Standard Package Installation

The `cryptoix-python` SDK is built using modern PEP 517 / PEP 621 packaging standards via the Hatchling backend. You can install the package via `pip` from PyPI or directly from the Git source repository.

### Installing from PyPI

```bash
pip install cryptoix-python
```

### Installing from Git Source

To install the latest development version or a specific branch directly from GitHub:

```bash
pip install git+https://github.com/Cryptoix-Dev/cryptoix-python.git
```

### Basic Verification

Once installed, you can verify that the package is available in your Python environment by running a quick import check:

```python
from cryptoix import CryptoixClient

print("Cryptoix SDK successfully imported.")
```

---

## Development & Editable Installation

If you are contributing to the SDK or wish to run the bundled examples and test suites locally, set up a dedicated virtual environment and install the package in editable mode with development dependencies.

### 1. Create and Activate a Virtual Environment

Navigate to your workspace and create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment:

- **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```
- **Windows (Command Prompt):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

### 2. Install in Editable Mode with Dependencies

From the root directory of the repository (where `pyproject.toml` is located), install the package in editable mode along with its testing and HTTP transport dependencies (`pytest` and `httpx` `>=0.27`):

```bash
pip install --editable .[dev]
```

---

## Verifying Installation

To ensure your development setup and test harness are functioning correctly, run the test suite using `pytest`. The package includes unit tests for client transport behavior, envelope parsing, and webhook signature verification (`tests/test_client.py` and `tests/test_webhooks.py`):

```bash
pytest
```

---

## Security Best Practices

When integrating or developing with `cryptoix-python`, observe the following security guidelines:

1. **API Key Management**: 
   Never hardcode your API keys in source files or check them into version control. The SDK automatically detects the `CRYPTOIX_API_KEY` environment variable if explicit client arguments are omitted:
   ```python
   import os
   from cryptoix import CryptoixClient

   # Automatically picks up CRYPTOIX_API_KEY from the environment
   client = CryptoixClient()
   ```
   For local development, define your key in a local `.env` file or export it in your shell session:
   ```bash
   export CRYPTOIX_API_KEY="cx_live_XXXXXXXXXXXXXXXXXXXXXXXX"
   ```

2. **Constant-Time Webhook Verification**: 
   When handling incoming webhooks from Cryptoix, always use the built-in `verify_webhook_signature` helper from `src/cryptoix/webhooks.py`. This utility leverages `hmac.compare_digest` under the hood to perform constant-time string comparisons, protecting your application endpoints against timing side-channel attacks:
   ```python
   from cryptoix import verify_webhook_signature

   is_valid = verify_webhook_signature(
       payload=request_body_bytes,
       signature_header=request.headers.get("X-Cryptoix-Signature", ""),
       secret=os.environ["CRYPTOIX_WEBHOOK_SECRET"],
   )
   
   if not is_valid:
       raise ValueError("Invalid webhook signature.")
   ```
