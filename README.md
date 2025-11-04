# Gamma Text Extractor (OCR) — README

This tool extracts text from instrument-cluster label images using **Mistral OCR**, compares it
against ground-truth strings stored in *Gamma* CSVs, and writes a per-image comparison report.

---

## 🧩 Problem Statement

Given:
- A set of **PNG images** named like `TXTALT_<BUIC_ID>_<INDEX>_<LANG>.png` (e.g., `TXTALT_10202_3_FR.png`),
- A **variant** that maps to a specific *Gamma* CSV (e.g., `Gamma_2x32.csv`),
- And optional **language selection**,

the tool should:
1. OCR each image via **Mistral OCR** (or a placeholder local OCR).
2. Find the **BUIC Id** row in the appropriate Gamma CSV.
3. Collect the **expected text** for the relevant language columns (e.g., `fr1`, `fr2` → combined).
4. Normalize OCR text to a single line and **compare** (exact substring check).
5. Write a results CSV with per-language **Expected / Extracted / Result** columns.
6. Add a **final row** with **per-language mismatch counts**.
7. **Do not skip** special cases; instead record:
   - Size mismatch → *Extracted*: `Faulty image`, *Result*: `FAIL`
   - Dynamic input `{#1}`/`(#1)` → *Extracted*: `dynamic input`, *Result*: `SKIP`

---

## 🛠️ Approach (Pipeline)

1. **Config & Inputs**
   - Read `config.txt` for: `variant`, `language`, `input_image_size`, `image_dir`, `output_dir`.
   - Read `api_key.txt` (optional). If missing, fallback to `local_ocr.py` (placeholder).

2. **Variant → Gamma CSV**
   - `var_ref.py` maps variants to a *Gamma* CSV inside `./gamma-master/`.

3. **Image Validation**
   - Image size must match `input_image_size` within **±2%** tolerance. If not → mark *Faulty image*.

4. **Expected Text**
   - From the Gamma CSV row where first column equals **BUIC Id**.
   - Selected languages:
     - If `language` is set in config and **not** `all` → only those columns (e.g., `fr*`).
     - If `language = all` → collect all language prefixes (e.g., `fr*`, `ar*`, …).
     - Else → language is inferred from **image name** (suffix like `_FR.png`).
   - If a language has multiple columns (e.g., `fr1`, `fr2`) → **combine in order** to one string.

5. **OCR**
   - If API key is present → call **Mistral OCR REST API** with base64-encoded image:
     - Endpoint: `POST https://api.mistral.ai/v1/ocr`
     - Model: `mistral-ocr-2505` (or `mistral-ocr-latest`)
     - Response shape: `{"pages": [{"markdown": "..."}], ...}`
   - Else → use `local_ocr.py` (currently returns a dummy string).

6. **Comparison**
   - OCR text is flattened to **one line** (newlines collapsed).
   - Comparison uses `combined_expected in extracted_text` (substring containment).

7. **Output**
   - Writes `{variant}_ocr_results.csv` into `output/`.
   - If a file with same name exists, appends **(1)**, **(2)**, … automatically.
   - Final row shows **per-language** mismatch counts under each `XX Result` column.

---

## 📁 Repository Structure

```
gamma-master/         # Folder with Gamma CSVs (e.g., Gamma_2x32.csv)
input/                # Input images (PNG) to OCR
output/               # OCR comparison CSVs (auto-created)
api_key.txt           # One-line Mistral API key (optional)
api_ocr.py            # Cloud OCR (Mistral) client
config.txt            # Run configuration
local_ocr.py          # Placeholder local OCR
main.ipynb            # Notebook entry (convertible to main.py)
requirements.txt      # Python dependencies
var_ref.py            # Variant → Gamma CSV mapping
```

> **Note:** If your file is named `var_refer.py`, either rename it to `var_ref.py` or update the import path in code.

---

## ⚙️ Configuration — `config.txt`

Example:
```
variant = C1AHSEVO_AMDC
language = fr
input_image_size = 707x79
image_dir = input
output_dir = output
```

- `language`:
  - `fr` (or any two-letter prefix) → only that language is evaluated.
  - `all` → every language present in the CSV is evaluated.
  - not set → language inferred from the **image filename** suffix (e.g., `_FR.png` → `fr`).

---

## 🔤 Filename Convention

`TXTALT_<BUIC_ID>_<INDEX>_<LANG>.png`  
Example: `TXTALT_10202_3_FR.png` → BUIC Id = `10202_3`, language = `fr`.

---

## 🧪 Output CSV Layout (example)

Columns (dynamic):
```
Id, fr Expected, fr Extracted, fr Result, ar Expected, ar Extracted, ar Result, ...
```

- Final row:
  - `Id = Total Mismatches`
  - Under each `XX Result` → number of **FAIL** cases for that language.

Special cases:
- Size mismatch → `Extracted = "Faulty image"`, `Result = FAIL`.
- `{#1}` / `(#1)` present in any sub-column → `Extracted = "dynamic input"`, `Result = SKIP`.

---

## 🧩 Libraries Used & Why

- **pandas** — CSV loading/filtering and easy row/column manipulation.
- **Pillow (PIL)** — Open images and validate dimensions.
- **requests** — Call Mistral OCR REST API with base64-encoded images.
- **re / csv / os / ast** — Standard library helpers for parsing, file ops, and safe `var_ref.py` eval.

*(Optional dev tools: `pyinstaller` for packaging an EXE.)*

---

## 📈 Result

- Produces a consolidated CSV per run in `output/`, reporting per-image comparisons.
- Handles multi-line OCR and multi-column languages.
- Logs size mismatches and dynamic text placeholders without skipping them.
- Appends numeric suffix to avoid overwriting previous runs.

---

## ▶️ How to Run

1. **Create and activate a virtual environment (recommended)**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add your Mistral API key (optional)**
   - Create a file `api_key.txt` with one line:
     ```
     YOUR_MISTRAL_API_KEY
     ```
   - If omitted, the tool uses `local_ocr.py` (dummy OCR).

4. **Prepare inputs**
   - Place PNG images in `input/`.
   - Ensure the required *Gamma* CSV is present in `gamma-master/`.
   - Set `config.txt` correctly.

5. **Run (from notebook or converted script)**
   - Open `main.ipynb` and run all cells **or** convert to a script:
     ```bash
     jupyter nbconvert --to python main.ipynb
     python main.py
     ```

---

## 🐞 Troubleshooting

- **404 from OCR API** — use endpoint `POST https://api.mistral.ai/v1/ocr`.
- **Wrong dimensions** — check `input_image_size` in `config.txt`; tool allows ±2% tolerance.
- **No matching BUIC Id** — ensure the first column of Gamma CSV contains `BUIC Id` values like `10202_3`.
- **No language columns** — ensure columns like `fr1`, `fr2`, `ar1` exist in the Gamma CSV.
- **Response parsing** — OCR returns text in `response["pages"][i]["markdown"]`; the tool flattens to one line.

---

## 🔒 Notes

- The tool doesn’t upload data anywhere except to the OCR API (when API key is given).
- If your data is sensitive, use the **local OCR** path or add an on-prem OCR in `local_ocr.py` later.

---

## 🧑‍💻 Author

Developed by **Kanishk Mishra**  
*Former* AI Intern at **RNTBCI (Renault Nissan Technology & Business Centre India)**  
Focus: *AI for Automotive Test Automation & Validation*

---

## 📄 License

Licensed under the **MIT License** — free to use, modify, and distribute with attribution.

