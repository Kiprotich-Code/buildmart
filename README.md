# Buildmart API

**Buildmart** is a modern marketplace platform built with Django REST Framework, featuring JWT authentication, role-based access control, and comprehensive user management for buyers, sellers, and administrators.

## 🚀 Features

- **Categories Management** - Complete category system with CRUD operations and hierarchy support
- **JWT Authentication** - Secure token-based authentication with refresh tokens
- **Role-Based Access Control** - Three user roles: User, Seller, Admin
- **User Management** - Comprehensive profile management system
- **Seller Management** - Complete seller onboarding and verification workflow
- **Admin Dashboard** - Administrative tools for user and seller management
- **Email-based Authentication** - Users authenticate using email addresses
- **Secure Password Management** - Password validation and change functionality

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
- [User Roles](#user-roles)
- [Error Handling](#error-handling)
- [Examples](#examples)

## 🛠 Getting Started

### Prerequisites

```bash
pip install django
pip install djangorestframework
pip install djangorestframework-simplejwt
```

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
4. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
5. Start the development server:
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/api/`

## 🔐 Authentication

Buildmart uses JWT (JSON Web Tokens) for authentication. All endpoints (except registration and login) require authentication.

### Token Structure

- **Access Token**: Valid for 60 minutes
- **Refresh Token**: Valid for 7 days
- **Token Type**: Bearer token

### Authentication Header

```
Authorization: Bearer <access_token>
```

## 👥 User Roles

### User (Default)
- Regular marketplace users
- Can browse products and make purchases
- Has a `Profile` model for personal information

### Seller
- Business users who sell products
- Must go through verification process
- Has a `Seller` model instead of Profile (contains business information)
- Can manage their own products

### Admin
- Full system access
- Can manage all users and sellers
- Can verify/reject seller applications
- Access to system statistics

## 📚 API Endpoints

### Authentication Endpoints

#### Register User
```http
POST /api/accounts/register/
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "password_confirm": "securePassword123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "is_email_verified": false,
    "date_joined": "2025-08-23T10:30:00Z",
    "profile": {
      "id": "uuid-here",
      "full_name": "John Doe",
      "phone": null,
      "address": null
    },
    "seller_profile": null
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  },
  "message": "User registered successfully"
}
```

#### Login
```http
POST /api/accounts/login/
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "user",
    "profile": {...},
    "seller_profile": null
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  },
  "message": "Login successful"
}
```

#### Logout
```http
POST /api/accounts/logout/
```

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Refresh Token
```http
POST /api/accounts/token/refresh/
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### User Management Endpoints

#### Get Current User Profile
```http
GET /api/accounts/profile/
```

