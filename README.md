# Orders App

A DjangoRestFramework-based Orders API with:

- Draft orders creation (idempotent)
- Optimistic locking (versioning)
- Close orders + transactional outbox
- Keyset pagination
- Tenant-based requests (X-Tenant-Id header)

---

## **1. Setup**

### 1️⃣ Clone the repo
```bash
git clone https://github.com/ARSLAN-47/orders_api.git
cd orders_api


2️⃣ Create virtual environment
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

3️⃣ Install dependencies
pip install -r requirements.txt


## **2. Database**
Option 1: Local Postgres
Create DB: orders_db
Set environment variable:
Set environment variables 
(replace values as needed):
export POSTGRES_DB=orders_db
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432

Option 2: Docker Postgres
(replace values as needed) in compose file for env variables:
docker-compose up -d


Make migrations:
python manage.py makemigrations

Run migrations:
python manage.py migrate


3. Run Tests
python manage.py test orders_app
# or with pytest
pytest orders_app/tests/


4. Run Server
python manage.py runserver

Server runs on: http://localhost:8000


5. Example cURL Requests
Create draft order
curl -X POST http://localhost:8000/orders \
  -H "X-Tenant-Id: shop-1" \
  -H "Idempotency-Key: test-123" \
  -H "Content-Type: application/json" \
  -d '{}'

Confirm order
curl -X PATCH http://localhost:8000/orders/<id>/confirm \
  -H "X-Tenant-Id: shop-1" \
  -H "If-Match: 1" \
  -H "Content-Type: application/json" \
  -d '{"totalCents": 1000}'

Close order
curl -X POST http://localhost:8000/orders/<id>/close \
  -H "X-Tenant-Id: shop-1"

List orders with pagination
curl http://localhost:8000/orders?limit=10&cursor=<opaque>


6. Notes

Tenant middleware checks X-Tenant-Id; exempted paths: /schema/, /docs/.

Idempotency keys valid for 1 hour.

Optimistic locking enforced with If-Match header.

Pagination uses keyset (cursor) to avoid duplicates/omissions.