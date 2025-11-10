import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../services/api_client.dart';
import 'package:http/http.dart' as http;

class AuthProvider with ChangeNotifier {
  final ApiClient api;
  final FlutterSecureStorage secureStorage;
  Map<String, dynamic>? user;
  bool loading = false;

  AuthProvider({required this.api, required this.secureStorage});

  Future<bool> login(String email, String password) async {
    loading = true; notifyListeners();
    final response = await api.post('/auth/login', body: {'email': email, 'password': password});
    loading = false;

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      user = data['user'];
      if (data['id_token'] != null) {
        await secureStorage.write(key: 'id_token', value: data['id_token']);
      }
      if (data['refresh_token'] != null) {
        await secureStorage.write(key: 'refresh_token', value: data['refresh_token']);
      }
      notifyListeners();
      return true;
    } else {
      // optionally include error handling / parse error message
      return false;
    }
  }

  Future<void> logout() async {
    user = null;
    await secureStorage.delete(key: 'id_token');
    await secureStorage.delete(key: 'refresh_token');
    notifyListeners();
  }

  Future<bool> tryAutoLogin() async {
    final token = await secureStorage.read(key: 'id_token');
    if (token == null) return false;
    // Optionally verify token server-side; we'll assume token works and fetch user
    final resp = await api.get('/users/me', auth: true); // implement this endpoint server-side if you want
    if (resp.statusCode == 200) {
      final data = jsonDecode(resp.body);
      user = data['user'];
      notifyListeners();
      return true;
    }
    return false;
  }

  // Optional: function to refresh token by calling backend refresh endpoint
  Future<bool> refreshToken() async {
    final refresh = await secureStorage.read(key: 'refresh_token');
    if (refresh == null) return false;
    final resp = await api.post('/auth/refresh', body: {'refresh_token': refresh});
    if (resp.statusCode == 200) {
      final data = jsonDecode(resp.body);
      if (data['id_token'] != null) {
        await secureStorage.write(key: 'id_token', value: data['id_token']);
        return true;
      }
    }
    return false;
  }
}
