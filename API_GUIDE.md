# Buildmart API Integration Guide

Quick reference for frontend developers integrating with Buildmart API.

## Base URL
```
http://localhost:8000/api/
```

## Authentication
Use JWT Bearer tokens in headers:
```javascript
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

## Quick Start
1. Register/Login to get tokens
2. Use access token for authenticated requests
3. Refresh token when access expires (60min)
4. Include `Authorization` header for protected endpoints

---

## Endpoints Reference

### Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/accounts/register/` | ❌ | Register new user |
| POST | `/accounts/login/` | ❌ | Login user |
| POST | `/accounts/logout/` | ✅ | Logout user |
| POST | `/accounts/token/refresh/` | ❌ | Refresh access token |

### User Profile
| Method | Endpoint | Auth | Role | Description |
|--------|----------|------|------|-------------|
| GET | `/accounts/profile/` | ✅ | Any | Get current user |
| PUT | `/accounts/profile/` | ✅ | Any | Update current user |
| DELETE | `/accounts/profile/` | ✅ | Any | Delete account |
| GET | `/accounts/profile/details/` | ✅ | User/Admin | Get profile details |
| PUT | `/accounts/profile/details/` | ✅ | User/Admin | Update profile details |
| POST | `/accounts/change-password/` | ✅ | Any | Change password |
| POST | `/accounts/verify-email/` | ❌ | Any | Verify email (placeholder) |

### Seller Management
| Method | Endpoint | Auth | Role | Description |
|--------|----------|------|------|-------------|
| POST | `/accounts/seller/register/` | ❌ | Any | Register as seller |
| GET | `/accounts/seller/profile/` | ✅ | Seller | Get current seller profile |
| PUT | `/accounts/seller/profile/` | ✅ | Seller | Update seller profile |
| GET | `/accounts/sellers/` | ✅ | Seller/Admin | List sellers |
| GET | `/accounts/sellers/{id}/` | ✅ | Seller/Admin | Get seller details |
| PUT | `/accounts/sellers/{id}/` | ✅ | Seller/Admin | Update seller |
| DELETE | `/accounts/sellers/{id}/` | ✅ | Admin | Delete seller |
| POST | `/accounts/sellers/{id}/verify/` | ✅ | Admin | Verify/reject seller |

### Admin Only
| Method | Endpoint | Auth | Role | Description |
|--------|----------|------|------|-------------|
| GET | `/accounts/admin/users/` | ✅ | Admin | List all users |
| GET | `/accounts/admin/users/{id}/` | ✅ | Admin | Get user details |
| PUT | `/accounts/admin/users/{id}/` | ✅ | Admin | Update user |
| DELETE | `/accounts/admin/users/{id}/` | ✅ | Admin | Delete user |
| GET | `/accounts/admin/profiles/` | ✅ | Admin | List all profiles |
| GET | `/accounts/admin/stats/` | ✅ | Admin | Get system stats |

### Products (Placeholder)
| Method | Endpoint | Auth | Role | Description |
|--------|----------|------|------|-------------|
| GET | `/products/` | ❌ | Any | List products |
| POST | `/products/` | ✅ | Seller | Create product |
| GET | `/products/{id}/` | ❌ | Any | Get product details |
| PUT | `/products/{id}/` | ✅ | Seller/Admin | Update product |
| DELETE | `/products/{id}/` | ✅ | Seller/Admin | Delete product |

### Chats (Placeholder)
| Method | Endpoint | Auth | Role | Description |
|--------|----------|------|------|-------------|
| GET | `/chats/` | ✅ | Any | List user chats |
| POST | `/chats/` | ✅ | Any | Create chat |
| GET | `/chats/{id}/` | ✅ | Any | Get chat details |
| POST | `/chats/{id}/messages/` | ✅ | Any | Send message |

---

## User Roles
- **User**: Regular customers (default)
- **Seller**: Business users, need verification
- **Admin**: Full system access

