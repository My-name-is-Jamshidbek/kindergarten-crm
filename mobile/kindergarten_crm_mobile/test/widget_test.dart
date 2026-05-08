import 'package:flutter_test/flutter_test.dart';
import 'package:kindergarten_crm_mobile/api_client.dart';
import 'package:kindergarten_crm_mobile/main.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  testWidgets('shows login screen when no token is saved', (tester) async {
    SharedPreferences.setMockInitialValues({});

    await tester.pumpWidget(KindergartenCrmApp(apiClient: ApiClient()));
    await tester.pumpAndSettle();

    expect(find.text('Kirish'), findsWidgets);
    expect(find.text("Anvar Bog'cha"), findsOneWidget);
  });
}
