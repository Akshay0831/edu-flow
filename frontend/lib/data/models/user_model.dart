import 'dart:convert';

class UserModel {
  final String id;
  final String email;
  final String name;
  final String role;
  final String? phone;
  final String? avatar;
  final DateTime? createdAt;
  final DateTime? updatedAt;
  final Map<String, dynamic>? additionalData;
  
  UserModel({
    required this.id,
    required this.email,
    required this.name,
    required this.role,
    this.phone,
    this.avatar,
    this.createdAt,
    this.updatedAt,
    this.additionalData,
  });
  
  // Factory constructor to create from JSON
  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] ?? json['user_id'] ?? '',
      email: json['email'] ?? '',
      name: json['name'] ?? '',
      role: json['role'] ?? 'student',
      phone: json['phone'],
      avatar: json['avatar'],
      createdAt: json['created_at'] != null 
          ? DateTime.parse(json['created_at']) 
          : null,
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at']) 
          : null,
      additionalData: json,
    );
  }
  
  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'name': name,
      'role': role,
      'phone': phone,
      'avatar': avatar,
      'created_at': createdAt?.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
      if (additionalData != null) ...additionalData!,
    };
  }
  
  // Create copy with updated fields
  UserModel copyWith({
    String? id,
    String? email,
    String? name,
    String? role,
    String? phone,
    String? avatar,
    DateTime? createdAt,
    DateTime? updatedAt,
    Map<String, dynamic>? additionalData,
  }) {
    return UserModel(
      id: id ?? this.id,
      email: email ?? this.email,
      name: name ?? this.name,
      role: role ?? this.role,
      phone: phone ?? this.phone,
      avatar: avatar ?? this.avatar,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      additionalData: additionalData ?? this.additionalData,
    );
  }
  
  // Check if user is admin
  bool get isAdmin => role.toLowerCase() == 'admin';
  
  // Check if user is teacher
  bool get isTeacher => role.toLowerCase() == 'teacher';
  
  // Check if user is student
  bool get isStudent => role.toLowerCase() == 'student';
  
  // Get user initials
  String get initials {
    if (name.isEmpty) return '';
    final parts = name.split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    } else if (parts.length == 1) {
      return parts[0][0].toUpperCase();
    }
    return '';
  }
  
  // Get display name
  String get displayName => name.isNotEmpty ? name : email;
  
  // Get email domain
  String get emailDomain {
    final parts = email.split('@');
    return parts.length > 1 ? parts[1] : '';
  }
  
  // Get avatar URL
  String get avatarUrl {
    if (avatar != null && avatar!.isNotEmpty) {
      return avatar!;
    }
    // Generate a placeholder URL with user initials
    return 'https://ui-avatars.com/api/?name=${Uri.encodeComponent(name)}&background=random&color=fff&size=200';
  }
  
  // Validate user model
  bool isValid() {
    return id.isNotEmpty && email.isNotEmpty && name.isNotEmpty;
  }
  
  // Get validation errors
  List<String> get validationErrors {
    final errors = <String>[];
    
    if (id.isEmpty) errors.add('User ID is required');
    if (email.isEmpty) errors.add('Email is required');
    if (!email.contains('@')) errors.add('Email is invalid');
    if (name.isEmpty) errors.add('Name is required');
    if (!['admin', 'teacher', 'student'].contains(role.toLowerCase())) {
      errors.add('Role must be admin, teacher, or student');
    }
    
    return errors;
  }
  
  // Equality operator
  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    
    return other is UserModel &&
      other.id == id &&
      other.email == email &&
      other.name == name &&
      other.role == role &&
      other.phone == phone &&
      other.avatar == avatar;
  }
  
  // Hash code
  @override
  int get hashCode {
    return id.hashCode ^
      email.hashCode ^
      name.hashCode ^
      role.hashCode ^
      phone.hashCode ^
      avatar.hashCode;
  }
  
  // toString method
  @override
  String toString() {
    return 'UserModel(id: $id, email: $email, name: $name, role: $role)';
  }
  
  // Create mock user for testing
  static UserModel mockUser({
    String id = 'mock-user-id',
    String email = 'test@example.com',
    String name = 'Test User',
    String role = 'student',
  }) {
    return UserModel(
      id: id,
      email: email,
      name: name,
      role: role,
      createdAt: DateTime.now(),
      updatedAt: DateTime.now(),
    );
  }
}