## Profile Types
- **Users/Admins**: Have `profile` object with personal info
- **Sellers**: Have `seller_profile` object with business info

---

## Common Request Examples

### Register User
```javascript
POST /accounts/register/
{
  "email": "user@example.com",
  "password": "password123",
  "password_confirm": "password123",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user"
}
```

### Login
```javascript
POST /accounts/login/
{
  "email": "user@example.com",
  "password": "password123"
}
// Returns: { user: {...}, tokens: { access, refresh } }
```

### Get Current User
```javascript
GET /accounts/profile/
// Headers: Authorization: Bearer {access_token}
// Returns: { id, email, role, profile, seller_profile }
```

### Register Seller
```javascript
POST /accounts/seller/register/
{
  "user": {
    "email": "seller@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "Jane",
    "last_name": "Business"
  },
  "shop_name": "Jane's Store",
  "state": "California",
  "city": "San Francisco",
  "address": "123 Business St",
  "trial_end_date": "2025-09-23T00:00:00Z"
}
```

### Update Profile
```javascript
PUT /accounts/profile/details/
{
  "full_name": "John Smith",
  "phone": "+1234567890",
  "address": "456 New St"
}
```

### Change Password
```javascript
POST /accounts/change-password/
{
  "old_password": "oldpass123",
  "new_password": "newpass456",
  "new_password_confirm": "newpass456"
}
```

### Refresh Token
```javascript
POST /accounts/token/refresh/
{
  "refresh": "refresh_token_here"
}
// Returns: { access: "new_access_token" }
```

---

## Error Responses

### 400 Bad Request
```javascript
{
  "email": ["This email is already in use."],
  "password": ["Password fields didn't match."]
}
```

### 401 Unauthorized
```javascript
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```javascript
{
  "error": "Only admin can update verification status"
}
```

---

## Frontend Integration Tips

### Token Management
```javascript
// Store tokens securely
localStorage.setItem('access_token', response.data.tokens.access);
localStorage.setItem('refresh_token', response.data.tokens.refresh);

// Auto-refresh logic
const refreshToken = async () => {
  const refresh = localStorage.getItem('refresh_token');
  const response = await fetch('/accounts/token/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh })
  });
  const data = await response.json();
  localStorage.setItem('access_token', data.access);
};
```

### Role-based UI
```javascript
const user = getCurrentUser(); // from /accounts/profile/
const isAdmin = user.role === 'admin';
const isSeller = user.role === 'seller';
const isUser = user.role === 'user';

// Show/hide components based on role
{isAdmin && <AdminPanel />}
{isSeller && <SellerDashboard />}
```

### Error Handling
```javascript
const handleApiError = (error) => {
  if (error.status === 401) {
    // Token expired, redirect to login
    redirectToLogin();
  } else if (error.status === 403) {
    // Permission denied
    showErrorMessage('Access denied');
  }
};
```

---

## Response Data Structure

### User Object
```javascript
{
  id: 1,
  email: "user@example.com",
  first_name: "John",
  last_name: "Doe",
  role: "user", // "user" | "seller" | "admin"
  is_email_verified: false,
  date_joined: "2025-08-23T10:30:00Z",
  profile: { /* for users/admins */ },
  seller_profile: { /* for sellers */ }
}
```

### Profile Object (Users/Admins)
```javascript
{
  id: "uuid",
  full_name: "John Doe",
  phone: "+1234567890",
  address: "123 Main St",
  date_of_birth: "1990-01-01",
  profile_picture: "https://...",
  created_at: "2025-08-23T10:30:00Z"
}
```

### Seller Profile Object
```javascript
{
  id: "uuid",
  shop_name: "Jane's Store",
  shop_description: "Great products",
  verification_status: "pending", // "pending" | "verified" | "rejected"
  business_license: "BL123",
  state: "California",
  city: "San Francisco",
  subscription_active: true
}
```
