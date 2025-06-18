# 🏗️ Bridge Deck Content Extraction

AI-powered pipeline for extracting structured bridge design data from engineering drawings and PDFs using Azure Document Intelligence and GPT-based vision models. Designed to support infrastructure engineering workflows at scale — such as bridge superstructure analysis, bid tab matching, and DOT compliance reviews.

---

## 🔍 Overview

This tool automates the extraction of critical engineering data — such as span lengths, girder spacing, deck widths, clearances, and diagram references — from bridge deck PDFs and images.

It uses:
- 📄 Azure Document Intelligence (Form Recognizer) for OCR and layout-aware text extraction
- 🤖 Azure OpenAI with GPT for reasoning and structured value extraction
- ⚙️ Promptflow orchestration for scalable execution and prompt injection

---

## 🧱 Architecture
```
Bridge Deck PDF/Image
        ↓
Azure Document Intelligence (OCR)
        ↓
Image Crops + Text
        ↓
Prompt Template (Jinja2)
        ↓
Azure OpenAI (GPT-4 Vision)
        ↓
Extracted JSON Values
        ↓
Downstream Use (analysis, matching, UI, etc.)
```

---

## 📦 Repository Structure

```
content-extraction-aecom/
├── content_extraction_deckSection.py        # Main pipeline tool
├── diagram_selection.py                     # Diagram extraction module
├── parse_doc_intelligence.py                # Azure OCR parser
├── file_processing.py                       # Pre/post-processing utilities
├── flow.dag.yaml                            # Promptflow DAG config
├── credentials.env                          # Azure/OpenAI credentials
├── prompts/
│   ├── system_prompt_content_extraction.jinja2
│   ├── system_prompt_diagram_selection.jinja2
│   └── few_shot_prompt_image.jinja2
└── input/
    └── few_shots/
        └── deck_section/
            └── example.pdf.jpg
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/bridge-deck-content-extraction.git
cd bridge-deck-content-extraction
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Credentials
Create a `.env` file or use `credentials.env` to set:

```env
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_MODEL=gpt-4-vision
```

---

## 🚀 Usage (via Promptflow)

The main tool is `content_extraction_deckSection.py`, which can be triggered inside a Promptflow DAG or manually.

### Example function call:
```python
from content_extraction_deckSection import content_extraction

output = content_extraction(
    images_meta={
        "bridge_number": "PI-123456",
        "images_metadata_cropped": [...]
    },
    system_prompt=rendered_prompt,
    few_shot_prompt=example_prompt,
    page_text="OCR text from Doc Intelligence"
)
```

---

## 📤 Output Format

Returns structured data with confidence annotations:

```json
{
  "SPAN": [{"Value": ["30ft", "45ft"], "ConfidenceLevel": "High"}],
  "GIRD_SPACE": [{"Value": "4.2m", "ConfidenceLevel": "Medium"}],
  "D_WIDTH": [{"Value": "12.5m", "ConfidenceLevel": "High"}],
  ...
}
```

---

## 🛠️ Use Cases

- Match bridge designs to prior bid tabs
- Pre-populate forms for structural engineering review
- Automate extraction from DOT deck submissions
- Enable search, filtering, and data mining of bridge plans

---

## 🤝 Contributors

- **Prince Crentsil** – Microsoft AI Engineer & Infra AI Specialist  
- In partnership with **AECOM** and **Department of Transportation** workflows

---
