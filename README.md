# HTML Knowledge Base Reformatting Script

This project provides a Python script to clean, restructure, and reformat HTML files.

The script performs operations such as:
* Standardizing image tags and `src`/`alt`/`title` attributes based on preceding step headers.
* Converting textual warnings/tips/notes into proper `div` containers with appropriate classes.
* Formatting "Required Supplies" sections into a two-column grid layout.
* Converting "Step X: Title" paragraphs/headers into standard `<h3>` tags.
* Applying general clean-up (removing unnecessary attributes, empty tags, and standardizing whitespace).

---

### Prerequisites

You need **Python 3.x** installed on your system.

### Installation

Install the necessary dependencies using `pip`. The script relies on the `BeautifulSoup` library for HTML parsing and manipulation.

```bash
pip install beautifulsoup4
```

### How to Run

1. Locate your HTML files and place them in a single directory to be processed. 
2. Open 'main.py' and modify the 'input_folder' in the main function to point ot hte directory containing your input HTML file. (Line 38)
* input_folder = "/path/to/your/html/files"
3. Run main.py on your terminal : 

```bash
python3 main.py
```


