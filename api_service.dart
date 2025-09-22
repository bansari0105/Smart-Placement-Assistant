import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = "http://10.0.2.2:5000";

  // ✅ Example GET request
  static Future<Map<String, dynamic>?> getHomeMessage() async {
    try {
      final response = await http.get(Uri.parse("$baseUrl/"));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print("Error calling backend: $e");
    }
    return null;
  }

  // ✅ Example POST request with body
  static Future<Map<String, dynamic>?> postRequest(
      String endpoint, Map<String, dynamic> body) async {
    try {
      final response = await http.post(
        Uri.parse("$baseUrl/$endpoint"),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(body),
      );
      return jsonDecode(response.body);
    } catch (e) {
      print("POST error: $e");
      return null;
    }
  }
}