**Headers:** `Authorization: Bearer <access_token>`

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "is_email_verified": false,
  "date_joined": "2025-08-23T10:30:00Z",
  "last_login": "2025-08-23T11:00:00Z",
  "profile": {
    "id": "uuid-here",
    "user_email": "user@example.com",
    "user_role": "user",
    "full_name": "John Doe",
    "phone": "+1234567890",
    "address": "123 Main St, City, State",
    "date_of_birth": "1990-01-01",
    "profile_picture": "https://example.com/image.jpg",
    "created_at": "2025-08-23T10:30:00Z",
    "updated_at": "2025-08-23T10:30:00Z"
  },
  "seller_profile": null
}
```

#### Update Current User Profile
```http
PUT /api/accounts/profile/
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith"
}
```

#### Get/Update Profile Details
```http
GET /api/accounts/profile/details/
PUT /api/accounts/profile/details/
```

**PUT Request Body:**
```json
{
  "full_name": "John Smith",
  "phone": "+1234567890",
  "address": "456 Oak Ave, City, State",
  "date_of_birth": "1990-01-01",
  "profile_picture": "https://example.com/new-image.jpg"
}
```

#### Change Password
```http
POST /api/accounts/change-password/
```

**Request Body:**
```json
{
  "old_password": "oldPassword123",
  "new_password": "newPassword456",
  "new_password_confirm": "newPassword456"
}
```

#### Delete Account
```http
DELETE /api/accounts/profile/
```

---

### Seller Endpoints

#### Register as Seller
```http
POST /api/accounts/seller/register/
```

**Request Body:**
```json
{
  "user": {
    "email": "seller@example.com",
    "password": "securePassword123",
    "password_confirm": "securePassword123",
    "first_name": "Jane",
    "last_name": "Business"
  },
  "shop_name": "Jane's Electronics",
  "shop_description": "Quality electronics and gadgets",
  "business_license": "BL123456789",
  "tax_id": "TAX987654321",
  "state": "California",
  "city": "San Francisco",
  "address": "789 Business Blvd, San Francisco, CA",
  "union_membership_number": "UN123456",
  "trial_end_date": "2025-09-23T00:00:00Z"
}
```

**Response:**
```json
{
  "user": {
    "id": 2,
    "email": "seller@example.com",
    "role": "seller",
    "profile": null,
    "seller_profile": {
      "id": "seller-uuid",
      "shop_name": "Jane's Electronics",
      "verification_status": "pending"
    }
  },
  "seller": {
    "id": "seller-uuid",
    "user_email": "seller@example.com",
    "shop_name": "Jane's Electronics",
    "shop_description": "Quality electronics and gadgets",
    "verification_status": "pending",
    "subscription_active": true
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  },
  "message": "Seller registered successfully"
}
```

#### Get Current Seller Profile
```http
GET /api/accounts/seller/profile/
```

**Permissions:** Seller role required

#### Update Current Seller Profile
```http
PUT /api/accounts/seller/profile/
```

**Request Body:**
```json
{
  "shop_name": "Jane's Premium Electronics",
  "shop_description": "Premium quality electronics and gadgets",
  "phone": "+1234567890"
}
```

#### List Sellers
```http
GET /api/accounts/sellers/
```

**Permissions:** 
- Admin: Can see all sellers
- Seller: Can see only their own profile
- User: No access

#### Get Seller Details
```http
GET /api/accounts/sellers/{seller_id}/
```

#### Update Seller Details
```http
PUT /api/accounts/sellers/{seller_id}/
```

**Note:** Only admin can update verification_status

---

### Admin Endpoints

#### List All Users
```http
GET /api/accounts/admin/users/
```

**Permissions:** Admin only

#### Get/Update/Delete User
```http
GET /api/accounts/admin/users/{user_id}/
PUT /api/accounts/admin/users/{user_id}/
DELETE /api/accounts/admin/users/{user_id}/
```

#### List All Profiles
```http
GET /api/accounts/admin/profiles/
```

#### Verify Seller
```http
POST /api/accounts/sellers/{seller_id}/verify/
```

**Request Body:**
```json
{
  "action": "verify"
}
```

**Possible actions:** `verify`, `reject`

#### Get System Statistics
```http
GET /api/accounts/admin/stats/
```

**Response:**
```json
{
  "total_users": 150,
  "total_admins": 5,
  "total_sellers": 45,
  "total_regular_users": 100,
  "verified_sellers": 30,
  "pending_sellers": 10,
  "rejected_sellers": 5
}
```

---

### Categories Endpoints

#### List All Categories
```http
GET /api/products/categories/
```

**Query Parameters:**
- `show_inactive` (boolean): Include inactive categories (default: false)
- `parent` (UUID): Filter by parent category ID
- `search` (string): Search in name and description
- `ordering` (string): Sort by name, created_at, updated_at (prefix with - for descending)

**Response:**
```json
[
  {
    "id": "uuid-here",
    "name": "Electronics",
    "slug": "electronics",
    "icon": "📱",
    "product_count": 25
  },
  {
    "id": "uuid-here", 
    "name": "Clothing",
    "slug": "clothing",
    "icon": "👕",
    "product_count": 15
  }
]
```

#### Create Category
```http
POST /api/products/categories/
```

**Request Body:**
```json
{
  "name": "Electronics",
  "slug": "electronics",
  "description": "Electronic devices and accessories",
  "icon": "📱",
  "parent": null,
  "is_active": true
}
```

**Response:**
```json
{
  "id": "uuid-here",
  "name": "Electronics",
  "slug": "electronics", 
  "description": "Electronic devices and accessories",
  "icon": "📱",
  "parent": null,
  "is_active": true,
  "product_count": 0,
  "created_at": "2025-08-24T10:30:00Z",
  "updated_at": "2025-08-24T10:30:00Z"
}
```

#### Get Category Details
```http
GET /api/products/categories/{id}/
```

**Response:**
```json
{
  "id": "uuid-here",
  "name": "Electronics",
  "slug": "electronics",
  "description": "Electronic devices and accessories", 
  "icon": "📱",
  "parent": null,
  "is_active": true,
  "product_count": 25,
  "created_at": "2025-08-24T10:30:00Z",
  "updated_at": "2025-08-24T10:30:00Z"
}
```

#### Update Category
```http
PUT /api/products/categories/{id}/
PATCH /api/products/categories/{id}/
```

**Request Body (PUT):**
```json
{
  "name": "Electronics & Gadgets",
  "slug": "electronics-gadgets",
  "description": "Electronic devices, gadgets and accessories",
  "icon": "📱",
  "parent": null,
  "is_active": true
}
```

#### Delete Category
```http
DELETE /api/products/categories/{id}/
```

#### Get Root Categories
```http
GET /api/products/categories/root_categories/
```

**Response:** Returns categories without a parent category.

#### Get Subcategories
```http
GET /api/products/categories/subcategories/
```

**Response:** Returns categories that have a parent category.

#### Get Category Children
```http
GET /api/products/categories/{id}/children/
```

**Response:** Returns direct child categories of the specified category.

#### Get Category Products
```http
GET /api/products/categories/{id}/products/
```

**Response:** Returns all active products in the specified category.

---

## ⚠️ Error Handling

### HTTP Status Codes

- `200 OK` - Successful GET/PUT requests
- `201 Created` - Successful POST requests
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "error": "Error message description",
  "details": {
    "field_name": ["Specific field error message"]
  }
}
```

