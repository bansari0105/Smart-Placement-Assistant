import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';

/// Backend API Service for connecting Flutter app to Flask backend
class BackendApiService {
  // Update this to match your backend URL
  // For Android Emulator: http://10.0.2.2:5000
  // For iOS Simulator: http://localhost:5000
  // For physical device: http://YOUR_COMPUTER_IP:5000
  static const String baseUrl = "http://10.0.2.2:5000";

  /// Get Firebase ID token for authentication
  static Future<String?> _getIdToken() async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      if (user == null) return null;
      return await user.getIdToken();
    } catch (e) {
      print("Error getting ID token: $e");
      return null;
    }
  }

  /// Make authenticated GET request
  static Future<Map<String, dynamic>?> _get(
    String endpoint, {
    bool requiresAuth = false,
  }) async {
    try {
      final headers = <String, String>{
        'Content-Type': 'application/json',
      };

      if (requiresAuth) {
        final token = await _getIdToken();
        if (token == null) {
          throw Exception('User not authenticated');
        }
        headers['Authorization'] = 'Bearer $token';
      }

      final response = await http.get(
        Uri.parse('$baseUrl$endpoint'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        print("GET Error: ${response.statusCode} - ${response.body}");
        return null;
      }
    } catch (e) {
      print("GET Request Error: $e");
      return null;
    }
  }

  /// Make authenticated POST request
  static Future<Map<String, dynamic>?> _post(
    String endpoint,
    Map<String, dynamic> body, {
    bool requiresAuth = false,
  }) async {
    try {
      final headers = <String, String>{
        'Content-Type': 'application/json',
      };

      if (requiresAuth) {
        final token = await _getIdToken();
        if (token == null) {
          throw Exception('User not authenticated');
        }
        headers['Authorization'] = 'Bearer $token';
      }

      final response = await http.post(
        Uri.parse('$baseUrl$endpoint'),
        headers: headers,
        body: jsonEncode(body),
      );

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        print("POST Error: ${response.statusCode} - ${response.body}");
        final errorData = jsonDecode(response.body) as Map<String, dynamic>?;
        throw Exception(errorData?['error'] ?? 'Request failed');
      }
    } catch (e) {
      print("POST Request Error: $e");
      rethrow;
    }
  }

  /// Make authenticated PUT request
  static Future<Map<String, dynamic>?> _put(
    String endpoint,
    Map<String, dynamic> body, {
    bool requiresAuth = false,
  }) async {
    try {
      final headers = <String, String>{
        'Content-Type': 'application/json',
      };

      if (requiresAuth) {
        final token = await _getIdToken();
        if (token == null) {
          throw Exception('User not authenticated');
        }
        headers['Authorization'] = 'Bearer $token';
      }

      final response = await http.put(
        Uri.parse('$baseUrl$endpoint'),
        headers: headers,
        body: jsonEncode(body),
      );

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        print("PUT Error: ${response.statusCode} - ${response.body}");
        return null;
      }
    } catch (e) {
      print("PUT Request Error: $e");
      return null;
    }
  }

  /// Make authenticated DELETE request
  static Future<bool> _delete(
    String endpoint, {
    bool requiresAuth = false,
  }) async {
    try {
      final headers = <String, String>{
        'Content-Type': 'application/json',
      };

      if (requiresAuth) {
        final token = await _getIdToken();
        if (token == null) {
          throw Exception('User not authenticated');
        }
        headers['Authorization'] = 'Bearer $token';
      }

      final response = await http.delete(
        Uri.parse('$baseUrl$endpoint'),
        headers: headers,
      );

      return response.statusCode >= 200 && response.statusCode < 300;
    } catch (e) {
      print("DELETE Request Error: $e");
      return false;
    }
  }

  // ==================== COMPANY METHODS ====================

  /// Get all companies from backend
  static Future<List<Map<String, dynamic>>> getCompanies() async {
    try {
      final response = await _get('/companies/');
      if (response != null && response['companies'] != null) {
        return List<Map<String, dynamic>>.from(response['companies']);
      }
      return [];
    } catch (e) {
      print("Error getting companies: $e");
      return [];
    }
  }

  /// Get company by ID from backend (admin-inserted record)
  static Future<Map<String, dynamic>?> getCompany(String companyId) async {
    try {
      return await _get('/companies/$companyId');
    } catch (e) {
      print("Error getting company: $e");
      return null;
    }
  }

  /// Get scraped company data by ID
  static Future<Map<String, dynamic>?> getScrapedCompany(String companyId) async {
    try {
      return await _get('/companies/scraped/$companyId');
    } catch (e) {
      print("Error getting scraped company: $e");
      return null;
    }
  }

  /// Scrape a company by companyId (new workflow)
  static Future<Map<String, dynamic>?> scrapeCompanyById(String companyId) async {
    try {
      return await _post(
        '/companies/scrape-company',
        {'companyId': companyId},
        requiresAuth: true,
      );
    } catch (e) {
      print("Error scraping company: $e");
      rethrow;
    }
  }

  /// Scrape a company website (legacy - for manual URL input)
  static Future<Map<String, dynamic>?> scrapeCompany(String url) async {
    try {
      return await _post(
        '/companies/scrape',
        {'url': url},
        requiresAuth: true,
      );
    } catch (e) {
      print("Error scraping company: $e");
      rethrow;
    }
  }

  /// Create a company manually
  static Future<Map<String, dynamic>?> createCompany({
    required String name,
    String? location,
    String? description,
  }) async {
    try {
      return await _post(
        '/companies/',
        {
          'name': name,
          'location': location ?? '',
          'description': description ?? '',
        },
        requiresAuth: true,
      );
    } catch (e) {
      print("Error creating company: $e");
      rethrow;
    }
  }

  // ==================== CALENDAR/EVENTS METHODS ====================

  /// Get user's events from backend
  static Future<List<Map<String, dynamic>>> getEvents() async {
    try {
      final response = await _get('/calendar/events', requiresAuth: true);
      if (response != null && response['events'] != null) {
        return List<Map<String, dynamic>>.from(response['events']);
      }
      return [];
    } catch (e) {
      print("Error getting events: $e");
      return [];
    }
  }

  /// Get user's reminders from backend
  static Future<List<Map<String, dynamic>>> getReminders() async {
    try {
      final response = await _get('/calendar/reminders', requiresAuth: true);
      if (response != null && response['reminders'] != null) {
        return List<Map<String, dynamic>>.from(response['reminders']);
      }
      return [];
    } catch (e) {
      print("Error getting reminders: $e");
      return [];
    }
  }

  /// Create a new event
  static Future<Map<String, dynamic>?> createEvent({
    required String title,
    required String date,
    String? time,
    String? description,
    String? companyName,
  }) async {
    try {
      return await _post(
        '/calendar/events',
        {
          'title': title,
          'date': date,
          'time': time ?? '',
          'description': description ?? '',
          'company_name': companyName ?? '',
        },
        requiresAuth: true,
      );
    } catch (e) {
      print("Error creating event: $e");
      rethrow;
    }
  }

  /// Delete an event
  static Future<bool> deleteEvent(String eventId) async {
    try {
      return await _delete('/calendar/events/$eventId', requiresAuth: true);
    } catch (e) {
      print("Error deleting event: $e");
      return false;
    }
  }

  /// Create a reminder
  static Future<Map<String, dynamic>?> createReminder({
    required String title,
    required String reminderTime,
    String? description,
    bool isCompleted = false,
  }) async {
    try {
      return await _post(
        '/calendar/reminders',
        {
          'title': title,
          'reminderTime': reminderTime,
          'description': description ?? '',
          'isCompleted': isCompleted,
        },
        requiresAuth: true,
      );
    } catch (e) {
      print("Error creating reminder: $e");
      rethrow;
    }
  }

  /// Delete a reminder
  static Future<bool> deleteReminder(String reminderId) async {
    try {
      return await _delete('/calendar/reminders/$reminderId', requiresAuth: true);
    } catch (e) {
      print("Error deleting reminder: $e");
      return false;
    }
  }

  /// Update a reminder
  static Future<bool> updateReminder(String reminderId, Map<String, dynamic> data) async {
    try {
      final response = await _put(
        '/calendar/reminders/$reminderId',
        data,
        requiresAuth: true,
      );
      return response != null;
    } catch (e) {
      print("Error updating reminder: $e");
      return false;
    }
  }

  // ==================== CHAT METHODS ====================

  /// Get chat messages from backend
  static Future<List<Map<String, dynamic>>> getChatMessages() async {
    try {
      final response = await _get('/chat/messages', requiresAuth: true);
      if (response != null && response['messages'] != null) {
        return List<Map<String, dynamic>>.from(response['messages']);
      }
      return [];
    } catch (e) {
      print("Error getting chat messages: $e");
      return [];
    }
  }

  /// Send a chat message
  static Future<Map<String, dynamic>?> sendChatMessage(String message, {String? receiverId}) async {
    try {
      return await _post(
        '/chat/messages',
        {
          'message': message,
          'receiverId': receiverId,
        },
        requiresAuth: true,
      );
    } catch (e) {
      print("Error sending message: $e");
      rethrow;
    }
  }

  /// Mark message as read
  static Future<bool> markMessageRead(String messageId) async {
    try {
      final response = await _put(
        '/chat/messages/$messageId/read',
        {},
        requiresAuth: true,
      );
      return response != null;
    } catch (e) {
      print("Error marking message as read: $e");
      return false;
    }
  }

  // ==================== CHATBOT METHODS ====================

  /// Smart query - automatically scrapes ANY company name
  static Future<Map<String, dynamic>?> smartQuery(String userMessage, {String? userId}) async {
    try {
      final currentUserId = await _getCurrentUserId();
      if (currentUserId == null) {
        throw Exception('User not authenticated');
      }
      
      final response = await _post(
        '/chatbot/smart-query',
        {
          'userId': userId ?? currentUserId,
          'userMessage': userMessage,
        },
        requiresAuth: true,
      );
      
      // Check if response has error
      if (response != null && response.containsKey('error') && !response.containsKey('data')) {
        throw Exception(response['error'] ?? 'Unknown error from backend');
      }
      
      return response;
    } catch (e) {
      print("Error in smart query: $e");
      // Re-throw with more context
      if (e.toString().contains('Failed host lookup') || 
          e.toString().contains('Connection refused')) {
        throw Exception('Backend server is not running. Please start it with: cd lib/backend && python -m app.main');
      }
      rethrow;
    }
  }

  /// Send query to AI chatbot
  static Future<Map<String, dynamic>?> queryChatbot(String message, {String? userId}) async {
    try {
      final currentUserId = await _getCurrentUserId();
      if (currentUserId == null) {
        throw Exception('User not authenticated');
      }
      
      final response = await _post(
        '/chatbot/query',
        {
          'userId': userId ?? currentUserId,
          'message': message,
        },
        requiresAuth: true,
      );
      
      // Check if response has error
      if (response != null && response.containsKey('error')) {
        throw Exception(response['error'] ?? 'Unknown error from backend');
      }
      
      return response;
    } catch (e) {
      print("Error querying chatbot: $e");
      // Re-throw with more context
      if (e.toString().contains('Failed host lookup') || 
          e.toString().contains('Connection refused')) {
        throw Exception('Backend server is not running. Please start it with: cd lib/backend && python -m app.main');
      }
      rethrow;
    }
  }

  /// Get chat history
  static Future<List<Map<String, dynamic>>> getChatHistory({int limit = 50}) async {
    try {
      final response = await _get(
        '/chatbot/history?limit=$limit',
        requiresAuth: true,
      );
      if (response != null && response['history'] != null) {
        return List<Map<String, dynamic>>.from(response['history']);
      }
      return [];
    } catch (e) {
      print("Error getting chat history: $e");
      return [];
    }
  }

  /// Get knowledge base entry for a company
  static Future<Map<String, dynamic>?> getKnowledgeBase(String companyName) async {
    try {
      final encodedName = Uri.encodeComponent(companyName);
      return await _get(
        '/chatbot/knowledge-base/$encodedName',
        requiresAuth: true,
      );
    } catch (e) {
      print("Error getting knowledge base: $e");
      return null;
    }
  }

  static Future<String?> _getCurrentUserId() async {
    try {
      final user = FirebaseAuth.instance.currentUser;
      return user?.uid;
    } catch (e) {
      return null;
    }
  }

  static Future<String?> getIdToken() async {
    return await _getIdToken();
  }

  // ==================== PROFILE METHODS ====================

  /// Get user profile from backend
  static Future<Map<String, dynamic>?> getProfile() async {
    try {
      final response = await _get('/auth/profile', requiresAuth: true);
      if (response != null && response['user'] != null) {
        return response['user'] as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      print("Error getting profile: $e");
      return null;
    }
  }

  /// Update user profile
  static Future<bool> updateProfile(Map<String, dynamic> profileData) async {
    try {
      final response = await _post(
        '/profile/setup',
        profileData,
        requiresAuth: true,
      );
      return response != null;
    } catch (e) {
      print("Error updating profile: $e");
      return false;
    }
  }

  // ==================== AUTH METHODS ====================

  /// Login with email and password (via backend)
  /// Note: This sends email/password to backend, which then uses Firebase Auth REST API
  static Future<Map<String, dynamic>?> login(String email, String password) async {
    try {
      return await _post(
        '/auth/login',
        {
          'email': email,
          'password': password,
        },
        requiresAuth: false,
      );
    } catch (e) {
      print("Error logging in: $e");
      rethrow;
    }
  }

  /// Register new user (via backend)
  /// Note: Backend creates Firebase user and Firestore document
  static Future<Map<String, dynamic>?> register({
    required String email,
    required String password,
    String? name,
  }) async {
    try {
      return await _post(
        '/auth/register',
        {
          'email': email,
          'password': password,
          'name': name ?? '',
        },
        requiresAuth: false,
      );
    } catch (e) {
      print("Error registering: $e");
      rethrow;
    }
  }

  /// Verify backend connection
  static Future<bool> checkConnection() async {
    try {
      final response = await _get('/');
      return response != null;
    } catch (e) {
      return false;
    }
  }
}

