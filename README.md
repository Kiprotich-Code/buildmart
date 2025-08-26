# Buildmart API

**Buildmart** is a modern marketplace platform built with Django REST Framework, featuring JWT authentication, role-based access control, and comprehensive user management for buyers, sellers, and administrators.

## 🚀 Features

- **Categories Management** - Complete category system with CRUD operations and hierarchy support
- **Products Management** - Full product catalog with advanced filtering, search, and seller management
- **Product Image Upload** - Production-ready image upload system with Pillow processing, automatic optimization, and thumbnail generation
- **Single-Step Product Creation** - Create products with images in one API call for improved efficiency
- **Real-time Chat System** - WebSocket-powered messaging between buyers and sellers with admin monitoring
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
pip install channels
pip install channels-redis
pip install django-cors-headers
pip install Pillow
pip install redis
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

### Products Endpoints

#### List All Products
```http
GET /api/products/products/
```

**Query Parameters:**
- `show_inactive` (boolean): Include inactive products (default: false)
- `category` (UUID): Filter by category ID
- `seller` (UUID): Filter by seller ID
- `min_price` (decimal): Minimum price filter
- `max_price` (decimal): Maximum price filter
- `in_stock` (boolean): Show only products with quantity > 0
- `boosted_only` (boolean): Show only boosted products
- `search` (string): Search in name, description, and seller name
- `ordering` (string): Sort by name, price, created_at, updated_at (prefix with - for descending)

**Response:**
```json
[
  {
    "id": "uuid-here",
    "name": "Premium Portland Cement",
    "price": "25.50",
    "quantity": 100,
    "images": ["https://example.com/image1.jpg"],
    "image_urls": ["/media/products/images/image1.jpg"],
    "thumbnail_urls": ["/media/products/images/thumb_image1.jpg"],
    "primary_image_url": "/media/products/images/image1.jpg",
    "category": "uuid-here",
    "category_name": "Cement",
    "seller": "uuid-here",
    "seller_name": "John Construction Supply",
    "is_active": true,
    "is_boosted": false,
    "review_count": 5,
    "average_rating": 4.2,
    "created_at": "2025-08-24T10:30:00Z"
  }
]
```

#### Create Product
```http
POST /api/products/products/
```

**Authentication:** Required (Seller or Admin)

**Request Body:**
```json
{
  "name": "Premium Portland Cement",
  "description": "High-quality Portland cement for construction projects",
  "price": "25.50",
  "quantity": 100,
  "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
  "category": "f1c28ad9-613e-4fcc-8790-f4a07a9a3a14",
  "is_active": true
}
```

**Response:**
```json
{
  "id": "uuid-here",
  "name": "Premium Portland Cement",
  "description": "High-quality Portland cement for construction projects",
  "price": "25.50",
  "quantity": 100,
  "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
  "image_urls": ["/media/products/images/image1.jpg", "/media/products/images/image2.jpg"],
  "thumbnail_urls": ["/media/products/images/thumb_image1.jpg", "/media/products/images/thumb_image2.jpg"],
  "product_images": [
    {
      "id": "image-uuid",
      "image": "/media/products/images/image1.jpg",
      "thumbnail": "/media/products/images/thumb_image1.jpg",
      "alt_text": "Product front view",
      "order": 0,
      "width": 1200,
      "height": 900,
      "file_size": 245760,
      "created_at": "2025-08-26T10:30:00Z"
    }
  ],
  "category": "f1c28ad9-613e-4fcc-8790-f4a07a9a3a14",
  "category_name": "Cement",
  "seller": "uuid-here",
  "seller_name": "John Construction Supply",
  "seller_email": "john@example.com",
  "is_active": true,
  "is_boosted": false,
  "boost_expires_at": null,
  "review_count": 0,
  "average_rating": null,
  "recent_reviews": [],
  "can_chat": true,
  "existing_chat_id": null,
  "created_at": "2025-08-24T10:30:00Z",
  "updated_at": "2025-08-24T10:30:00Z"
}
```

#### Create Product with Images (One API Call) 🆕
```http
POST /api/products/products/
Content-Type: multipart/form-data
```

