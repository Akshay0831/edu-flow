"""
Frontend-Backend Integration Script

This script helps establish connection between Flutter frontend and FastAPI backend.
It validates API connectivity, CORS configuration, and data format compatibility.

Usage:
    python frontend_backend_integration.py --test-endpoints
    python frontend_backend_integration.py --validate-cors
    python frontend_backend_integration.py --check-formats
"""

import requests
import json
import argparse
import sys
from typing import Dict, Any, List
import time

class FrontendBackendIntegration:
    """Frontend-Backend Integration Validator"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.api_base = f"{backend_url}/api/v1"
        self.session = requests.Session()
        
    def test_backend_connectivity(self) -> Dict[str, Any]:
        """Test basic backend connectivity"""
        print("🔍 Testing backend connectivity...")
        
        results = {}
        
        # Test root endpoint
        try:
            response = self.session.get(f"{self.backend_url}/")
            results['root_endpoint'] = {
                'status': response.status_code,
                'success': response.status_code == 200,
                'response_time': response.elapsed.total_seconds()
            }
            print(f"  Root endpoint: {response.status_code}")
        except Exception as e:
            results['root_endpoint'] = {'error': str(e)}
            print(f"  Root endpoint error: {e}")
        
        # Test health check
        try:
            response = self.session.get(f"{self.backend_url}/health")
            results['health_check'] = {
                'status': response.status_code,
                'success': response.status_code == 200,
                'response_time': response.elapsed.total_seconds()
            }
            print(f"  Health check: {response.status_code}")
        except Exception as e:
            results['health_check'] = {'error': str(e)}
            print(f"  Health check error: {e}")
        
        return results
    
    def test_api_endpoints(self) -> Dict[str, Any]:
        """Test API endpoints availability"""
        print("🌐 Testing API endpoints...")
        
        results = {}
        
        # Test authentication endpoints
        endpoints = [
            ('auth_register', 'POST', '/auth/register', {
                'email': 'test@example.com',
                'password': 'testpass123',
                'name': 'Test User',
                'role': 'student'
            }),
            ('auth_login', 'POST', '/auth/login', {
                'email': 'test@example.com',
                'password': 'testpass123'
            }),
            ('users_list', 'GET', '/users', {}),
        ]
        
        for name, method, path, data in endpoints:
            try:
                url = f"{self.api_base}{path}"
                if method == 'POST':
                    response = self.session.post(url, json=data)
                else:
                    response = self.session.get(url)
                
                results[name] = {
                    'status': response.status_code,
                    'success': response.status_code in [200, 201, 400, 401, 409, 422],
                    'response_time': response.elapsed.total_seconds(),
                    'content_type': response.headers.get('content-type', '')
                }
                print(f"  {name}: {response.status_code}")
                
            except Exception as e:
                results[name] = {'error': str(e)}
                print(f"  {name} error: {e}")
        
        return results
    
    def test_cors_configuration(self) -> Dict[str, Any]:
        """Test CORS configuration"""
        print("🔒 Testing CORS configuration...")
        
        results = {}
        
        # Test with different origins
        origins = [
            'http://localhost:3000',
            'http://localhost:8080',
            'http://localhost:5173',  # Vite dev server
            'http://localhost:5000',  # Custom frontend
        ]
        
        for origin in origins:
            try:
                headers = {'Origin': origin}
                response = self.session.get(f"{self.backend_url}/", headers=headers)
                
                cors_headers = {
                    'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
                    'access-control-allow-headers': response.headers.get('access-control-allow-headers'),
                }
                
                results[origin] = {
                    'status': response.status_code,
                    'cors_headers': cors_headers,
                    'cors_enabled': any(cors_headers.values())
                }
                print(f"  {origin}: CORS {'enabled' if any(cors_headers.values()) else 'disabled'}")
                
            except Exception as e:
                results[origin] = {'error': str(e)}
                print(f"  {origin} error: {e}")
        
        return results
    
    def test_data_formats(self) -> Dict[str, Any]:
        """Test data format compatibility"""
        print("📋 Testing data format compatibility...")
        
        results = {}
        
        # Test user registration data format
        user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test User',
            'role': 'student'
        }
        
        try:
            response = self.session.post(f"{self.api_base}/auth/register", json=user_data)
            
            results['user_registration'] = {
                'status': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'response_size': len(response.content),
                'is_json': 'application/json' in response.headers.get('content-type', '')
            }
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    results['user_registration']['response_data'] = response_data
                    results['user_registration']['has_token'] = 'access_token' in response_data
                except json.JSONDecodeError:
                    results['user_registration']['json_error'] = 'Invalid JSON response'
            
            print(f"  User registration: {response.status_code}")
            
        except Exception as e:
            results['user_registration'] = {'error': str(e)}
            print(f"  User registration error: {e}")
        
        return results
    
    def test_performance(self) -> Dict[str, Any]:
        """Test performance metrics"""
        print("⚡ Testing performance...")
        
        results = {}
        
        # Test multiple requests
        test_count = 10
        endpoints = [
            ('root', 'GET', ''),
            ('health', 'GET', '/health'),
            ('docs', 'GET', '/docs'),
        ]
        
        for name, method, path in endpoints:
            response_times = []
            
            for i in range(test_count):
                try:
                    url = f"{self.backend_url}{path}"
                    if method == 'GET':
                        response = self.session.get(url)
                    else:
                        response = self.session.post(url)
                    
                    response_times.append(response.elapsed.total_seconds())
                    
                except Exception as e:
                    print(f"  {name} request {i+1} failed: {e}")
                    break
            
            if response_times:
                results[name] = {
                    'avg_response_time': sum(response_times) / len(response_times),
                    'min_response_time': min(response_times),
                    'max_response_time': max(response_times),
                    'success_rate': len(response_times) / test_count
                }
                print(f"  {name}: {results[name]['avg_response_time']:.3f}s avg")
        
        return results
    
    def generate_flutter_config(self) -> str:
        """Generate Flutter backend configuration"""
        config_template = '''
// Backend API Configuration
const String BACKEND_URL = 'http://localhost:8000';
const String API_BASE = '$BACKEND_URL/api/v1';

// API Endpoints
const Map<String, String> ENDPOINTS = {
  'auth': {
    'register': '$API_BASE/auth/register',
    'login': '$API_BASE/auth/login',
    'logout': '$API_BASE/auth/logout',
    'refresh': '$API_BASE/auth/refresh',
  },
  'users': '$API_BASE/users',
  'students': '$API_BASE/students',
  'teachers': '$API_BASE/teachers',
  'courses': '$API_BASE/courses',
  'classes': '$API_BASE/classes',
};

// HTTP Client Configuration
class ApiClient {
  static const Duration CONNECT_TIMEOUT = Duration(seconds: 30);
  static const Duration RECEIVE_TIMEOUT = Duration(seconds: 30);
  
  static Map<String, String> getHeaders({String? token}) {
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }
}

// CORS Configuration
class CorsConfig {
  static const List<String> ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:8080',
    'http://localhost:5173',
    'http://localhost:5000',
  ];
}
'''
        return config_template
    
    def run_full_test_suite(self) -> Dict[str, Any]:
        """Run complete integration test suite"""
        print("🚀 Starting Frontend-Backend Integration Test Suite...")
        print("=" * 60)
        
        results = {
            'timestamp': time.time(),
            'backend_url': self.backend_url,
            'connectivity': self.test_backend_connectivity(),
            'api_endpoints': self.test_api_endpoints(),
            'cors_configuration': self.test_cors_configuration(),
            'data_formats': self.test_data_formats(),
            'performance': self.test_performance(),
        }
        
        # Calculate overall success rate
        total_tests = 0
        successful_tests = 0
        
        for category in results.values():
            if isinstance(category, dict):
                for test_name, test_result in category.items():
                    if isinstance(test_result, dict) and 'success' in test_result:
                        total_tests += 1
                        if test_result['success']:
                            successful_tests += 1
        
        results['summary'] = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        print("=" * 60)
        print(f"📊 Integration Test Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Successful: {successful_tests}")
        print(f"  Success Rate: {results['summary']['success_rate']:.1f}%")
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Frontend-Backend Integration Validator')
    parser.add_argument('--backend-url', default='http://localhost:8000', help='Backend URL')
    parser.add_argument('--test-endpoints', action='store_true', help='Test API endpoints')
    parser.add_argument('--validate-cors', action='store_true', help='Validate CORS')
    parser.add_argument('--check-formats', action='store_true', help='Check data formats')
    parser.add_argument('--performance', action='store_true', help='Test performance')
    parser.add_argument('--full-test', action='store_true', help='Run full test suite')
    parser.add_argument('--generate-config', action='store_true', help='Generate Flutter config')
    
    args = parser.parse_args()
    
    integrator = FrontendBackendIntegration(args.backend_url)
    
    if args.generate_config:
        print("📱 Generating Flutter backend configuration...")
        print(integrator.generate_flutter_config())
        return
    
    if args.full_test or not any([args.test_endpoints, args.validate_cors, args.check_formats, args.performance]):
        results = integrator.run_full_test_suite()
        return
    
    if args.test_endpoints:
        integrator.test_api_endpoints()
    
    if args.validate_cors:
        integrator.test_cors_configuration()
    
    if args.check_formats:
        integrator.test_data_formats()
    
    if args.performance:
        integrator.test_performance()

if __name__ == "__main__":
    main()