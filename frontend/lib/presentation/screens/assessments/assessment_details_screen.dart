import 'package:flutter/material.dart';
import 'package:edu_flow/core/theme/app_theme.dart';

class AssessmentDetailsScreen extends StatefulWidget {
  final String assessmentId;
  
  const AssessmentDetailsScreen({super.key, required this.assessmentId});

  @override
  State<AssessmentDetailsScreen> createState() => _AssessmentDetailsScreenState();
}

class _AssessmentDetailsScreenState extends State<AssessmentDetailsScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Assessment Details'),
        backgroundColor: AppTheme.primaryColor,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.assignment, size: 64, color: AppTheme.primaryColor),
            const SizedBox(height: 16),
            Text(
              'Assessment ID: ${widget.assessmentId}',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Assessment Details Screen',
              style: TextStyle(fontSize: 14, color: AppTheme.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}