# Test Plan for Smart Placement Assistant

## 1. Backend Scraper Tests

### Unit Tests for HTML Parser
```bash
cd lib/backend
python test_scraper.py
```

### Test Scraper with Firestore
```bash
# Make sure serviceaccountkey.json is in lib/backend/
cd lib/backend
python test_scraper.py
```

### Manual Scraper Test (Python)
```python
from app.services.scraper_service import ScraperService
from firebase_admin import credentials, firestore, initialize_app

# Initialize Firebase
cred = credentials.Certificate('serviceaccountkey.json')
app = initialize_app(cred)
db = firestore.client()

# Test scraper
scraper = ScraperService(db)
doc_id = scraper.scrape_and_save("https://example-company.com")
print(f"Scraped and saved: {doc_id}")
```

### Test Scraper via API (curl)
```bash
# Start Flask server first
# cd lib/backend
# python -m app.main

# Test scrape endpoint (requires auth token)
curl -X POST http://localhost:5000/companies/scrape \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ID_TOKEN" \
  -d '{"url": "https://example-company.com"}'
```

## 2. Backend API Tests

### Test Companies Endpoint
```bash
# Get all companies
curl http://localhost:5000/companies/

# Get specific company
curl http://localhost:5000/companies/COMPANY_ID

# Create company (requires auth)
curl -X POST http://localhost:5000/companies/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ID_TOKEN" \
  -d '{"name": "Test Company", "location": "Test Location", "description": "Test Description"}'
```

### Test Calendar Endpoint
```bash
# Get events (requires auth)
curl http://localhost:5000/calendar/events \
  -H "Authorization: Bearer YOUR_ID_TOKEN"

# Create event (requires auth)
curl -X POST http://localhost:5000/calendar/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ID_TOKEN" \
  -d '{"title": "Test Event", "date": "2025-12-31", "time": "10:00 AM"}'
```

### Test Chat Endpoint
```bash
# Get messages (requires auth)
curl http://localhost:5000/chat/messages \
  -H "Authorization: Bearer YOUR_ID_TOKEN"

# Send message (requires auth)
curl -X POST http://localhost:5000/chat/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ID_TOKEN" \
  -d '{"text": "Hello, world!"}'
```

## 3. Flutter App Tests

### Run Flutter App
```bash
cd /path/to/project
flutter pub get
flutter run
```

### Test Scenarios

#### 1. Authentication
- [ ] Sign up with email/password
- [ ] Login with existing account
- [ ] Logout
- [ ] Auto-login on app restart

#### 2. Company List Screen
- [ ] Companies load from Firestore
- [ ] Company cards display correctly
- [ ] Tap company to view details
- [ ] Pull to refresh updates list
- [ ] Error handling when no companies

#### 3. Company Detail Screen
- [ ] Company details display correctly
- [ ] Skills are shown as chips
- [ ] Location, email, phone displayed
- [ ] Apply button works
- [ ] Calendar event created on apply

#### 4. Resume Upload
- [ ] File picker opens
- [ ] PDF/DOC files can be selected
- [ ] Upload progress shown
- [ ] Resume saved to Firebase Storage
- [ ] Resume metadata saved to Firestore
- [ ] Error handling for failed uploads

#### 5. Resume Gallery
- [ ] User's resumes displayed
- [ ] Resume list updates in real-time
- [ ] Delete resume works
- [ ] File deleted from Storage and Firestore

#### 6. Calendar Screen
- [ ] Events load from Firestore
- [ ] Events display correctly
- [ ] Events update in real-time
- [ ] Delete event works
- [ ] Events sorted by date

#### 7. Chat Screen
- [ ] Messages load from Firestore
- [ ] Real-time message updates
- [ ] Send message works
- [ ] Messages display with sender name
- [ ] Timestamp formatting correct

#### 8. Suggestions Screen
- [ ] Suggestions generated based on profile
- [ ] Suggestions update when profile changes
- [ ] Missing skills identified
- [ ] Error handling works

#### 9. Notifications Screen
- [ ] Notifications load from Firestore
- [ ] Real-time notification updates
- [ ] Notification display correct

## 4. Firebase Integration Tests

### Firestore Rules Test
```bash
# Deploy Firestore rules
firebase deploy --only firestore:rules

# Test rules using Firebase Emulator Suite
firebase emulators:start
```

### Storage Rules Test
```bash
# Deploy Storage rules
firebase deploy --only storage

# Test upload via Flutter app
# Try uploading resume and verify it's saved correctly
```

## 5. Integration Tests

### End-to-End Test Flow
1. User signs up
2. User completes profile
3. User views companies
4. User applies to company
5. Calendar event created automatically
6. User uploads resume
7. User views resume in gallery
8. User sends chat message
9. User views suggestions
10. User logs out

## 6. Performance Tests

### Scraper Performance
- Test scraper with multiple URLs
- Verify rate limiting works
- Check retry logic on failures
- Monitor Firestore write performance

### Flutter App Performance
- Test app startup time
- Test screen load times
- Test real-time updates performance
- Test file upload performance

## 7. Error Handling Tests

### Network Errors
- [ ] Handle no internet connection
- [ ] Handle timeout errors
- [ ] Handle server errors (500, 503)
- [ ] Show user-friendly error messages

### Firebase Errors
- [ ] Handle authentication errors
- [ ] Handle Firestore permission errors
- [ ] Handle Storage upload errors
- [ ] Handle quota exceeded errors

### Validation Errors
- [ ] Validate email format
- [ ] Validate password strength
- [ ] Validate file types for upload
- [ ] Validate required fields

## 8. Security Tests

### Authentication
- [ ] Verify tokens are stored securely
- [ ] Verify tokens are validated on backend
- [ ] Verify unauthorized access is blocked

### Firestore Rules
- [ ] Verify users can only read their own data
- [ ] Verify users can only write their own data
- [ ] Verify companies_scraped is read-only for students

### Storage Rules
- [ ] Verify users can only upload their own files
- [ ] Verify file size limits are enforced
- [ ] Verify file type restrictions work

## Example Test Commands

### Python Scraper Test
```bash
cd lib/backend
python test_scraper.py
```

### Flask API Test
```bash
cd lib/backend
python -m app.main
# In another terminal:
curl http://localhost:5000/
```

### Flutter Test
```bash
flutter test
flutter run
```

### Firestore Rules Test
```bash
firebase emulators:start --only firestore
# Run tests against emulator
```

