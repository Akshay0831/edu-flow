import 'package:flutter/foundation.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:edu_flow/data/services/auth_service.dart';

@GenerateNiceMocks([MockSpec<AuthService>()])
class MockAuthService extends Mock with ChangeNotifier implements AuthService {}