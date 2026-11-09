# Data Science Project Template

**Group Name:** [Your Group Name]  
**Authors:** Author 1, Author 2, Author 3

The project template was initially developed by [Ilia Azizi](https://iliaazizi.com/) with [main source here](https://github.com/Unco3892/datascience-template).

We use [Quarto](https://quarto.org/) for the template, which starts from a single `report.qmd` file and can give several outputs:

- 🌐 HTML report called `report.html`
- 📑 PDF report called `report.pdf`
- 📝 Microsoft Word report called `report.docx` (you can also directly edit this instead of the `report.qmd`)


![How Quarto Works](report/images/qmd-how-it-works.png)

⚠️<ins>**Please read the current file (`README.md`) very carefully!**</ins>⚠️

## Quick Start

### 1. Get the Project Template

There are two ways to get started:

**Option A: Use GitHub (recommended for collaboration)**

If you have a GitHub account and Git installed:

1. Click **Use this template → Create a new repository**.
2. Give your repository a name and click **Create repository**.
3. Clone your new repository to your computer:
   ```bash
   git clone <your-repo-url>
   ```
4. Open the downloaded project folder.

We recommend installing [GitHub Desktop](https://desktop.github.com/) to clone your repository and manage changes without using the terminal.

**Option B: Download as ZIP**

If you don't want to use GitHub:

1. Click the green **Code** button on this repository.
2. Select **Download ZIP**.
3. Extract the ZIP file to a folder on your computer.
4. Open the extracted folder.


### 2. Install Required Software

Make sure the following software is installed:

1. **Anaconda** (if not already installed)
   - Download from [anaconda.com](https://www.anaconda.com/download)
   - Follow installation instructions for your OS
   - Using *venv* instead of Conda is also possible

2. **Install Quarto**
   - Download from [quarto.org](https://quarto.org/docs/get-started/)
   - Verify: `quarto --version`
   - **Troubleshooting:** Run `quarto check` to diagnose installation issues

3. **Set up the Python environment**

   Open a new terminal in VS Code (**Terminal → New Terminal**).

   Make sure you're in the project root folder (where `requirements.txt` is located), then run:

   ```bash
   # Create a conda environment
   conda create -n dsmfm_project

   # Activate the environment
   conda activate dsmfm_project

   # Install required packages
   python -m pip install -r requirements.txt
   ```

4. **Install TinyTeX** (only required for PDF output)
   ```bash
   quarto install tinytex
   ```

5. **Render your report**

   ```bash
   quarto render report/report.qmd
   ```

#### Alternative: Render with Anaconda Navigator

1. **Open Anaconda Navigator**
   - Launch Anaconda Navigator from your applications.

2. **Create the Python environment**
   - Go to the **Environments** tab.
   - Click **Create**, name the environment `dsmfm_project`, and select your Python version. Alternatively, open a terminal in the base environment and run the following command:
   ```bash
   conda create -n dsmfm_project python
   ```

3. **Install the dependencies**
   - Select your new `dsmfm_project` environment.
   - Open a terminal for this environment.
   - Navigate to your downloaded project folder:

   ```bash
   cd <path-to-your-project-folder>
   ```

   - Install the required packages:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. **Install TinyTeX** (required for PDF output)

   ```bash
   quarto install tinytex
   ```

5. **Render your report**

   From your project root folder, run:

   ```bash
   quarto render report/report.qmd
   ```

   This generates the report in the formats specified in `report.qmd` (HTML, PDF, and/or DOCX).

## Project Structure

```
.
├── data/
│   ├── raw/           # Original data (original data here, then do not modify!)
│   └── processed/     # Cleaned data
├── report/
│   ├── sections/      # Report sections (.qmd files)
│   ├── report.qmd     # Main report file
│   └── references.bib # Bibliography
├── src/               # Python modules
└── requirements.txt   # Package dependencies
```

**Key rules:**
- Never modify files in `data/raw/` (ensures reproducibility)
- Use clear comments and docstrings in `src/`
- Each section in `report/sections/` is a separate `.qmd` file

## Working with Conda Environments

Conda manages Python environments to avoid package conflicts.

**Basic commands:**
```bash
# Activate your project environment
conda activate dsmfm_project

# Install additional packages
pip install package_name

# Deactivate when done
conda deactivate

# List all environments
conda env list
```

## Best Practices

- Set random seeds for reproducibility: `np.random.seed(42)`
- Use version control (Git) and commit regularly
- Write clear commit messages explaining what changed
- Update `.gitignore` to exclude `.venv/`, `__pycache__/` or `.DS_Store`
- Document your code thoroughly
- Never commit passwords, API keys, or other credentials. Avoid committing large datasets unless explicitly required.

## Reproducibility Checklist

Your project is reproducible if anyone can:

1. Clone the repository
2. Create conda environment: `conda create -n dsmfm_project python`
3. Activate environment: `conda activate dsmfm_project`
4. Install dependencies: `pip install -r requirements.txt`
5. Render report: `quarto render report/report.qmd`

All results should match exactly.

## Need Help?

- Ask during execise sessions.