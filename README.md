# Orders API

A Django-based REST API for managing orders with multi-tenancy support, idempotency, optimistic locking, and cursor-based pagination.

## 1. Setup

### Clone the Repository

```bash
git clone https://github.com/ARSLAN-47/orders_api.git
cd orders_api
```

### Create Virtual Environment

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Database Setup

### Option 1: Local PostgreSQL

1. Create database: `orders_db`
2. Set environment variables (replace values as needed):

```bash
export POSTGRES_DB=orders_db
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
```

### Option 2: Docker PostgreSQL

1. Update environment variables in `docker-compose.yml` as needed
2. Run Docker Compose:

```bash
docker-compose up -d
```

### Run Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

## 3. Run Tests

```bash
# Using Django test runner
python manage.py test orders_app

# Or with pytest
pytest orders_app/tests/
```

## 4. Run Server

```bash
python manage.py runserver
```

Server runs on: [http://localhost:8000](http://localhost:8000)

## 5. Example cURL Requests

### Create Draft Order

```bash
curl -X POST http://localhost:8000/orders \
  -H "X-Tenant-Id: shop-1" \
  -H "Idempotency-Key: test-123" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Confirm Order

```bash
curl -X PATCH http://localhost:8000/orders/<id>/confirm \
  -H "X-Tenant-Id: shop-1" \
  -H "If-Match: 1" \
  -H "Content-Type: application/json" \
  -d '{"totalCents": 1000}'
```

### Close Order

```bash
curl -X POST http://localhost:8000/orders/<id>/close \
  -H "X-Tenant-Id: shop-1"
```

### List Orders with Pagination

```bash
curl http://localhost:8000/orders?limit=10&cursor=<opaque>
```

## 6. Important Notes

- **Multi-tenancy**: Tenant middleware checks `X-Tenant-Id` header; exempted paths: `/schema/`, `/docs/`
- **Idempotency**: Idempotency keys are valid for 1 hour
- **Optimistic Locking**: Enforced with `If-Match` header for version control
- **Pagination**: Uses keyset (cursor-based) pagination to avoid duplicates/omissions

