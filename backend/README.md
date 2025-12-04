
## API Testing Guide

All commands below use `curl`. The `-c cookies.txt` flag saves cookies and `-b cookies.txt` sends them.

### Authentication

#### Sign Up (Create Account)
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "password": "yourpassword123"
  }'
```

#### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "user@example.com",
    "password": "yourpassword123"
  }'
```

#### Check Auth Status
```bash
curl -X GET http://localhost:8000/auth/status \
  -b cookies.txt
```

#### Logout
```bash
curl -X POST http://localhost:8000/auth/logout \
  -b cookies.txt
```

---

### User

#### Get Current User Profile
```bash
curl -X GET http://localhost:8000/users/me \
  -b cookies.txt
```

---

### Transactions

#### Create Income Transaction
```bash
curl -X POST http://localhost:8000/transactions/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "amount": 5000.00,
    "type": "income",
    "category": "salary",
    "note": "Monthly salary",
    "date": "2025-12-03T10:00:00Z"
  }'
```

#### Create Expense Transaction
```bash
curl -X POST http://localhost:8000/transactions/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "amount": 250.50,
    "type": "expense",
    "category": "food",
    "note": "Groceries",
    "date": "2025-12-03T15:30:00Z"
  }'
```

#### Get All Transactions
```bash
curl -X GET http://localhost:8000/transactions/ \
  -b cookies.txt
```

#### Delete Transaction
```bash
curl -X DELETE http://localhost:8000/transactions/{transaction_id} \
  -b cookies.txt
```