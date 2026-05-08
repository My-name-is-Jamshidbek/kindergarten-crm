import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api_client.dart';

class AppSession extends ChangeNotifier {
  AppSession(this.api);

  static const _tokenKey = 'auth_token';

  final ApiClient api;
  bool isLoading = true;
  Map<String, dynamic>? user;

  bool get isAuthenticated => api.token != null && user != null;
  String get role => user?['role']?.toString() ?? '';
  String get username => user?['username']?.toString() ?? '';

  bool _isEducator(Map<String, dynamic>? userData) {
    return userData?['role']?.toString() == 'educator';
  }

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    api.token = prefs.getString(_tokenKey);
    if (api.token != null) {
      try {
        final data = await api.me();
        user = data['user'] as Map<String, dynamic>?;
        if (!_isEducator(user)) {
          await prefs.remove(_tokenKey);
          api.token = null;
          user = null;
        }
      } on ApiException {
        await prefs.remove(_tokenKey);
        api.token = null;
        user = null;
      }
    }
    isLoading = false;
    notifyListeners();
  }

  Future<void> login(String username, String password) async {
    final data = await api.login(username, password);
    final prefs = await SharedPreferences.getInstance();
    api.token = data['token'] as String;
    user = data['user'] as Map<String, dynamic>?;
    if (!_isEducator(user)) {
      api.token = null;
      user = null;
      throw const ApiException('Mobil ilova faqat tarbiyachi roli uchun.');
    }
    await prefs.setString(_tokenKey, api.token!);
    notifyListeners();
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    api.token = null;
    user = null;
    notifyListeners();
  }
}
