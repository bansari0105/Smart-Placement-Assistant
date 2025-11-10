# How to Run the Smart Placement Assistant

## Prerequisites

1. **Python 3.8+** installed
2. **Flutter SDK** installed
3. **Firebase Project** set up
4. **Service Account Key** (`serviceaccountkey.json`) in `lib/backend/` directory
5. **Node.js** (optional, for Firebase CLI)

## Step 1: Backend Setup

### 1.1 Install Python Dependencies

```bash
cd lib/backend
pip install -r requirements.txt
```

Or if using virtual environment (recommended):

```bash
cd lib/backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 1.2 Setup Firebase Service Account

1. Download your Firebase service account key from Firebase Console
2. Place it in `lib/backend/serviceaccountkey.json`
3. Make sure the file path matches what's in `lib/backend/app/config.py`:

```python
FIREBASE_CREDENTIALS = 'serviceaccountkey.json'
```

### 1.3 Configure Backend

Edit `lib/backend/app/config.py` if needed:

```python
class Config:
    SECRET_KEY = 'your-secret-key'
    FIREBASE_CREDENTIALS = 'serviceaccountkey.json'
    FIREBASE_API_KEY = 'your-firebase-api-key'
```

### 1.4 Start Backend Server

```bash
cd lib/backend
python -m app.main
```

Or:

```bash
cd lib/backend
python app/main.py
```

The server should start on `http://localhost:5000` or `http://0.0.0.0:5000`

You should see:
```
 * Running on http://0.0.0.0:5000
```

### 1.5 Test Backend (Optional)

Open a new terminal and test:

```bash
# Test home endpoint
curl http://localhost:5000/

# Should return: {"message":"home route working"}
```

## Step 2: Flutter Setup

### 2.1 Install Flutter Dependencies

```bash
# From project root
flutter pub get
```

### 2.2 Configure Firebase for Flutter

#### Android Setup:
1. Place `google-services.json` in `android/app/` directory
2. Already configured in `android/app/build.gradle`

#### iOS Setup:
1. Place `GoogleService-Info.plist` in `ios/Runner/` directory
2. Already configured in Xcode project

### 2.3 Update Backend URL (if needed)

Edit `lib/services/backend_api_service.dart`:

```dart
// For Android Emulator (default)
static const String baseUrl = "http://10.0.2.2:5000";

// For iOS Simulator
static const String baseUrl = "http://localhost:5000";

// For Physical Device (use your computer's IP address)
// Find IP: Windows (ipconfig) or Mac/Linux (ifconfig)
static const String baseUrl = "http://192.168.1.100:5000";
```

### 2.4 Run Flutter App

```bash
# From project root
flutter run
```

Or run on specific device:

```bash
# List available devices
flutter devices

# Run on specific device
flutter run -d <device-id>
```

## Step 3: Deploy Security Rules (Optional but Recommended)

### 3.1 Install Firebase CLI

```bash
npm install -g firebase-tools
```

### 3.2 Login to Firebase

```bash
firebase login
```

### 3.3 Deploy Rules

```bash
# Deploy Firestore rules
firebase deploy --only firestore:rules

# Deploy Storage rules
firebase deploy --only storage
```

Or manually copy rules from:
- `firestore.rules` → Firebase Console → Firestore → Rules
- `storage.rules` → Firebase Console → Storage → Rules

## Step 4: Testing

### 4.1 Test Backend Connection

1. Open the Flutter app
2. Go to Company List Screen
3. You should see companies (if any exist in Firestore)
4. Tap the cloud download icon to test scraping

### 4.2 Test Scraping

1. In Company List Screen, tap the cloud download icon (☁️)
2. Enter a company URL (e.g., `https://www.google.com`)
3. Tap "Scrape"
4. Wait for scraping to complete
5. Company should appear in the list

### 4.3 Test Authentication

1. Open the app
2. Sign up with email/password
3. User should be created in Firebase
4. Login should work

### 4.4 Test Other Features

- **Companies**: View, scrape, apply
- **Calendar**: Create events, view events
- **Chat**: Send messages, view messages
- **Resume Upload**: Upload PDF, view in gallery
- **Profile**: Update profile information

## Troubleshooting

### Backend Issues

#### "Module not found" or "Import error"
```bash
# Make sure you're in the backend directory
cd lib/backend
pip install -r requirements.txt
```

#### "FIREBASE_API_KEY missing"
- Check `lib/backend/app/config.py`
- Make sure `FIREBASE_API_KEY` is set

#### "Service account key not found"
- Make sure `serviceaccountkey.json` is in `lib/backend/` directory
- Check the path in `config.py`

#### "Port already in use"
```bash
# Kill the process using port 5000
# On Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# On Mac/Linux
lsof -ti:5000 | xargs kill
```

### Flutter Issues

#### "Backend connection failed"
- Make sure backend server is running
- Check the URL in `backend_api_service.dart`
- For physical device, use your computer's IP address
- Check firewall settings

#### "Firebase not initialized"
- Make sure Firebase is configured in `main.dart`
- Check `google-services.json` (Android) or `GoogleService-Info.plist` (iOS)

#### "Build errors"
```bash
flutter clean
flutter pub get
flutter run
```

### Platform-Specific Issues

#### Android Emulator
- Use `http://10.0.2.2:5000` for backend URL
- Make sure backend is running on your computer

#### iOS Simulator
- Use `http://localhost:5000` for backend URL
- Make sure backend is running on your computer

#### Physical Device
1. Find your computer's IP address:
   - Windows: `ipconfig` (look for IPv4 Address)
   - Mac/Linux: `ifconfig` or `ip addr`
2. Update backend URL to `http://YOUR_IP:5000`
3. Make sure your phone and computer are on the same network
4. Make sure firewall allows connections on port 5000

## Quick Start Commands

### Backend (Terminal 1)
```bash
cd lib/backend
pip install -r requirements.txt
python -m app.main
```

### Flutter (Terminal 2)
```bash
flutter pub get
flutter run
```

## Development Workflow

1. **Start Backend**: Always start backend server first
2. **Start Flutter**: Then run Flutter app
3. **Test Features**: Test each feature as you develop
4. **Check Logs**: Monitor backend logs and Flutter debug console
5. **Deploy Rules**: Deploy Firestore/Storage rules when ready

## Production Deployment

### Backend
- Deploy to cloud platform (Heroku, AWS, GCP, etc.)
- Update backend URL in Flutter app
- Set environment variables for production

### Flutter
- Build release APK/IPA
- Test on physical devices
- Deploy to app stores

## Additional Resources

- **Backend API Docs**: See `BACKEND_FRONTEND_CONNECTION.md`
- **Test Plan**: See `TEST_PLAN.md`
- **Quick Start**: See `QUICK_START.md`
- **Changes Summary**: See `CHANGES_SUMMARY.md`

## Need Help?

1. Check the troubleshooting section
2. Check Firebase Console for errors
3. Check backend logs for errors
4. Check Flutter debug console for errors
5. Verify all prerequisites are installed
6. Verify Firebase is configured correctly

