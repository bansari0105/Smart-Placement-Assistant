import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  final String baseUrl;
  final FlutterSecureStorage storage;

  ApiClient({required this.baseUrl, required this.storage});

  Future<http.Response> post(String path, {Map<String, dynamic>? body, bool auth = false}) async {
    final uri = Uri.parse('$baseUrl$path');
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (auth) {
      final token = await storage.read(key: 'id_token');
      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    return http.post(uri, headers: headers, body: jsonEncode(body ?? {}));
  }

  Future<http.Response> get(String path, {bool auth = false}) async {
    final uri = Uri.parse('$baseUrl$path');
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (auth) {
      final token = await storage.read(key: 'id_token');
      if (token != null) headers['Authorization'] = 'Bearer $token';
    }
    return http.get(uri, headers: headers);
  }
}
