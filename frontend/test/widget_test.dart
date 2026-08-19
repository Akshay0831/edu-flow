import 'package:flutter_test/flutter_test.dart';
import 'package:edu_flow/main.dart';

void main() {
  testWidgets('EduFlowApp smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const EduFlowApp());
    await tester.pump(const Duration(seconds: 1));
    expect(find.byType(EduFlowApp), findsOneWidget);
  });
}
