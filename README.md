# 🛡️ ZeroDaily

![ZeroDaily Banner](https://img.shields.io/badge/Status-Active-success) ![Python](https://img.shields.io/badge/Python-3.11+-blue.svg) ![AWS](https://img.shields.io/badge/Deployed-AWS%20Lambda-orange.svg) ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

**ZeroDaily** is an autonomous, AI-driven cybersecurity newsletter engine. It constantly monitors the web for the latest zero-day vulnerabilities, data breaches, and tech news, uses Large Language Models (LLMs) to generate deep technical summaries (and hilarious, brutal "roasts" of bad security practices), and dispatches them directly to subscribers via email.

---

## ✨ Features

- **🧠 AI-Powered Summarization:** Uses DeepSeek models to break down complex cybersecurity articles into short, readable summaries and deep-dive technical insights.
- **🔥 Automated Security Roasts:** The AI generates punchy 3-4 line roasts for top security failures and breaches of the day, giving your newsletter a unique edge.
- **⚡ Fully Serverless:** Runs 100% autonomously in the cloud via AWS Lambda, scaling instantly with zero maintenance.
- **☁️ Cloud Storage & State:** Stores historical issues in AWS S3 and utilizes AWS DynamoDB to enforce idempotency (ensuring subscribers never receive the same email twice).
- **🛡️ Quality Controlled:** Features built-in tests, HTML-filtering algorithms, and duplicate detection (difflib) to guarantee high-quality outputs.
- **📬 One-Click Dispatch:** Integrates with the Resend API to blast newsletters out seamlessly and dodge spam filters.

---

## 🚀 Getting Started Locally

Want to run the ZeroDaily engine on your local machine? It's easy to spin up!

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/zerodaily-bot.git
cd zerodaily-bot
```

### 2. Install Dependencies
Make sure you have Python 3.11+ installed.
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory based on the following template:
```env
DEEPSEEK_API_KEY=your_deepseek_api_key
RESEND_API_KEY=your_resend_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=ap-south-2
S3_BUCKET_NAME=zeroday-scraped-content-prod-your-id
DYNAMODB_TABLE_NAME=zeroday-subscribers
```

### 4. Run the Pipeline!
To manually trigger the scraper, LLM processing, and generation pipeline locally:
```bash
python scraper/v2.py
```
*(Note: If you want to test the entire email dispatch, run `python automation/send_newsletter.py` after the scrape is finished.)*

---

## 🧪 Running Tests
We enforce strict CI/CD pipelines to ensure stability. To run the full test suite locally:
```bash
python tests/run_tests.py
```
This tests everything from our AWS S3 mocking to our AI content sanitizers.

---

## 📖 Documentation & Technical Specs

Want to know exactly how the engine works under the hood? 
We have documented the **entire** architecture (including our prompt engineering, geometric exponential backoffs, and AWS event structures).

👉 **[Read the Full Technical Documentation here](documentation.md)**

---

## 🤝 Contributing

We welcome contributions! Whether you want to add a new RSS feed, tweak the LLM prompt, or optimize our AWS Lambda deployments, your help is appreciated.

Please see our **[CONTRIBUTING.md](CONTRIBUTING.md)** for detailed instructions on how to get started, branch naming conventions, and pull request guidelines.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