**Authentication:** Required (Seller or Admin)

**Description:** Create a product and upload images simultaneously in a single API call. This is the recommended approach for creating products with images as it's more efficient than the two-step process.

**Form Data Fields:**
- `name` (string, required): Product name
- `description` (string, optional): Product description
- `price` (decimal, required): Product price
- `quantity` (integer, required): Available quantity
- `category` (UUID, required): Category ID
- `images` (file[], optional): Array of image files (max 10 images)
- `alt_texts` (string[], optional): Alt text for each image (same order as images)
- `is_active` (boolean, optional): Product status (default: true)

**cURL Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "name=Premium Steel Beams" \
  -F "description=High-grade steel beams for construction" \
  -F "price=450.00" \
  -F "quantity=25" \
  -F "category=f1c28ad9-613e-4fcc-8790-f4a07a9a3a14" \
  -F "images=@beam1.jpg" \
  -F "images=@beam2.jpg" \
  -F "images=@beam3.jpg" \
  -F "alt_texts=Steel beam front view" \
  -F "alt_texts=Steel beam side view" \
  -F "alt_texts=Steel beam dimensions" \
  http://localhost:8000/api/products/products/
```

**JavaScript/FormData Example:**
```javascript
const formData = new FormData();
formData.append('name', 'Premium Steel Beams');
formData.append('description', 'High-grade steel beams for construction');
formData.append('price', '450.00');
formData.append('quantity', '25');
formData.append('category', 'f1c28ad9-613e-4fcc-8790-f4a07a9a3a14');

// Add multiple images
formData.append('images', beamImage1File);  // File object
formData.append('images', beamImage2File);  // File object
formData.append('images', beamImage3File);  // File object

// Add alt texts
formData.append('alt_texts', 'Steel beam front view');
formData.append('alt_texts', 'Steel beam side view');
formData.append('alt_texts', 'Steel beam dimensions');

