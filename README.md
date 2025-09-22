# Credit Risk Analysis with AI


This project is a **Streamlit application** for AI-powered credit risk analysis based on financial data.  
It allows users to upload Excel files, process key financial indicators, and automatically generate comments and reports that support credit risk assessment and decision-making.

---

## Features
- Automated extraction of key financial indicators (e.g., revenues, EBITDA, capital, payment delays)  
- Credit risk assessment supported by AI methods  
- Generation of concise and structured credit risk reports  
- Configurable thresholds and parameters for risk evaluation  

---

## Installation
Clone the repository and install dependencies:

```bash
git clone https://github.com/stevanoem/dts-fin-app
cd dts-fin-app
pip install -r requirements.txt
```

---

## Usage
Run the Streamlit app:
```bash
streamlit run app.py
```
Once started, open the local URL shown in the terminal (default: http://localhost:8501) in your browser.

---

## Project Structure
```bash
.
├── app.py                  # Main Streamlit app
├── comment_generator.py     # AI-based credit risk comment generation
├── excel_processor.py       # Excel file parsing and feature extraction
├── google_drive_utils.py    # Google Drive integration
├── requirements.txt         # Dependencies
├── .env                     # Environment variables (e.g., API keys)
├── .streamlit/secrets.toml  # Streamlit secrets configuration
├── inputs/                  # Uploaded Excel files
├── output/                  # Processed data and generated comments
├── notebooks/               # Jupyter notebooks for testing/analysis
├── temp_uploaded_files/     # Temporary storage of uploaded files
└── README.md                # Project documentation
```

## Configuration
- Store sensitive credentials (API keys, Google Drive config) in .env or .streamlit/secrets.toml.
- Place Excel files in the inputs/ directory or upload them directly via the app interface.
- Generated results (JSON files and AI comments) will be saved in the `output/` folder **and the analysis results will also be displayed directly on the web interface**.

## Authors
AI Champions Team – Delta Holding