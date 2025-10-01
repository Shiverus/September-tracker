# 📊 September-tracker
Easy finance tracker based on private telegram channel 

Automated system for tracking personal expenses through Telegram channels. The program automatically collects messages from private Telegram channels, analyzes expenses, and generates detailed reports in Excel.

## ✨ Features

- **🤖 Automated Data Collection** - fetch messages from Telegram channels
- **📈 Expense Analysis** - categorization, daily/weekly statistics
- **📊 Visualization** - automatic Excel report generation
- **🔔 Smart Notifications** - top categories, weekday/weekend comparisons
- **⚙️ Flexible Configuration** - easy configuration files

## 🛠 Installation

### Requirements

- Python 3.8+
- Telegram account with access to private channel

### Install Dependencies

```bash
pip install telethon pandas openpyxl
```

### Telegram API Setup

1. Get API credentials from [my.telegram.org](https://my.telegram.org/)
2. Create `config.py` file in project root:

```python
# config.py
API_ID = 1234567                    # Your API ID
API_HASH = 'your_api_hash_here'     # Your API Hash
CHANNEL_ID = -1001234567890         # Your channel ID
```

## 🚀 Quick Start

### 1. Prepare Telegram Channel

Create a private channel. Message format for expense tracking:

```
expense_name amount
```

**Examples:**
```
coffee 350
groceries 1200
gasoline 2500
```

### 2. Run the Program

```bash
# For windows:
python main.py

# For MacOS an Linux:
python3 main.py
```

### 3. Authorization

On first run you'll need to:
- Enter your phone number
- Confirm login via code
- Enter 2FA password if required

## 📁 Project Structure

```
telegram-expenses-tracker/
├── main.py                 # Main script
├── requirements.txt        # Dependencies
└── ../september/data/      # Generated files
    ├── config.py               # API configuration (created)
    ├── categories.py           # File with categories (created)
    ├── messages.json           # Raw Telegram data
    ├── budget.xlsx             # All transactions
    ├── daily_spendings.xlsx    # Daily expenses
    ├── category_spendings.xlsx # Category expenses
    ├── weekday_spendings.xlsx  # Weekday statistics (workdays vs. weekends)
    └── not_used_categories.txt # Unprocessed categories (transfer all not used categories to categories.py manually)
```

## ⚙️ Configuration

### Expense Categories

Edit the `categories` dictionary in the code to configure categories:

```python
'category': ['keywords', 'for', 'matching', 'messages']
```

### Time Period Settings

Change `days_back` in configuration for different data collection periods:

```python
'telegram': {
    'days_back': 30  # Collect data for last 30 days
}
```

## 📊 Generated Reports

### 1. **budget.xlsx**
- Complete list of all transactions
- Date, category, amount

### 2. **daily_spendings.xlsx**
- Total expenses by day
- Overall period sum

### 3. **category_spendings.xlsx**
- Expense distribution by categories
- Top spending categories

### 4. **weekday_spendings.xlsx**
- Weekday vs weekend comparison
- Average values per day type

## 🎯 Usage Example

```bash
# Run the program
python main.py

# Console output:



==================================================
EXPENSE SUMMARY REPORT
==================================================
Monthly expenses: 45,200 RUB
Average daily expense: 1,507 RUB
Days with expenses: 30
Total transactions: 45

Top 3 spending categories:
  1. supermarkets: 15,200 RUB
  2. snacks: 8,500 RUB
  3. car: 7,300 RUB

Expense comparison:
  Average weekday expense: 1,200 RUB
  Average weekend expense: 2,100 RUB
  You spend 900 RUB more on weekends
==================================================


```

## 🔧 Troubleshooting

### ❌ "Channel not found"
- Verify channel ID is correct
- Use @username_to_id_bot to get channel ID

### ❌ "No access to channel"
- Ensure you're channel administrator
- Bot must be added as administrator

### ❌ "Invalid message format"
- Messages must contain text and number
- Format: `text amount` (example: "coffee 350")

### ❌ API Errors
- Verify API_ID and API_HASH are correct
- Ensure account is not blocked

## 📝 Data Format

### Input Data (Telegram Messages)
```
coffee 350
groceries 1200
gasoline 2500
cinema 800
```

### Output Data (Excel Reports)
- **Date** in DD.MM.YYYY format
- **Category** - automatically detected
- **Amount** - numerical value

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is distributed under MIT License - see [LICENSE](LICENSE) file for details.

## ⚠️ Important Notes

- Keep `config.py` secure, don't commit to public repositories
- Regularly update categories for accurate analytics
- Backup generated reports regularly

---

**⭐ If this project was helpful, please give it a star on GitHub!**
