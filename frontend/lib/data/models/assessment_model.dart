import 'dart:convert';

class AssessmentModel {
  final String id;
  final String title;
  final String description;
  final double maxMarks;
  final String courseId;
  final String teacherId;
  final DateTime dueDate;
  final DateTime createdAt;
  final DateTime updatedAt;
  final List<AssessmentSubmission> submissions;
  final Map<String, dynamic>? additionalData;

  AssessmentModel({
    required this.id,
    required this.title,
    required this.description,
    required this.maxMarks,
    required this.courseId,
    required this.teacherId,
    required this.dueDate,
    required this.createdAt,
    required this.updatedAt,
    this.submissions = const [],
    this.additionalData,
  });

  // Factory constructor to create from JSON
  factory AssessmentModel.fromJson(Map<String, dynamic> json) {
    return AssessmentModel(
      id: json['id'] ?? json['assessment_id'] ?? '',
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      maxMarks: (json['max_marks'] ?? json['maxMarks'] ?? 100).toDouble(),
      courseId: json['course_id'] ?? json['courseId'] ?? '',
      teacherId: json['teacher_id'] ?? json['teacherId'] ?? '',
      dueDate: json['due_date'] != null 
          ? DateTime.parse(json['due_date']) 
          : DateTime.now(),
      createdAt: json['created_at'] != null 
          ? DateTime.parse(json['created_at']) 
          : DateTime.now(),
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at']) 
          : DateTime.now(),
      submissions: json['submissions'] != null 
          ? (json['submissions'] as List)
              .map((submissionJson) => AssessmentSubmission.fromJson(submissionJson))
              .toList()
          : [],
      additionalData: json,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'max_marks': maxMarks,
      'course_id': courseId,
      'teacher_id': teacherId,
      'due_date': dueDate.toIso8601String(),
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'submissions': submissions.map((s) => s.toJson()).toList(),
    };
  }
}

class AssessmentSubmission {
  final String id;
  final String assessmentId;
  final String studentId;
  final double? marks;
  final String? grade;
  final String? feedback;
  final String? status; // 'submitted', 'graded', 'reviewed'
  final DateTime submittedAt;
  final DateTime gradedAt;
  final Map<String, dynamic>? additionalData;

  AssessmentSubmission({
    required this.id,
    required this.assessmentId,
    required this.studentId,
    this.marks,
    this.grade,
    this.feedback,
    this.status = 'submitted',
    required this.submittedAt,
    required this.gradedAt,
    this.additionalData,
  });

  // Factory constructor to create from JSON
  factory AssessmentSubmission.fromJson(Map<String, dynamic> json) {
    return AssessmentSubmission(
      id: json['id'] ?? json['submission_id'] ?? '',
      assessmentId: json['assessment_id'] ?? json['assessmentId'] ?? '',
      studentId: json['student_id'] ?? json['studentId'] ?? '',
      marks: json['marks']?.toDouble(),
      grade: json['grade'],
      feedback: json['feedback'],
      status: json['status'] ?? 'submitted',
      submittedAt: json['submitted_at'] != null 
          ? DateTime.parse(json['submitted_at']) 
          : DateTime.now(),
      gradedAt: json['graded_at'] != null 
          ? DateTime.parse(json['graded_at']) 
          : DateTime.now(),
      additionalData: json,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'assessment_id': assessmentId,
      'student_id': studentId,
      'marks': marks,
      'grade': grade,
      'feedback': feedback,
      'status': status,
      'submitted_at': submittedAt.toIso8601String(),
      'graded_at': gradedAt.toIso8601String(),
    };
  }
}

class GradeCalculation {
  final String studentId;
  final String courseId;
  final List<AssessmentGrade> assessmentGrades;
  final double totalScore;
  final String finalGrade;
  final double percentage;
  final String letterGrade;

  GradeCalculation({
    required this.studentId,
    required this.courseId,
    required this.assessmentGrades,
    required this.totalScore,
    required this.finalGrade,
    required this.percentage,
    required this.letterGrade,
  });

  // Factory constructor to create from JSON
  factory GradeCalculation.fromJson(Map<String, dynamic> json) {
    return GradeCalculation(
      studentId: json['student_id'] ?? json['studentId'] ?? '',
      courseId: json['course_id'] ?? json['courseId'] ?? '',
      assessmentGrades: json['assessment_grades'] != null
          ? (json['assessment_grades'] as List)
              .map((gradeJson) => AssessmentGrade.fromJson(gradeJson))
              .toList()
          : [],
      totalScore: (json['total_score'] ?? 0).toDouble(),
      finalGrade: json['final_grade'] ?? '',
      percentage: (json['percentage'] ?? 0).toDouble(),
      letterGrade: json['letter_grade'] ?? '',
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'student_id': studentId,
      'course_id': courseId,
      'assessment_grades': assessmentGrades.map((g) => g.toJson()).toList(),
      'total_score': totalScore,
      'final_grade': finalGrade,
      'percentage': percentage,
      'letter_grade': letterGrade,
    };
  }
}

class AssessmentGrade {
  final String assessmentId;
  final String title;
  final double marks;
  final double maxMarks;
  final double percentage;
  final String grade;
  final DateTime gradedAt;

  AssessmentGrade({
    required this.assessmentId,
    required this.title,
    required this.marks,
    required this.maxMarks,
    required this.percentage,
    required this.grade,
    required this.gradedAt,
  });

  // Factory constructor to create from JSON
  factory AssessmentGrade.fromJson(Map<String, dynamic> json) {
    return AssessmentGrade(
      assessmentId: json['assessment_id'] ?? json['assessmentId'] ?? '',
      title: json['title'] ?? '',
      marks: (json['marks'] ?? 0).toDouble(),
      maxMarks: (json['max_marks'] ?? 100).toDouble(),
      percentage: (json['percentage'] ?? 0).toDouble(),
      grade: json['grade'] ?? '',
      gradedAt: json['graded_at'] != null 
          ? DateTime.parse(json['graded_at']) 
          : DateTime.now(),
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'assessment_id': assessmentId,
      'title': title,
      'marks': marks,
      'max_marks': maxMarks,
      'percentage': percentage,
      'grade': grade,
      'graded_at': gradedAt.toIso8601String(),
    };
  }
}