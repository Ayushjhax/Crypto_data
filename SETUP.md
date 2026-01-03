# Setup Instructions

## Quick Setup

### 1. Create Virtual Environment (if not already created)

```bash
python3 -m venv venv
```

### 2. Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Setup

```bash
python3 test_collection.py
```

### 5. Run Full Collection

```bash
python3 main.py
```

Or use the convenience script:
```bash
chmod +x run.sh
./run.sh
```

## Environment Variables

The `.env` file is already configured with your API key. If you need to change it:

1. Edit `.env` file
2. Update `FREECRYPTO_API_KEY` with your API key

## Troubleshooting

### "Module not found" errors
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt`

### "API key not found" errors
- Check that `.env` file exists in project root
- Verify `FREECRYPTO_API_KEY` is set in `.env`

### Import errors
- Make sure you're in the project root directory
- Verify all files are present

## Running in Console

Always activate the virtual environment first:

```bash
source venv/bin/activate
python3 main.py
```

Or use the run script:
```bash
./run.sh
```