### Common Errors

#### Authentication Errors
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### Permission Errors
```json
{
  "error": "Only admin can update verification status"
}
```

#### Validation Errors
```json
{
  "email": ["This email is already in use."],
  "password": ["Password fields didn't match."]
}
```

---

## 📝 Examples

### Complete User Registration and Profile Update Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securePass123",
    "password_confirm": "securePass123",
    "first_name": "John",
    "last_name": "Doe"
  }'

# 2. Login (get tokens)
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securePass123"
  }'

# 3. Update profile details (use access token from login)
curl -X PUT http://localhost:8000/api/accounts/profile/details/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "full_name": "John Doe",
    "phone": "+1234567890",
    "address": "123 Main St, City, State"
  }'
```

### Seller Registration Flow

```bash
# Register as seller
curl -X POST http://localhost:8000/api/accounts/seller/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "email": "seller@example.com",
      "password": "securePass123",
      "password_confirm": "securePass123",
      "first_name": "Jane",
      "last_name": "Business"
    },
    "shop_name": "Jane'\''s Electronics",
    "state": "California",
    "city": "San Francisco",
    "address": "789 Business Blvd",
    "trial_end_date": "2025-09-23T00:00:00Z"
  }'
```

---

## 🔧 Development

### Project Structure

```
buildmart/
├── accounts/           # User management and authentication
│   ├── models.py      # CustomUser, Profile, Seller models
│   ├── views.py       # API views
│   ├── serializers.py # DRF serializers
│   ├── permissions.py # Custom permissions
│   └── urls.py        # URL routing
├── products/          # Product management (to be documented)
├── chats/            # Chat system (to be documented)
└── buildmart/        # Project settings
    ├── settings.py   # Django settings with JWT config
    └── urls.py       # Main URL configuration
```

### Key Models

- **CustomUser**: Extended user model with role-based authentication
- **Profile**: Personal information for users and admins
- **Seller**: Business information and verification status for sellers

---

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support and questions, please contact the development team or create an issue in the repository.

---

**Buildmart API** - Building the future of online marketplaces 🏗️🛒
