# DonutAI - Crypto Data Collection Pipeline

A comprehensive project for learning agent-based data collection, cleaning, labeling, and quality checks for cryptocurrency data.

## 🎯 Project Overview

This project demonstrates a production-ready data pipeline for collecting, processing, and validating cryptocurrency data using an agent-based architecture.

## 📚 Learning Objectives

### Phase 1: Data Collection (Current)
- ✅ API integration with error handling
- ✅ Rate limiting and retry logic
- ✅ Data validation
- ✅ File I/O operations
- ✅ Agent-based orchestration

### Phase 2: Data Cleaning (Upcoming)
- Missing value handling
- Outlier detection
- Data normalization
- Duplicate removal

### Phase 3: Data Labeling (Upcoming)
- Rule-based labeling
- Time-series labeling
- Feature engineering

### Phase 4: Quality Checks (Upcoming)
- Completeness metrics
- Consistency validation
- Statistical summaries

## 🏗️ Project Structure

```
DonutAI/
├── agents/              # Agent orchestration layer
│   └── collector_agent.py
├── core/                # Core business logic
│   └── data_collector.py
├── config/              # Configuration management
│   ├── settings.py
│   └── data_sources.yaml
├── utils/               # Utility functions
│   ├── logger.py
│   └── validators.py
├── data/                # Data storage
│   └── raw/
├── main.py              # Entry point
└── requirements.txt
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

The API key is already configured in `.env`. If you need to change it:

```bash
cp .env.example .env
# Edit .env and add your API key
```

### 3. Run Data Collection

```bash
python main.py
```

## 📖 Interview Preparation Guide

### Key Concepts Explained

#### 1. **Agent Pattern**
- **What**: High-level orchestrators that coordinate workflows
- **Why**: Separates orchestration from business logic
- **Example**: `CollectorAgent` coordinates data collection workflow

#### 2. **Separation of Concerns**
- **Agents**: Workflow orchestration
- **Core**: Business logic
- **Utils**: Helper functions
- **Config**: Settings management

#### 3. **Error Handling**
- **Retry Logic**: Exponential backoff for transient failures
- **Graceful Degradation**: Continue processing even if some items fail
- **Logging**: Comprehensive error tracking

#### 4. **Data Validation**
- **Input Validation**: Check API responses
- **Output Validation**: Verify collected data structure
- **Type Safety**: Ensure correct data types

#### 5. **Rate Limiting**
- **Why**: Prevent API abuse and stay within limits
- **How**: Track request timing, add delays
- **Best Practice**: Respectful API usage

#### 6. **Configuration Management**
- **Environment Variables**: Sensitive data (API keys)
- **YAML Files**: Structured configuration
- **Settings Module**: Centralized config access

## 🔧 API Integration Details

### FreeCryptoAPI Endpoints

The project uses FreeCryptoAPI for data collection. Common endpoints:
- `/coins/{symbol}` - Get coin data
- `/price/{symbol}` - Get current price

**Note**: Adjust endpoints in `core/data_collector.py` based on actual API documentation.

## 📊 Data Format

Collected data is saved in JSON format with the following structure:

```json
{
  "symbol": "BTC",
  "timestamp": "2024-01-15T10:30:00",
  "price": 45000.00,
  "market_cap": 850000000000,
  "volume_24h": 25000000000,
  "price_change_24h": 2.5,
  "raw_data": { ... }
}
```

## 🧪 Testing

Run tests (when implemented):

```bash
pytest tests/
```

## 📝 Next Steps

1. **Phase 2**: Implement data cleaning agents
2. **Phase 3**: Add data labeling functionality
3. **Phase 4**: Build quality check system
4. **Enhancements**: 
   - Add async/threading for parallel collection
   - Implement data streaming
   - Add database storage
   - Create monitoring dashboard

## 💡 Interview Tips

When discussing this project in interviews:

1. **Architecture**: Explain the agent pattern and separation of concerns
2. **Error Handling**: Discuss retry logic and graceful degradation
3. **Scalability**: Mention how you'd add parallel processing
4. **Testing**: Explain how you'd test each component
5. **Production**: Discuss monitoring, logging, and deployment considerations

## 📄 License

This is a learning project. Feel free to use and modify as needed.