fetch('/api/products/products/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + token
  },
  body: formData
});
```

**Response:**
```json
{
  "id": "new-product-uuid",
  "name": "Premium Steel Beams",
  "description": "High-grade steel beams for construction",
  "price": "450.00",
  "quantity": 25,
  "images": [],  // Legacy field - empty for new products
  "image_urls": [
    "/media/products/images/beam1-uuid.jpg",
    "/media/products/images/beam2-uuid.jpg", 
    "/media/products/images/beam3-uuid.jpg"
  ],
  "thumbnail_urls": [
    "/media/products/images/beam1-uuid_thumb.jpg",
    "/media/products/images/beam2-uuid_thumb.jpg",
    "/media/products/images/beam3-uuid_thumb.jpg"
  ],
  "primary_image_url": "/media/products/images/beam1-uuid.jpg",
  "product_images": [
    {
      "id": "image1-uuid",
      "image": "/media/products/images/beam1-uuid.jpg",
      "thumbnail": "/media/products/images/beam1-uuid_thumb.jpg",
      "alt_text": "Steel beam front view",
      "order": 0,
      "width": 1200,
      "height": 800,
      "file_size": 342156,
      "created_at": "2025-08-26T10:30:00Z"
    },
    {
      "id": "image2-uuid",
      "image": "/media/products/images/beam2-uuid.jpg",
      "thumbnail": "/media/products/images/beam2-uuid_thumb.jpg",
      "alt_text": "Steel beam side view", 
      "order": 1,
      "width": 1200,
      "height": 800,
      "file_size": 298745,
      "created_at": "2025-08-26T10:30:00Z"
    },
    {
      "id": "image3-uuid",
      "image": "/media/products/images/beam3-uuid.jpg",
      "thumbnail": "/media/products/images/beam3-uuid_thumb.jpg",
      "alt_text": "Steel beam dimensions",
      "order": 2,
      "width": 1200,
      "height": 800, 
      "file_size": 315642,
      "created_at": "2025-08-26T10:30:00Z"
    }
  ],
  "category": "f1c28ad9-613e-4fcc-8790-f4a07a9a3a14",
  "category_name": "Steel & Metal",
  "seller": "seller-uuid",
  "seller_name": "Steel Supply Co",
  "seller_email": "sales@steelsupply.com",
  "is_active": true,
  "is_boosted": false,
  "boost_expires_at": null,
  "review_count": 0,
  "average_rating": null,
  "recent_reviews": [],
  "can_chat": false,  // Can't chat with yourself
  "existing_chat_id": null,
  "created_at": "2025-08-26T10:30:00Z",
  "updated_at": "2025-08-26T10:30:00Z"
}
```

#### Get Product Details
```http
GET /api/products/products/{id}/
```

**Response:**
```json
{
  "id": "uuid-here",
  "name": "Premium Portland Cement",
  "description": "High-quality Portland cement for construction projects",
  "price": "25.50",
  "quantity": 100,
  "images": ["https://example.com/image1.jpg"],
  "image_urls": ["/media/products/images/image1.jpg"],
  "thumbnail_urls": ["/media/products/images/thumb_image1.jpg"],
  "product_images": [
    {
      "id": "image-uuid",
      "image": "/media/products/images/image1.jpg",
      "thumbnail": "/media/products/images/thumb_image1.jpg",
      "alt_text": "Product front view",
      "order": 0,
      "width": 1200,
      "height": 900,
      "file_size": 245760,
      "created_at": "2025-08-26T10:30:00Z"
    }
  ],
  "category": "f1c28ad9-613e-4fcc-8790-f4a07a9a3a14",
  "category_name": "Cement",
  "seller": "uuid-here",
  "seller_name": "John Construction Supply",
  "seller_email": "john@example.com",
  "is_active": true,
  "is_boosted": false,
  "boost_expires_at": null,
  "review_count": 5,
  "average_rating": 4.2,
  "recent_reviews": [
    {
      "id": "uuid-here",
      "user_name": "Jane Smith",
      "rating": 5,
      "comment": "Excellent quality cement!",
      "created_at": "2025-08-23T15:30:00Z"
    }
  ],
  "can_chat": true,
  "existing_chat_id": "chat-uuid-here",
  "created_at": "2025-08-24T10:30:00Z",
  "updated_at": "2025-08-24T10:30:00Z"
}
```

#### Update Product
```http
PUT /api/products/products/{id}/
PATCH /api/products/products/{id}/
```

**Authentication:** Required (Product owner or Admin)

**Request Body (PUT):**
```json
{
  "name": "Updated Premium Portland Cement",
  "description": "Updated description",
  "price": "27.50",
  "quantity": 150,
  "images": ["https://example.com/new-image.jpg"],
  "category": "f1c28ad9-613e-4fcc-8790-f4a07a9a3a14",
  "is_active": true
}
```

#### Delete Product
```http
DELETE /api/products/products/{id}/
```

**Authentication:** Required (Product owner or Admin)

#### Get Featured Products
```http
GET /api/products/products/featured/
```

**Response:** Returns boosted/promoted products.

#### Get Popular Products
```http
GET /api/products/products/popular/
```

**Response:** Returns products with high ratings (4.0+) and multiple reviews (3+).

#### Get My Products
```http
GET /api/products/products/my_products/
```

**Authentication:** Required

**Response:** Returns products owned by the current user.

#### Get Product Reviews
```http
GET /api/products/products/{id}/reviews/
```

**Response:** Returns all reviews for the specified product.

#### Toggle Product Active Status
```http
POST /api/products/products/{id}/toggle_active/
```

**Authentication:** Required (Product owner or Admin)

**Response:**
```json
{
  "message": "Product activated successfully",
  "product": {
    "id": "uuid-here",
    "name": "Premium Portland Cement",
    "is_active": true,
    // ... other product fields
  }
}
```

#### Upload Product Images
```http
POST /api/products/products/{id}/upload_images/
```

**Authentication:** Required (Product owner or Admin)

**Content-Type:** `multipart/form-data`

**Form Data:**
- `images`: List of image files (max 10 images per product)
- `alt_texts`: Optional list of alt texts for images (same order as images)

**Example using curl:**
```bash
curl -X POST \
  http://localhost:8000/api/products/products/{product_id}/upload_images/ \
  -H "Authorization: Bearer your-jwt-token" \
  -F "images=@image1.jpg" \
  -F "images=@image2.png" \
  -F "alt_texts=Product front view" \
  -F "alt_texts=Product side view"
