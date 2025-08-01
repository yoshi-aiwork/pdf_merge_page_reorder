# 📄 PDF Extract & Merge & Page Reorder Tool

Welcome to the PDF Extract & Merge Tool! This easy-to-use application helps you combine pages from two different PDF files into a single, new PDF. You can select specific pages, arrange them in any order you like, and even give your new PDF a custom filename.

## 💡 Use Case 🐱
Need to add a handwritten ("wet") signature to only the last page of a PDF while preserving lossless PDF integrity?  Print, sign, and merge — without ever touching the other pages.  Here are a few common scenarios:

- Sign‑only the last page of long contractsSkip wasting paper on 20+ pages. Extract the final page, sign it, then merge it back in seconds.

- HR & onboarding paperworkMany HR forms still need a physical signature line. Print just that page, hand‑sign, and keep the file structure intact.
  
## ✨ Features

*   **Upload Two PDFs:** Easily upload your 'PDF A' and 'PDF B' files.
*   **Select Page Ranges:** Choose exactly which pages you want from each PDF using a flexible range syntax (e.g., `1, 3-5, 8`).
*   **Visual Page Preview:** See thumbnails of your selected pages.
*   **Custom Page Ordering:** Define the final sequence of pages using a simple text format (e.g., `A1-3, B5, A10`).
*   **Custom Output Filename:** Name your merged PDF exactly what you want.
*   **Generate & Download:** Create your new PDF with a single click and download it instantly.

## 🚀 Getting Started

Follow these simple steps to get the application up and running on your computer:

### 1. Install Dependencies

First, you need to install the necessary Python libraries. It's recommended to use a virtual environment to keep your project dependencies organized.

```bash
# Create a virtual environment (if you don't have one)
python -m venv venv

# Activate the virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install the required packages
pip install -r requirements.txt
```

### 2. Run the Application

Once the dependencies are installed, you can start the Gradio application:

```bash
python app.py
```

Your web browser should automatically open a new tab with the application interface. If not, copy and paste the URL displayed in your terminal (usually `http://127.0.0.1:7860`) into your browser.

## 💡 How to Use the App

1.  **Upload PDFs:** Click the "Upload" buttons under "PDF A" and "PDF B" to select your source PDF files.
2.  **Enter Page Ranges:** In the textboxes below each PDF upload, specify the pages you want to extract. 
    *   Examples:
        *   `1, 3-5, 8` (pages 1, 3, 4, 5, and 8)
        *   `all` (all pages)
        *   `1-` (from page 1 to the end)
        *   `-5` (from the beginning to page 5)
3.  **Preview Pages:** Click "Preview PDF A" and "Preview PDF B" to see thumbnails of the pages you've selected from each PDF.
4.  **Specify Final Order:** In the "Final Page Order" textbox, define the sequence of pages for your merged PDF. Use `A` for pages from PDF A and `B` for pages from PDF B, followed by the page number or range.
    *   Example: `A1-3, B5, A10, B2-4` (pages 1-3 from PDF A, page 5 from PDF B, page 10 from PDF A, pages 2-4 from PDF B).
5.  **Preview Final Order:** Click "Preview Final Order" to see the thumbnails arranged in your specified sequence.
6.  **Output Filename:** Enter your desired name for the merged PDF in the "Output Filename" textbox (e.g., `my_merged_document.pdf`).
7.  **Generate PDF:** Click the "Generate PDF" button. The merged PDF will appear as a downloadable file below the button.

Enjoy merging your PDFs!
