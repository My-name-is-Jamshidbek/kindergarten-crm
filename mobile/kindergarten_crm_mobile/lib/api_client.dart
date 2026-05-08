import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiException implements Exception {
  const ApiException(this.message, [this.statusCode]);

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({
    String baseUrl = const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://127.0.0.1:8000/api',
    ),
    http.Client? httpClient,
  }) : baseUrl = baseUrl.replaceFirst(RegExp(r'/$'), ''),
       _httpClient = httpClient ?? http.Client();

  final String baseUrl;
  final http.Client _httpClient;
  String? token;

  Future<Map<String, dynamic>> login(String username, String password) {
    return post('/auth/login/', {
      'username': username,
      'password': password,
    }, authenticated: false);
  }

  Future<Map<String, dynamic>> me() => get('/auth/me/');

  Future<Map<String, dynamic>> dashboard() => get('/dashboard/');

  Future<Map<String, dynamic>> classrooms() => get('/classrooms/');

  Future<Map<String, dynamic>> guardians({String? query}) {
    return get(
      '/guardians/',
      query: {if (query != null && query.trim().isNotEmpty) 'q': query.trim()},
    );
  }

  Future<Map<String, dynamic>> attendance({
    DateTime? date,
    String? classroom,
    String? status,
    String? query,
  }) {
    return get(
      '/attendance/',
      query: {
        if (date != null) 'date': _date(date),
        if (classroom != null && classroom.isNotEmpty) 'classroom': classroom,
        if (status != null && status.isNotEmpty) 'status': status,
        if (query != null && query.trim().isNotEmpty) 'q': query.trim(),
      },
    );
  }

  Future<Map<String, dynamic>> markAttendance(int id, String status) {
    return post('/attendance/$id/mark/', {'status': status});
  }

  Future<Map<String, dynamic>> updateAttendance(
    int id,
    Map<String, dynamic> body,
  ) {
    return patch('/attendance/$id/', body);
  }

  Future<Map<String, dynamic>> bulkMarkPresent({
    required DateTime date,
    required String classroom,
  }) {
    return post('/attendance/bulk/mark-present/', {
      'date': _date(date),
      'classroom': classroom,
    });
  }

  Future<Map<String, dynamic>> get(
    String path, {
    Map<String, String>? query,
    bool authenticated = true,
  }) async {
    final response = await _httpClient.get(
      _uri(path, query),
      headers: _headers(authenticated),
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> post(
    String path,
    Map<String, dynamic> body, {
    bool authenticated = true,
  }) async {
    final response = await _httpClient.post(
      _uri(path),
      headers: _headers(authenticated),
      body: jsonEncode(body),
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> patch(
    String path,
    Map<String, dynamic> body, {
    bool authenticated = true,
  }) async {
    final response = await _httpClient.patch(
      _uri(path),
      headers: _headers(authenticated),
      body: jsonEncode(body),
    );
    return _decode(response);
  }

  Uri _uri(String path, [Map<String, String>? query]) {
    return Uri.parse('$baseUrl$path').replace(queryParameters: query);
  }

  Map<String, String> _headers(bool authenticated) {
    return {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      if (authenticated && token != null) 'Authorization': 'Token $token',
    };
  }

  Map<String, dynamic> _decode(http.Response response) {
    final decoded = response.body.isEmpty
        ? <String, dynamic>{}
        : jsonDecode(response.body);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return decoded as Map<String, dynamic>;
    }
    final detail = decoded is Map<String, dynamic> ? decoded['detail'] : null;
    throw ApiException(
      detail?.toString() ?? 'Server error ${response.statusCode}',
      response.statusCode,
    );
  }

  String _date(DateTime date) {
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '${date.year}-$month-$day';
  }
}