```

**Response:**
```json
{
  "message": "Successfully uploaded 2 images",
  "images": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "image": "/media/products/images/550e8400-e29b-41d4-a716-446655440000.jpg",
      "thumbnail": "/media/products/images/thumb_550e8400-e29b-41d4-a716-446655440000.jpg",
      "alt_text": "Product front view",
      "order": 0,
      "width": 1200,
      "height": 900,
      "file_size": 245760,
      "created_at": "2025-08-26T10:30:00Z"
    }
  ]
}
```

#### Get Product Images
```http
GET /api/products/products/{id}/images/
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "image": "/media/products/images/550e8400-e29b-41d4-a716-446655440000.jpg",
    "thumbnail": "/media/products/images/thumb_550e8400-e29b-41d4-a716-446655440000.jpg",
    "alt_text": "Product front view",
    "order": 0,
    "width": 1200,
    "height": 900,
    "file_size": 245760,
    "created_at": "2025-08-26T10:30:00Z"
  }
]
```

#### Reorder Product Images
```http
POST /api/products/products/{id}/reorder_images/
```

**Authentication:** Required (Product owner or Admin)

**Request Body:**
```json
{
  "image_orders": [
    {"id": "550e8400-e29b-41d4-a716-446655440000", "order": 0},
    {"id": "550e8400-e29b-41d4-a716-446655440001", "order": 1}
  ]
}
```

**Response:**
```json
{
  "message": "Images reordered successfully"
}
```

#### Delete Product Image
```http
DELETE /api/products/products/{id}/delete_image/?image_id={image_id}
```

**Authentication:** Required (Product owner or Admin)

**Response:**
```json
{
  "message": "Image deleted successfully"
}
```

#### Start Chat About Product
```http
POST /api/products/products/{id}/start_chat/
```

**Authentication:** Required

**Description:** Start a chat conversation with the product seller.

**Response:**
```json
{
  "message": "Chat started successfully",
  "chat": {
    "id": "chat-uuid-here",
    "buyer": "buyer-uuid",
    "seller": "seller-uuid", 
    "product": "product-uuid",
    "is_active": true,
    "created_at": "2025-08-26T10:30:00Z"
  },
  "created": true
}
```

---

### Chat System Endpoints

The chat system enables real-time communication between buyers and sellers about specific products. It includes WebSocket support for real-time messaging and comprehensive admin monitoring features.

#### List User's Chats
```http
GET /api/chats/chats/
```

**Authentication:** Required

**Description:** Get all active chats for the current user (buyer or seller).

**Response:**
```json
[
  {
    "id": "chat-uuid-here",
    "buyer": {
      "id": "buyer-uuid",
      "email": "buyer@example.com",
      "full_name": "John Buyer"
    },
    "seller": {
      "id": "seller-uuid", 
      "email": "seller@example.com",
      "full_name": "Jane Seller"
    },
    "product": {
      "id": "product-uuid",
      "name": "Premium Portland Cement",
      "category_name": "Cement"
    },
    "last_message_at": "2025-08-26T15:30:00Z",
    "unread_count": 2,
    "last_message": {
      "content": "Is this still available?",
      "sender_name": "John Buyer",
      "created_at": "2025-08-26T15:30:00Z"
    },
    "is_active": true,
    "created_at": "2025-08-26T10:00:00Z"
  }
]
```

#### Create New Chat
```http
POST /api/chats/chats/
```

**Authentication:** Required

**Request Body:**
```json
{
  "seller": "seller-uuid-here",
  "product": "product-uuid-here"
}
```

**Response:**
```json
{
  "id": "new-chat-uuid",
  "buyer": {...},
  "seller": {...},
  "product": {...},
  "is_active": true,
  "created_at": "2025-08-26T16:00:00Z"
}
```

#### Get Chat Messages
```http
GET /api/chats/chats/{chat_id}/messages/
```

**Authentication:** Required (Chat participant only)

**Description:** Get all messages in a specific chat. Automatically marks messages as read.

**Response:**
```json
[
  {
    "id": "message-uuid",
    "sender": {
      "id": "user-uuid",
      "full_name": "John Buyer",
      "email": "buyer@example.com"
    },
    "message_type": "text",
    "content": "Is this cement still available?",
    "file_url": null,
    "is_read": true,
    "is_edited": false,
    "created_at": "2025-08-26T15:30:00Z"
  },
  {
    "id": "message-uuid-2",
    "sender": {
      "id": "seller-uuid",
      "full_name": "Jane Seller",
      "email": "seller@example.com"
    },
    "message_type": "text",
    "content": "Yes, we have 100 bags in stock!",
    "file_url": null,
    "is_read": false,
    "is_edited": false,
    "created_at": "2025-08-26T15:35:00Z"
  }
]
```

#### Send Message
```http
POST /api/chats/chats/{chat_id}/send_message/
```

**Authentication:** Required (Chat participant only)

**Request Body:**
```json
{
  "message_type": "text",
  "content": "What's the price for bulk orders?"
}
```

**For image/file messages:**
```json
{
  "message_type": "image",
  "content": "Here's a photo of the product",
  "file_url": "https://example.com/image.jpg"
}
```

**Response:**
```json
{
  "id": "new-message-uuid",
  "sender": {
    "id": "user-uuid",
    "full_name": "John Buyer",
    "email": "buyer@example.com"
  },
  "message_type": "text",
  "content": "What's the price for bulk orders?",
  "file_url": null,
  "is_read": false,
  "is_edited": false,
  "created_at": "2025-08-26T16:00:00Z"
}
```

#### Mark Messages as Read
```http
PATCH /api/chats/chats/{chat_id}/mark_as_read/
```

**Authentication:** Required (Chat participant only)

**Response:**
```json
{
  "message": "3 messages marked as read"
}
```

#### Get Unread Count
```http
GET /api/chats/chats/unread_count/
```

**Authentication:** Required

**Response:**
```json
{
  "unread_count": 5
}
```

#### Update Message
```http
PUT /api/chats/messages/{message_id}/
PATCH /api/chats/messages/{message_id}/
```

**Authentication:** Required (Message sender only)

**Request Body:**
```json
{
  "content": "Updated message content"
}
```

#### Delete Message
```http
DELETE /api/chats/messages/{message_id}/
```

**Authentication:** Required (Message sender only)

#### Flag Chat (Report)
```http
POST /api/chats/chats/{chat_id}/flag/
```

**Authentication:** Required

**Request Body:**
```json
{
  "reason": "Inappropriate content or spam"
}
```

**Response:**
```json
{
  "message": "Chat flagged successfully"
}
```

### Admin Chat Monitoring

#### Get All Chats (Admin)
```http
GET /api/chats/chats/admin_all_chats/
```

**Authentication:** Admin required

**Query Parameters:**
- `status`: 'active', 'archived', 'all' (default: 'all')
- `is_flagged`: true/false to filter flagged chats
- `search`: Search in buyer/seller emails or product names
- `date_from`: Filter chats created from this date (YYYY-MM-DD)
- `date_to`: Filter chats created to this date (YYYY-MM-DD)

#### Get Chat Statistics (Admin)
```http
GET /api/chats/chats/admin_chat_stats/
```

**Authentication:** Admin required

**Response:**
```json
{
  "total_chats": 150,
  "active_chats": 120,
  "flagged_chats": 5,
  "total_messages": 2500,
  "chats_today": 10,
  "messages_today": 45
}
```

### WebSocket Support

The chat system supports real-time messaging via WebSockets. Connect to:

```
ws://localhost:8000/ws/chat/{chat_id}/
```

**WebSocket Message Format:**
```json
{
  "type": "chat_message",
  "message": {
    "id": "message-uuid",
    "content": "Real-time message",
    "sender": {...},
    "created_at": "2025-08-26T16:00:00Z"
  }
}
```

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
