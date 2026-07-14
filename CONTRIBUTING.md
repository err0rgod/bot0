# Contributing to bot0

First off, thank you for considering contributing to bot0! It's people like you that make open-source tools robust, fun, and powerful.

## How Can I Contribute?

### 1. Reporting Bugs
If you find a bug, please open an issue in the repository. Make sure to include:
- A clear and descriptive title.
- Steps to reproduce the bug.
- Expected behavior vs. actual behavior.
- Logs from your terminal (if applicable, ensuring you redact any sensitive API keys!).

### 2. Suggesting Enhancements
Have an idea to make the AI better? Or maybe a new source for cybersecurity news? We'd love to hear it! Open an issue describing your idea, how it would work, and why it would be beneficial.

### 3. Pull Requests
We actively welcome Pull Requests (PRs). When submitting a PR:
1. **Fork the repository** and create your branch from `main`.
2. **Name your branch appropriately**: e.g., `feature/add-new-rss-feed` or `bugfix/fix-s3-upload-timeout`.
3. **Run the Tests**: Before submitting, make sure you run the test suite locally using `python tests/run_tests.py` and ensure everything passes.
4. **Update Documentation**: If you are adding a new feature or changing the architecture, please update the `README.md` or `documentation.md` as necessary.
5. **Detailed PR Description**: Clearly explain what your PR does. If it solves an open issue, link to it (e.g., "Fixes #12").

## Local Setup
Check the `README.md` for instructions on setting up the project locally. You will need your own API keys for DeepSeek, AWS, and Resend to test end-to-end functionality.

## Code Style
- **Python**: We follow standard PEP 8 conventions. Please ensure your code is clean, readable, and well-commented.
- **Type Hinting**: As the project evolves, we strongly encourage adding Python type hints to any new functions you write.

## Need Help?
If you're stuck or have questions, feel free to open a draft PR or an issue asking for help. We are a welcoming community and are happy to guide you!
