# 📒 Khata Bot

A Telegram group bot for tracking shared expenses and transactions in both **INR** and **USDT** with automatic currency conversion.

---

## ✨ Features

- 💱 Real-time INR ↔ USDT conversion using a manually set rate
- 📤 Record debits, credits, and salary payments
- 📊 Per-user balance summaries
- 📋 Paginated transaction history
- 🤝 Settle balances with full history preserved
- 📁 Export ledger to CSV (Indian timezone)
- 👥 Admin-only user and price management
- 🔔 Interactive inline buttons for navigation

---

## 🤖 Commands

### 💱 Currency
| Command | Description |
|---|---|
| `/setprice <price>` | Set 1 USDT = ₹price *(admin only)* |
| `/price` | Show current USDT rate |
| `/convert <amount> <inr/usdt>` | Convert between INR and USDT |

### 👥 Users
| Command | Description |
|---|---|
| `/add @user` | Add user to ledger *(admin only)* |
| `/del @user` | Remove user from ledger *(admin only)* |
| `/users` | Show all users with balances |

### 💸 Transactions
| Command | Description |
|---|---|
| `/debit @user <amount> <inr/usdt> [note]` | Record money you gave |
| `/credit @user <amount> <inr/usdt> [note]` | Record money you received |
| `/salary @user <amount> <inr/usdt> [note]` | Record salary paid |

### 📊 Ledger
| Command | Description |
|---|---|
| `/balance @user` | Balance summary with a user |
| `/ledger @user` | Paginated transaction history |
| `/settle @user` | Reset balance to zero |
| `/export` | Export all group transactions to CSV |
| `/export @user` | Export transactions with a specific user |

---

## 🗂️ Project Structure

```
khata_bot/
├── main.py                  # Entry point
├── .env                     # Bot token (not committed)
├── .env.example             # Example env file
├── requirements.txt
└── bot/
    ├── main.py              # App builder & handler registration
    ├── database/
    │   └── db.py            # SQLite schema & all DB operations
    ├── handlers/
    │   ├── price.py         # /setprice, /price
    │   ├── convert.py       # /convert
    │   ├── users.py         # /add, /del, /users
    │   ├── transactions.py  # /debit, /credit, /salary
    │   ├── ledger.py        # /balance, /ledger, /settle
    │   ├── export.py        # /export
    │   └── help.py          # /help, /start
    ├── services/
    │   └── converter.py     # INR ↔ USDT conversion logic
    ├── utils/
    │   └── helpers.py       # Admin check, formatters, parsers
    └── keyboards/
        └── pagination.py    # Inline keyboard for ledger pages
```

---

## 🗄️ Database Schema

```sql
-- Group settings
CREATE TABLE groups (
    group_id      INTEGER PRIMARY KEY,
    usdt_price_inr REAL DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now'))
);

-- Registered users
CREATE TABLE users (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id INTEGER NOT NULL,
    username         TEXT,
    first_name       TEXT,
    group_id         INTEGER NOT NULL,
    UNIQUE(telegram_user_id, group_id)
);

-- All transactions
CREATE TABLE transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id    INTEGER NOT NULL,
    from_user   INTEGER NOT NULL,
    to_user     INTEGER NOT NULL,
    amount_inr  REAL NOT NULL,
    amount_usdt REAL NOT NULL,
    type        TEXT NOT NULL CHECK(type IN ('debit','credit','settle')),
    note        TEXT DEFAULT '',
    created_at  TEXT DEFAULT (datetime('now'))
);
```

---

## ⚙️ Setup & Installation

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/khata_bot.git
cd khata_bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```
BOT_TOKEN=your_telegram_bot_token_here
```

> Get a token from [@BotFather](https://t.me/BotFather) on Telegram.

### 4. Run the bot

```bash
python main.py
```

---

## ☁️ Deploying on PythonAnywhere (24/7)

> Requires a paid plan for Always-on tasks.

### 1. Upload project

```bash
git clone https://github.com/yourusername/khata_bot.git ~/khata_bot
```

### 2. Install dependencies

```bash
cd ~/khata_bot
pip3 install --user -r requirements.txt
```

### 3. Create `.env`

```bash
nano ~/khata_bot/.env
# Add: BOT_TOKEN=your_token
```

### 4. Add Always-on Task

Go to **Dashboard → Tasks → Always-on tasks** and enter:

```
cd /home/yourusername/khata_bot && python3 main.py
```

The task auto-restarts if the process crashes, keeping the bot online 24/7.

---

## 📋 Example Usage

```
# Admin sets the rate
/setprice 85

# Add users
/add @rahul
/add @amit

# Record a transaction
/debit @rahul 500 inr dinner

# Bot responds:
📤 Debit Recorded
👤 @rahul
💰 ₹500.00 (5.88 USDT)
📝 dinner

📊 Balance
✅ Rahul owes you
💵 ₹500.00 (5.88 USDT)

# Check balance
/balance @rahul

# Export to CSV
/export
```

---

## 🛡️ Rules & Validations

- Only **group admins** can run `/setprice`, `/add`, `/del`
- Users must be registered via `/add` before transacting
- Self-transactions are blocked
- Currency must be `inr` or `usdt`
- Admins are **auto-added** to the ledger on first transaction
- `/settle` records a settlement entry — history is never deleted
- All amounts rounded to 2 decimal places

---

## 📦 Requirements

```
python-telegram-bot==21.10
python-dotenv==1.1.0
```

Python 3.10+ required.

---

## 📄 License

MIT License — free to use and modify.
