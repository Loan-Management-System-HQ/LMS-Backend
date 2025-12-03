# LMS Backend API Endpoints Documentation

## Overview

This document describes all API endpoints in the Loan Management System (LMS) backend. The system includes four main apps: Users, Documents, Loans, and Simulations. All endpoints are prefixed with `/api/` and run on `localhost:8000` by default.

## Authentication

Most endpoints require authentication using JWT tokens. Obtain tokens via `/api/auth/login/` or `/api/auth/register/`.

## 1. Users App (`/api/auth/`)

### 1.1 Register User

- **Endpoint**: `POST /api/auth/register/`
- **Description**: Register a new user account
- **Sample Request**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }
  ```
- **Sample Response**:
  ```json
  {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe"
    },
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```

### 1.2 Login

- **Endpoint**: `POST /api/auth/login/`
- **Description**: Authenticate user and get JWT tokens
- **Sample Request**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword123"
  }
  ```
- **Sample Response**: Same as register response

### 1.3 Refresh Token

- **Endpoint**: `POST /api/auth/token/refresh/`
- **Description**: Refresh access token using refresh token
- **Sample Request**:
  ```json
  {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```

### 1.4 Get/Update Profile

- **Endpoint**: `GET/PUT/PATCH /api/auth/profile/`
- **Description**: Retrieve or update user profile
- **Headers**: `Authorization: Bearer <access_token>`
- **Sample Response**:
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_staff": false
  }
  ```

### 1.5 Logout

- **Endpoint**: `POST /api/auth/logout/`
- **Description**: Blacklist refresh token to logout
- **Sample Request**:
  ```json
  {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
  ```

## 2. Documents App (`/api/documents/`)

### 2.1 List/Create Documents

- **Endpoint**: `GET/POST /api/documents/documents/`
- **Description**: List user's documents or upload new document
- **Headers**: `Authorization: Bearer <access_token>`
- **Sample POST Request** (Upload):
  ```json
  {
    "document_type": "ID_PROOF",
    "file": "<file_data>",
    "display_filename": "My ID Document"
  }
  ```

### 2.2 Document Actions

- **Download**: `GET /api/documents/documents/{id}/download/`
- **Preview**: `GET /api/documents/documents/{id}/preview/`
- **Approve** (Staff): `POST /api/documents/documents/{id}/approve/`
- **Reject** (Staff): `POST /api/documents/documents/{id}/reject/`
- **Reset** (Staff): `POST /api/documents/documents/{id}/reset/`
- **Review** (Staff): `POST /api/documents/documents/{id}/review/`

### 2.3 Special Endpoints

- **My Documents**: `GET /api/documents/my-documents/`
- **Pending Documents**: `GET /api/documents/pending/`
- **Approved Documents**: `GET /api/documents/approved/`
- **Documents by Type**: `GET /api/documents/by-type/?type=ID_PROOF`
- **Statistics**: `GET /api/documents/stats/`
- **Staff Dashboard**: `GET /api/documents/staff/dashboard/`
- **Request New Document** (Staff): `POST /api/documents/request_new/`

## 3. Loans App (`/api/loans/`)

### 3.1 Loan Applications

- **Endpoint**: `GET/POST /api/loans/applications/`
- **Description**: List/create loan applications
- **Sample POST Request**:
  ```json
  {
    "amount": 10000.0,
    "duration": 12,
    "purpose": "HOME_IMPROVEMENT"
  }
  ```
- **Actions**:
  - Submit: `POST /api/loans/applications/{id}/submit/`
  - Approve (Staff): `POST /api/loans/applications/{id}/approve/`
  - Reject (Staff): `POST /api/loans/applications/{id}/reject/`
  - Add Document: `POST /api/loans/applications/{id}/add_document/`

### 3.2 Loans

- **Endpoint**: `GET /api/loans/loans/`
- **Description**: List user's approved loans
- **Actions**:
  - Get Installments: `GET /api/loans/loans/{id}/installments/`

### 3.3 Installments

- **Endpoint**: `GET /api/loans/installments/`
- **Description**: List user's loan installments
- **Actions**:
  - Overdue: `GET /api/loans/installments/overdue/`
  - Upcoming: `GET /api/loans/installments/upcoming/`

### 3.4 Calculator

- **Endpoint**: `POST /api/loans/calculator/`
- **Description**: Calculate loan payments without applying
- **Sample Request**:
  ```json
  {
    "amount": 10000.0,
    "duration": 12,
    "interest_rate": 5.0
  }
  ```
- **Sample Response**:
  ```json
  {
    "monthly_payment": 856.07,
    "total_interest": 272.84,
    "total_payment": 10272.84,
    "amortization_table": [...]
  }
  ```

### 3.5 Payments

- **Endpoint**: `POST /api/loans/payments/`
- **Description**: Make a loan payment
- **Sample Request**:
  ```json
  {
    "installment_id": 1,
    "amount": 856.07
  }
  ```

### 3.6 Dashboard

- **Endpoint**: `GET /api/loans/dashboard/`
- **Description**: Get loan dashboard statistics

## 4. Simulations App (`/api/simulations/`)

### 4.1 Create Simulation

- **Endpoint**: `POST /api/simulations/simulations/`
- **Description**: Create and save simulation (authenticated) or calculate (anonymous)
- **Sample Request**:
  ```json
  {
    "amount": 10000.0,
    "duration": 12,
    "interest_rate": 5.0
  }
  ```
- **Sample Response** (Authenticated):
  ```json
  {
    "id": 1,
    "amount": 10000.0,
    "duration": 12,
    "interest_rate": 5.0,
    "monthly_payment": 856.07,
    "total_interest": 272.84,
    "total_payment": 10272.84,
    "simulation_date": "2025-12-03T10:00:00Z"
  }
  ```

### 4.2 Calculate Only

- **Endpoint**: `POST /api/simulations/simulations/calculate/`
- **Description**: Calculate simulation without saving
- **Sample Request/Response**: Same as create but without saving

### 4.3 Simulation History

- **Endpoint**: `GET /api/simulations/simulations/history/`
- **Description**: Get user's simulation history
- **Headers**: `Authorization: Bearer <access_token>`

### 4.4 Use for Application

- **Endpoint**: `POST /api/simulations/simulations/{id}/use_for_application/`
- **Description**: Mark simulation for loan application
- **Headers**: `Authorization: Bearer <access_token>`

### 4.5 Clear History

- **Endpoint**: `DELETE /api/simulations/simulations/clear_history/`
- **Description**: Delete all user's simulations
- **Headers**: `Authorization: Bearer <access_token>`

## Testing Instructions

### Setup

1. Start the Django server: `python manage.py runserver`
2. Server runs on `http://localhost:8000`
3. Use tools like Postman, curl, or browser for testing

### Authentication Flow

1. Register: `POST /api/auth/register/` with user data
2. Login: `POST /api/auth/login/` to get tokens
3. Include `Authorization: Bearer <access_token>` in subsequent requests

### Sample Test Sequence

1. Register a user
2. Login to get tokens
3. Create a simulation: `POST /api/simulations/simulations/`
4. Upload a document: `POST /api/documents/documents/`
5. Create loan application: `POST /api/loans/applications/`
6. View dashboard: `GET /api/loans/dashboard/`

### Error Handling

- 401: Authentication required
- 403: Permission denied
- 400: Bad request (validation errors)
- 404: Resource not found

## Notes

- Staff users have additional permissions for approval/rejection actions
- Anonymous users can calculate simulations but cannot save them
- File uploads require multipart/form-data
- All monetary values are in decimal format
