import 'package:flutter/material.dart';
import 'package:edu_flow/core/theme/app_theme.dart';

class TeacherDetailsScreen extends StatefulWidget {
  final String teacherId;
  
  const TeacherDetailsScreen({super.key, required this.teacherId});

  @override
  State<TeacherDetailsScreen> createState() => _TeacherDetailsScreenState();
}

class _TeacherDetailsScreenState extends State<TeacherDetailsScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Teacher Details'),
        backgroundColor: AppTheme.primaryColor,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.person, size: 64, color: AppTheme.primaryColor),
            SizedBox(height: 16),
            Text(
              'Teacher ID: ${widget.teacherId}',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 8),
            Text(
              'Teacher Details Screen',
              style: TextStyle(fontSize: 14, color: AppTheme.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}