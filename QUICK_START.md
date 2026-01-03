# Quick Start Guide

## 🚀 Getting Started in 3 Steps

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Verify Setup

Test your API key and configuration:

```bash
python test_collection.py
```

This will:
- Test API connectivity
- Collect sample data for Bitcoin
- Save data to verify file operations
- Show you what data looks like

### Step 3: Run Full Collection

Collect data for all configured coins:

```bash
python main.py
```

This will:
- Collect data for all coins in `config/data_sources.yaml`
- Save individual files for each coin
- Create an aggregated dataset
- Show collection statistics

---

## 📁 Where is My Data?

Collected data is saved in:
- **Individual files**: `data/raw/{SYMBOL}_{TIMESTAMP}.json`
- **Aggregated file**: `data/raw/all_coins_{TIMESTAMP}.json`

Example:
```
data/raw/
├── BTC_20240115_103000.json
├── ETH_20240115_103000.json
└── all_coins_20240115_103000.json
```

---

## 🔧 Configuration

### Adding More Coins

Edit `config/data_sources.yaml`:

```yaml
coins:
  - symbol: "BTC"
    name: "Bitcoin"
  - symbol: "ETH"
    name: "Ethereum"
  # Add more coins here
  - symbol: "LINK"
    name: "Chainlink"
```

### Changing API Settings

Edit `.env` file:

```bash
# Adjust collection interval (seconds)
COLLECTION_INTERVAL_SECONDS=60

# Adjust retry attempts
MAX_RETRIES=3

# Adjust request timeout
REQUEST_TIMEOUT=30
```

---

## 🐛 Troubleshooting

### "API key not found"
- Check that `.env` file exists
- Verify `FREECRYPTO_API_KEY` is set correctly

### "Connection timeout"
- Check your internet connection
- Verify API endpoint URL is correct
- Try increasing `REQUEST_TIMEOUT` in `.env`

### "Invalid API response"
- API response format might have changed
- Check `core/data_collector.py` `_transform_coin_data` method
- Adjust field mappings based on actual API response

### "Rate limit exceeded"
- You're making requests too quickly
- Increase delay between requests
- Check API rate limits in documentation

---

## 📊 Understanding the Output

When you run `main.py`, you'll see:

```
============================================================
DonutAI - Crypto Data Collection Pipeline
Phase 1: Data Collection
============================================================
[2024-01-15 10:30:00] [INFO] [agents.collector_agent] Starting data collection...
[2024-01-15 10:30:01] [INFO] [core.data_collector] Collecting data for BTC
[2024-01-15 10:30:02] [INFO] [core.data_collector] Saved data to data/raw/BTC_20240115_103002.json
...
============================================================
COLLECTION SUMMARY
============================================================
Total collections attempted: 8
Successful: 8
Failed: 0
Success rate: 100.0%
Coins collected: BTC, ETH, BNB, SOL, ADA, XRP, DOGE, DOT
============================================================
```

---

## 🎯 Next Steps

1. **Explore the code**: Read through the files to understand the architecture
2. **Check INTERVIEW_GUIDE.md**: Learn how to explain this project
3. **Modify and experiment**: Try adding features or changing behavior
4. **Phase 2**: Ready to move to data cleaning? Let me know!

---

## 💡 Tips

- **Check logs**: Look in `logs/donutai.log` for detailed information
- **Test first**: Always run `test_collection.py` before full collection
- **Read the code**: Comments explain concepts for interview prep
- **Experiment**: Try modifying the code to see what happens

Happy coding! 🚀

cd /Users/ayush/Desktop/DonutAI && chmod +x run.sh