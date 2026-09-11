# Travel-booking-backend


> **🚧 Project Status:** This project is actively under development. The README will be updated as new features, endpoints, and functionality are added.




# ✈️ Travel Booking Backend

A Python-based backend for a travel booking application. The project is currently focused on building and testing REST API endpoints that will form the foundation of a larger travel booking system.

## 📌 Current Status

The backend currently has **two working API endpoints**:

| Method | Endpoint   | Response           |
| ------ | ---------- | ------------------ |
| GET    | `/health`  | `{"status": "ok"}` |
| GET    | `/flights` | `{"flights": []}`  |

The `/health` endpoint confirms that the server is running, while `/flights` provides the initial structure for retrieving available flights.

## 🛠️ Technologies

* Python 3
* Flask
* REST API
* JSON
* Git & GitHub

## 📁 Project Structure

```text
travel-booking-backend/
│
├── main.py
├── requirements.txt
├── README.md
└── ...
```

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/travel-booking-backend.git
```

Then enter the project directory:

```bash
cd travel-booking-backend
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
```

Activate it on Linux/macOS:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## ▶️ Running the Backend

Start the server with:

```bash
python3 main.py
```

The API will be available locally at:

```text
http://127.0.0.1:5000
```

## 🔌 API Endpoints

### 1. Health Check

**GET `/health`**

This endpoint checks whether the backend server is running correctly.

Example request:

```bash
curl http://127.0.0.1:5000/health
```

Response:

```json
{
  "status": "ok"
}
```

### 2. Flights

**GET `/flights`**

This endpoint returns the currently available flights.

Example request:

```bash
curl http://127.0.0.1:5000/flights
```

Current response:

```json
{
  "flights": []
}
```

The empty array indicates that flight data has not yet been added.

## 🧪 Testing the API

You can test the endpoints using a browser, Postman, or `curl`.

### Health endpoint

```bash
curl http://127.0.0.1:5000/health
```

Expected:

```json
{
  "status": "ok"
}
```

### Flights endpoint

```bash
curl http://127.0.0.1:5000/flights
```

Expected:

```json
{
  "flights": []
}
```

## 🗺️ Next Steps

The backend will be expanded gradually. Planned functionality includes:

* [ ] Add flight data
* [ ] Search for flights
* [ ] Create flight bookings
* [ ] Retrieve booking information
* [ ] Cancel bookings
* [ ] Add database integration
* [ ] Add input validation
* [ ] Add automated tests
* [ ] Add authentication
* [ ] Connect the backend to a frontend

## 👨‍💻 Author

**Abraham Adejoh Shaibu**

This project is part of my backend development learning journey, focused on learning Python, APIs, HTTP methods, and building real-world backend applications.

## 📄 License

This project is currently intended for educational and development purposes.
