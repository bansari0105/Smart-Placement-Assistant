// import 'package:flutter/material.dart';
// import 'package:firebase_core/firebase_core.dart';

// import 'screens/home_screen.dart';
// import 'screens/login_screen.dart';
// import 'screens/signup_screen.dart';
// import 'screens/wrapper_screen.dart';

// void main() async {
//   WidgetsFlutterBinding.ensureInitialized();
//   await Firebase.initializeApp();
//   runApp(const MyApp());
// }

// class MyApp extends StatelessWidget {
//   const MyApp({super.key});

//   @override
//   Widget build(BuildContext context) {
//     return MaterialApp(
//       title: 'Auth UI',
//       debugShowCheckedModeBanner: false,
//       theme: ThemeData(useMaterial3: false),
//       initialRoute: '/',
//       routes: {
//         '/': (_) => const WrapperScreen(),
//         '/home': (_) => const HomeScreen(),
//         '/login': (_) => const LoginScreen(),
//         '/signup': (_) => const SignUpScreen(),
//       },
//     );
//   }
// }


// import 'package:flutter/material.dart';
// import 'package:firebase_core/firebase_core.dart';

// // Import all screens
// import 'screens/wrapper_screen.dart';
// import 'screens/home_screen.dart';
// import 'screens/login_screen.dart';
// import 'screens/signup_screen.dart';
// import 'screens/profile_setup_screen.dart';
// import 'screens/resume_upload_screen.dart';
// import 'screens/suggestions_screen.dart';
// import 'screens/company_list_screen.dart';
// import 'screens/company_detail_screen.dart';
// import 'screens/notifications_screen.dart';
// import 'screens/chat_screen.dart';
// import 'screens/resume_gallery_screen.dart';
// import 'screens/calender_screen.dart';

// void main() async {
//   WidgetsFlutterBinding.ensureInitialized();
//   await Firebase.initializeApp();
//   runApp(const MyApp());
// }

// class MyApp extends StatelessWidget {
//   const MyApp({super.key});

//   @override
//   Widget build(BuildContext context) {
//     return MaterialApp(
//       title: 'Smart Placement Assistant',
//       debugShowCheckedModeBanner: false,
//       theme: ThemeData(
//         useMaterial3: true,
//         colorSchemeSeed: Colors.blue,
//       ),
//       initialRoute: '/',
//       routes: {
//         '/': (_) => const WrapperScreen(),
//         '/home': (_) => const HomeScreen(),
//         '/login': (_) => const LoginScreen(),
//         '/signup': (_) => const SignUpScreen(),
//         '/profile-setup': (_) => const ProfileSetupScreen(),
//         '/resume-upload': (_) => const ResumeUploadScreen(),
//         '/suggestions': (_) => const SuggestionsScreen(),
//         '/companies': (_) => const CompanyListScreen(),
//         // For company details, use MaterialPageRoute dynamically (not here)
//         '/notifications': (_) => const NotificationsScreen(),
//         '/chat': (_) => const ChatScreen(),
//         '/resume-gallery': (_) => const ResumeGalleryScreen(),
//         '/calendar': (_) => const CalenderScreen(),
//       },
//     );
//   }
// }


import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';

// Import your screens
import 'screens/wrapper_screen.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/signup_screen.dart';
import 'screens/profile_setup_screen.dart';
import 'screens/resume_upload_screen.dart';
import 'screens/suggestions_screen.dart';
import 'screens/company_list_screen.dart';
import 'screens/notifications_screen.dart';
import 'screens/chat_screen.dart';
import 'screens/resume_gallery_screen.dart';
import 'screens/calender_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  if (kIsWeb) {
    // ✅ Initialize Firebase for Web
    await Firebase.initializeApp(
      options: const FirebaseOptions(
        apiKey: "AIzaSyBaC-6ec5WCKTFeqQn0bOL1wILtY1hm-ZY", // replace with your web API key
        authDomain: "smart-placement-assistan-a54bd.firebaseapp.com",
        projectId: "smart-placement-assistan-a54bd",
        storageBucket: "smart-placement-assistan-a54bd.firebasestorage.app",
        messagingSenderId:"905464757558",
        appId: "1:905464757558:web:a969081156ccf8876a8797",
      ),
    );
  } else {
    // ✅ Initialize Firebase for mobile
    await Firebase.initializeApp();
  }

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Placement Assistant',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: Colors.blue,
      ),
      initialRoute: '/',
      routes: {
        '/': (_) => const WrapperScreen(),
        '/home': (_) => const HomeScreen(),
        '/login': (_) => const LoginScreen(),
        '/signup': (_) => const SignUpScreen(),
        '/profile-setup': (_) => const ProfileSetupScreen(),
        '/resume-upload': (_) => const ResumeUploadScreen(),
        '/suggestions': (_) => const SuggestionsScreen(),
        '/companies': (_) => const CompanyListScreen(),
        '/notifications': (_) => const NotificationsScreen(),
        '/chat': (_) => const ChatScreen(),
        '/resume-gallery': (_) => const ResumeGalleryScreen(),
        '/calendar': (_) => const CalenderScreen(),
      },
    );
  }
}
