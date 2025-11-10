# Quick Start Checklist

## ✅ Pre-flight Checks

- [ ] Python 3.8+ installed
- [ ] Flutter SDK installed
- [ ] Firebase project created
- [ ] Service account key downloaded (`serviceaccountkey.json`)
- [ ] `google-services.json` (Android) or `GoogleService-Info.plist` (iOS) downloaded

## 🚀 Step-by-Step Run Guide

### Step 1: Backend Setup (5 minutes)

1. **Install Dependencies**
   ```bash
   cd lib/backend
   pip install -r requirements.txt
   ```

2. **Place Service Account Key**
   - Copy `serviceaccountkey.json` to `lib/backend/` directory

3. **Start Backend Server**
   ```bash
   python -m app.main
   ```
   - Should see: `Running on http://0.0.0.0:5000`
   - ✅ Backend is running!

### Step 2: Flutter Setup (2 minutes)

1. **Install Flutter Dependencies**
   ```bash
   flutter pub get
   ```

2. **Configure Firebase**
   - Android: Place `google-services.json` in `android/app/`
   - iOS: Place `GoogleService-Info.plist` in `ios/Runner/`

3. **Update Backend URL (if needed)**
   - Edit `lib/services/backend_api_service.dart`
   - For Android Emulator: `http://10.0.2.2:5000` (already set)
   - For iOS Simulator: `http://localhost:5000`
   - For Physical Device: `http://YOUR_COMPUTER_IP:5000`

4. **Run Flutter App**
   ```bash
   flutter run
   ```
   - ✅ App is running!

### Step 3: Test (2 minutes)

1. **Test Backend Connection**
   - Open app → Company List Screen
   - Should see companies or empty list

2. **Test Scraping**
   - Tap cloud download icon (☁️)
   - Enter URL: `https://www.google.com`
   - Tap "Scrape"
   - Wait for completion
   - ✅ Company should appear!

3. **Test Authentication**
   - Sign up with email/password
   - Login
   - ✅ Authentication works!

## 🎯 Quick Commands

### Windows
```bash
# Terminal 1: Start Backend
cd lib\backend
python -m app.main

# Terminal 2: Start Flutter
flutter run
```

### Mac/Linux
```bash
# Terminal 1: Start Backend
cd lib/backend
python -m app.main

# Terminal 2: Start Flutter
flutter run
```

## 🔧 Common Issues & Solutions

### Backend won't start
- ✅ Check Python is installed: `python --version`
- ✅ Check dependencies: `pip install -r requirements.txt`
- ✅ Check service account key is in `lib/backend/`

### Flutter can't connect to backend
- ✅ Check backend is running on port 5000
- ✅ Check backend URL in `backend_api_service.dart`
- ✅ For physical device, use computer's IP address
- ✅ Check firewall allows port 5000

### Firebase errors
- ✅ Check `google-services.json` (Android) or `GoogleService-Info.plist` (iOS)
- ✅ Check Firebase is initialized in `main.dart`
- ✅ Check Firebase project is active in Firebase Console

## 📱 Platform-Specific URLs

| Platform | Backend URL |
|----------|-------------|
| Android Emulator | `http://10.0.2.2:5000` |
| iOS Simulator | `http://localhost:5000` |
| Physical Device | `http://YOUR_COMPUTER_IP:5000` |

## 🎉 You're Ready!

Once both backend and Flutter are running:

1. ✅ Backend server running on port 5000
2. ✅ Flutter app running on device/emulator
3. ✅ Companies can be scraped
4. ✅ Data syncs with Firestore
5. ✅ All features working!

## 📚 Next Steps

- Read `HOW_TO_RUN.md` for detailed instructions
- Read `BACKEND_FRONTEND_CONNECTION.md` for API details
- Read `TEST_PLAN.md` for testing guide
- Deploy security rules to Firebase
- Test all features
- Deploy to production

## 🆘 Need Help?

1. Check `HOW_TO_RUN.md` for detailed guide
2. Check troubleshooting section
3. Check backend logs
4. Check Flutter debug console
5. Verify all prerequisites

