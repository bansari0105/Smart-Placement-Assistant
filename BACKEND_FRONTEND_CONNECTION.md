# Backend-Frontend Connection Guide

## Overview

The Flutter app is now connected to the Flask backend API through the `BackendApiService`. The app uses a **hybrid approach**:

1. **Backend API** - For operations that require server-side processing (scraping, complex operations)
2. **Firebase Direct** - For real-time updates and simple CRUD operations

## Architecture

```
Flutter App
    ├── BackendApiService (lib/services/backend_api_service.dart)
    │   └── Connects to Flask backend (http://10.0.2.2:5000)
    │
    └── FirebaseService (lib/services/firebase_service.dart)
        └── Direct Firestore/Storage access for real-time updates
```

## Backend API Service

### Configuration

Update the `baseUrl` in `lib/services/backend_api_service.dart`:

```dart
// For Android Emulator
static const String baseUrl = "http://10.0.2.2:5000";

// For iOS Simulator
static const String baseUrl = "http://localhost:5000";

// For Physical Device (use your computer's IP)
static const String baseUrl = "http://192.168.1.100:5000";
```

### Available Methods

#### Company Methods
- `getCompanies()` - Get all companies from backend
- `getCompany(String companyId)` - Get company by ID
- `scrapeCompany(String url)` - Scrape a company website
- `createCompany(...)` - Create a company manually

#### Calendar/Events Methods
- `getEvents()` - Get user's events
- `createEvent(...)` - Create a new event
- `deleteEvent(String eventId)` - Delete an event

#### Chat Methods
- `getChatMessages()` - Get chat messages
- `sendChatMessage(String text)` - Send a message

#### Profile Methods
- `getProfile()` - Get user profile
- `updateProfile(Map<String, dynamic> profileData)` - Update profile

#### Auth Methods
- `login(String email, String password)` - Login via backend
- `register(...)` - Register new user

## Authentication

The backend API uses Firebase ID tokens for authentication. The service automatically:

1. Gets the current Firebase user's ID token
2. Adds it to the `Authorization` header as `Bearer <token>`
3. Sends it with each authenticated request

## Usage Examples

### Scraping a Company

```dart
try {
  final result = await BackendApiService.scrapeCompany('https://example.com');
  if (result != null) {
    print('Company scraped: ${result['id']}');
  }
} catch (e) {
  print('Error: $e');
}
```

### Getting Companies

```dart
final companies = await BackendApiService.getCompanies();
```

### Creating an Event

```dart
try {
  final event = await BackendApiService.createEvent(
    title: 'Interview',
    date: '2025-12-31',
    time: '10:00 AM',
    description: 'Technical interview',
    companyName: 'Tech Company',
  );
} catch (e) {
  print('Error: $e');
}
```

## Current Implementation Status

### ✅ Connected to Backend
- **Company List Screen** - Can fetch from backend API or Firebase
- **Company Scraping** - Uses backend API
- **Backend API Service** - Complete service with all endpoints

### ⚠️ Partially Connected
- **Calendar/Events** - Can use backend API (endpoints available) but currently uses Firebase
- **Chat** - Can use backend API (endpoints available) but currently uses Firebase
- **Profile** - Can use backend API (endpoints available) but currently uses Firebase

### 📝 Recommended Approach

1. **Use Backend API for:**
   - Company scraping (required)
   - Complex operations that need server-side processing
   - Operations that need backend validation

2. **Use Firebase Direct for:**
   - Real-time updates (chat, events, notifications)
   - Simple CRUD operations
   - File uploads (Storage)

3. **Hybrid Approach:**
   - Fetch initial data from backend API
   - Use Firebase streams for real-time updates
   - Use backend API for write operations that need validation

## Testing the Connection

### 1. Start Backend Server

```bash
cd lib/backend
python -m app.main
```

### 2. Test from Flutter App

```dart
// Test backend connection
final companies = await BackendApiService.getCompanies();
print('Companies from backend: ${companies.length}');
```

### 3. Test Scraping

```dart
// Scrape a company
final result = await BackendApiService.scrapeCompany('https://example.com');
print('Scraped: $result');
```

## Troubleshooting

### Connection Issues

1. **"Connection refused"** - Make sure backend server is running
2. **"Timeout"** - Check if the URL is correct for your platform
3. **"Unauthorized"** - Make sure user is logged in with Firebase

### Platform-Specific URLs

- **Android Emulator**: `http://10.0.2.2:5000`
- **iOS Simulator**: `http://localhost:5000`
- **Physical Device**: `http://YOUR_COMPUTER_IP:5000`

To find your computer's IP:
- Windows: `ipconfig`
- Mac/Linux: `ifconfig` or `ip addr`

### CORS Issues (Web)

If running on web, you may need to enable CORS in Flask:

```python
from flask_cors import CORS
CORS(app)
```

## Next Steps

1. Update other screens to use backend API where needed
2. Add error handling and retry logic
3. Add loading states for API calls
4. Implement offline caching
5. Add API response caching

