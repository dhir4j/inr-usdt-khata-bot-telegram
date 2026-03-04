 Below is the **final command list and exact working of each command** for my Telegram Khata Bot.

---

# Final Command List

```
/setprice
/price
/convert

/add
/del

/debit
/credit

/balance
/ledger

/users
/settle

/help
```

---

# 1. `/setprice <price>`

**Purpose:** Set the INR value of **1 USDT**.

Example

```
/setprice 83.5
```

Bot response

```
USDT price updated

1 USDT = ₹83.5
```

Rules

* Only **group admins**
* Used for **all conversions**

---

# 2. `/price`

Shows the current stored USDT price.

Example

```
/price
```

Response

```
Current Rate

1 USDT = ₹83.5
```

---

# 3. `/convert <amount> <currency>`

Converts between **USDT and INR**.

Example

```
/convert 1000 inr
```

Response

```
Conversion

₹1000 = 11.97 USDT
Rate: 1 USDT = ₹83.5
```

Example

```
/convert 10 usdt
```

Response

```
Conversion

10 USDT = ₹835
Rate: 1 USDT = ₹83.5
```

---

# 4. `/add @user`

Adds a user to the **group khata system**.

Example

```
/add @rahul
```

Response

```
User added to ledger

User: @rahul
Initial Balance: ₹0
```

Notes

* Only **admin allowed**
* Prevents random users from entering system

---

# 5. `/del @user`

Removes a user from the ledger.

Example

```
/del @rahul
```

Response

```
User removed from ledger
```

Rules

* Only admin
* If user has balance → bot warns

Example

```
Cannot delete user

Pending balance ₹500
```

---

# 6. `/debit @user <amount> <currency> <note>`

Records that **you gave money to the user**.

Example

```
/debit @rahul 500 inr dinner
```

Bot converts automatically.

Response

```
Debit Recorded

User: @rahul
Amount: ₹500 (6.02 USDT)
Note: dinner

Balance
Rahul owes you
₹500 (6.02 USDT)
```

---

# 7. `/credit @user <amount> <currency> <note>`

Records **payment received from the user**.

Example

```
/credit @rahul 200 inr
```

Response

```
Credit Recorded

User: @rahul
Amount: ₹200 (2.40 USDT)

Balance
Rahul owes you
₹300 (3.62 USDT)
```

---

# 8. `/balance @user`

Shows total balance between two users.

Example

```
/balance @rahul
```

Response

```
Ledger with @rahul

You gave: ₹2000 (24.09 USDT)
You received: ₹500 (6.01 USDT)

Balance

Rahul owes you
₹1500 (18.08 USDT)
```

---

# 9. `/ledger @user`

Shows transaction history.

Features

* **10 transactions per page**
* **Next / Previous buttons**

Example output

```
Ledger with @rahul
Page 1 / 3

1️⃣ Debit
₹500 (6.02 USDT)
Dinner

2️⃣ Credit
₹200 (2.40 USDT)
Paid back
```

Buttons

```
⬅ Prev | Next ➡
```

Bot **edits the same message when navigating pages**.

---

# 10. `/users`

Shows all users with balances.

Example

```
Group Ledger Summary

🟢 @rahul +₹1500 (18.07 USDT)
🔴 @amit -₹500 (6.01 USDT)
⚪ @neha ₹0
```

Legend

```
🟢 They owe you
🔴 You owe them
⚪ Settled
```

---

# 11. `/settle @user`

Clears balance between users.

Example

```
/settle @rahul
```

Response

```
Ledger settled

User: @rahul
Balance reset to ₹0
```

Note

* Ledger history **still kept**

---

# 12. `/help`

Shows command guide.

Example output

```
Khata Bot Commands

/setprice <price>
/price
/convert <amount> <inr/usdt>

/add @user
/del @user

/debit @user amount currency
/credit @user amount currency

/balance @user
/ledger @user
/users
/settle @user
```

---

# Example Real Usage Flow

Admin:

```
/setprice 83
```

Add users:

```
/add @rahul
/add @amit
```

Transaction:

```
/debit @rahul 830 inr dinner
```

Bot:

```
Debit Recorded

₹830 = 10 USDT
Rahul owes you ₹830
```

Rahul pays back:

```
/credit @rahul 5 usdt
```

Bot:

```
Credit Recorded

₹415 received
Balance ₹415
```

---

# Small Optional Rule (Recommended)

To avoid spam:

```
Only users added with /add
can participate in ledger
```

---
