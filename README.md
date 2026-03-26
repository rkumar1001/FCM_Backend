# FCM Order Notification Backend

A production-ready **FastAPI** backend that receives restaurant orders from **RetellAI** voice agent webhooks, validates them against the restaurant menu, sends **Firebase Cloud Messaging (FCM)** push notifications to the restaurant's device, and persists all orders to **SQLite**.

Built for **The Masala Twist** restaurant — easily adaptable to any restaurant by updating the menu and environment config.

---

## Architecture

```
Customer → RetellAI Voice Agent → Webhook POST → This Backend → FCM Push → Restaurant Android App
                                                       ↓
                                                    SQLite DB
```

### Flow

1. Customer places an order via phone call handled by RetellAI voice agent.
2. RetellAI sends a webhook (`POST /webhooks/retell/order`) with call info and order details.
3. Backend parses order items (JSON or text format), including **spice levels** and **modifications**.
4. Items are **fuzzy-matched** against the restaurant menu (difflib, threshold 0.75). Unrecognized items are flagged as `[NEEDS REVIEW]`.
5. A short **confirmation number** (e.g. `MT-4829`) is generated and returned to RetellAI to tell the customer.
6. Order is **saved to SQLite** for record keeping.
7. Full order data is sent as a **data-only FCM push notification** to the restaurant's device.

---

## Project Structure

```
FCM_Backend/
├── app/
│   ├── main.py              # FastAPI app, startup, health check, legacy endpoint
│   ├── config.py             # Centralized env config
│   ├── models.py             # Pydantic models (webhook payload, order, items)
│   ├── parser.py             # Order item parsers (JSON + text fallback)
│   ├── menu.py               # Menu registry with fuzzy matching (100+ items)
│   ├── services.py           # Order normalization, menu validation, FCM dispatch
│   ├── database.py           # SQLite persistence (init + save)
│   ├── firebase_config.py    # Firebase Admin SDK init + push notification
│   └── routes/
│       └── retell.py         # RetellAI webhook endpoint
├── .env                      # Environment variables (not committed)
├── .env.example              # Template for .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.12+
- Firebase project with Cloud Messaging enabled
- Firebase service account key (JSON file)
- RetellAI agent configured to call the webhook URL

### Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/FCM_Backend.git
cd FCM_Backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

2. Place your Firebase service account JSON key in the project root and update the filename in `app/firebase_config.py` if needed.

3. Set your Android device's FCM token in `.env` as `DEVICE_TOKEN`.

### Environment Variables

| Variable             | Description                          |
|----------------------|--------------------------------------|
| `SECRET_KEY`         | Auth secret for the legacy endpoint  |
| `PORT`               | Server port (default: 8000)          |
| `DEVICE_TOKEN`       | FCM device token of restaurant app   |
| `RESTAURANT_NAME`    | Restaurant name for order data       |
| `RESTAURANT_PHONE`   | Restaurant phone number              |
| `RESTAURANT_ADDRESS` | Restaurant address                   |
| `ORDER_TYPE`         | Default order type (e.g. `pickup`)   |

---

## Running

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Expose via ngrok (for RetellAI webhook)

```bash
ngrok http 8000
```

Set your ngrok public URL + `/webhooks/retell/order` as the webhook URL in RetellAI.

---

## API Endpoints

### `GET /health`

Health check. Returns `{"status": "ok"}`.

### `POST /webhooks/retell/order`

Main endpoint for RetellAI webhooks.

**Request body** (sent by RetellAI):

```json
{
  "call": {
    "call_id": "call_abc123",
    "from_number": "+14155551234",
    "to_number": "+19052309355",
    "call_status": "ended"
  },
  "name": "place_order",
  "args": {
    "customer_name": "John Smith",
    "phone_number": "+14155551234",
    "pickup_time": "30 minutes",
    "order_items_json": "[{\"item_name\":\"Chicken Tikka Masala\",\"quantity\":2,\"spice_level\":4,\"modifications\":\"extra onions\"},{\"item_name\":\"Garlic Naan\",\"quantity\":3,\"modifications\":\"extra butter\"}]",
    "order_summary": "2 Chicken Tikka Masala (spice 4, extra onions), 3 Garlic Naan (extra butter)"
  }
}
```

**Response:**

```json
{
  "status": "sent",
  "confirmation_number": "MT-4829",
  "job_id": "call_abc123"
}
```

### `POST /send-order`

Legacy endpoint (for backward compatibility with n8n workflows). Requires `secret` auth.

---

## FCM Payload

The restaurant's Android app receives a data-only FCM message with key `order_json` containing:

```json
{
  "job_id": "call_abc123",
  "confirmation_number": "MT-4829",
  "order_date": "2026-03-25 18:30:00",
  "customer_name": "John Smith",
  "phone_number": "+14155551234",
  "ready_time": "30 minutes",
  "status": "confirmed",
  "restaurant_name": "The Masala Twist",
  "order_type": "pickup",
  "items": [
    {
      "quantity": 2,
      "name": "chicken tikka masala",
      "spice_level": 4,
      "original_name": "Chicken Tikka Masala",
      "matched": true,
      "confidence": 1.0,
      "modifiers": {
        "modifications": "extra onions"
      }
    },
    {
      "quantity": 3,
      "name": "garlic naan",
      "spice_level": null,
      "original_name": "Garlic Naan",
      "matched": true,
      "confidence": 1.0,
      "modifiers": {
        "modifications": "extra butter"
      }
    }
  ]
}
```

---

## Key Features

- **Fuzzy menu matching** — Handles misspellings and voice transcription errors (e.g. "Lamb Sherry Korma" → "lamb shahi korma")
- **Spice levels & modifications** — Captures all per-item customizations from the customer
- **Short confirmation numbers** — Human-friendly codes (MT-XXXX) returned to RetellAI for the customer
- **SQLite order history** — Every order is persisted automatically
- **Data-only FCM push** — Full order details sent to the restaurant app for printing/display

---

## Tech Stack

- **Python 3.12** / **FastAPI** / **Uvicorn**
- **Firebase Admin SDK** (FCM)
- **SQLite** (order persistence)
- **Pydantic v2** (data validation)
- **difflib** (fuzzy menu matching)
