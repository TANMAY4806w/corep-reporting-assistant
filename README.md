# COREP Reporting Assistant

**Professional regulatory reporting automation for UK Banks**

A prototype LLM-assisted regulatory reporting tool focused on COREP template C 01.00 (Own Funds). The system extracts capital and own funds data from natural language scenarios and maps them to structured COREP reporting fields.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.30+-red.svg)

## 🎯 Features

- **Hybrid Input Processing**: Supports both narrative scenarios and raw numerical values
- **Auto-mapping**: Numeric inputs automatically mapped to R010 (Common Equity Tier 1 Capital)
- **LLM-Powered Extraction**: Uses Google Gemini 2.0 Flash for intelligent field extraction
- **Professional UI**: Clean Slate/Neutral color palette with dark/light mode support
- **Audit Trail**: Expandable justification log with PRA Rulebook references
- **Schema-Driven**: Structured validation using COREP template definitions

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/corep-reporting-assistant.git
   cd corep-reporting-assistant
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key**
   
   Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

5. **Run the application**
   ```bash
   streamlit run src/app.py
   ```

6. **Open your browser**
   
   Navigate to `http://localhost:8501`

## 📖 Usage

### Numeric Input Mode
Enter a single numerical value to auto-map to Common Equity Tier 1 Capital (R010):

```
50000000
```

### Narrative Input Mode
Describe the scenario in natural language for full extraction:

```
The bank has £50m in Common Equity Tier 1 Capital and £20m in retained earnings
```

## 🏗️ Project Structure

```
corep-reporting-assistant/
├── data/
│   ├── pra_rules_subset.txt    # PRA Rulebook excerpts
│   └── schema.json              # COREP C 01.00 template schema
├── src/
│   ├── engine.py                # Core processing engine
│   └── app.py                   # Streamlit UI
├── requirements.txt             # Python dependencies
├── .env                         # API configuration (not in repo)
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🎨 UI Features

- **Professional Slate Color Palette**: Consistent neutral tones in light and dark modes
- **Responsive Layout**: Two-column design for input and results
- **Currency Formatting**: Proper £ symbol and thousands separators
- **Expandable Audit Log**: Detailed justification with regulatory references
- **Aggregate Metrics**: Total capital and field count displays

## 🔧 Technology Stack

- **Backend**: Python 3.x
- **LLM**: Google Gemini 2.0 Flash
- **UI Framework**: Streamlit
- **Data Processing**: Pandas
- **Styling**: Custom CSS (Slate palette)

## 📋 COREP Template Coverage

Currently supports **C 01.00 (Own Funds)** with the following fields:

- **R010**: Common Equity Tier 1 Capital
- **R130**: Retained Earnings
- **R180**: Accumulated other comprehensive income

## 🔐 Security Notes

- Never commit your `.env` file or API keys to Git
- The `.gitignore` file is configured to exclude sensitive data
- For production deployment, use Streamlit Cloud secrets management

## 🚀 Deployment

### Streamlit Cloud (Recommended)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Add your `GEMINI_API_KEY` to Streamlit secrets
5. Deploy!

### Local Deployment

```bash
streamlit run src/app.py --server.port 8501
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

This is a prototype for demonstration purposes. For production use, please ensure:

- Comprehensive testing with real COREP data
- Additional template coverage (C 02.00, C 03.00, etc.)
- Enhanced validation rules
- Multi-user authentication
- Audit trail persistence

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Note**: This is a prototype for educational and demonstration purposes. It is not intended for production regulatory reporting without proper validation and compliance review.
