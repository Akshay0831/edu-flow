import 'dart:convert';

class StudentPerformance {
  final String studentId;
  final String name;
  final double overallScore;
  final double attendanceRate;
  final int totalAssessments;
  final int completedAssessments;
  final double averageGrade;
  final List<CourseProgress> courseProgress;
  final Map<String, dynamic>? additionalData;

  StudentPerformance({
    required this.studentId,
    required this.name,
    required this.overallScore,
    required this.attendanceRate,
    required this.totalAssessments,
    required this.completedAssessments,
    required this.averageGrade,
    required this.courseProgress,
    this.additionalData,
  });

  // Factory constructor to create from JSON
  factory StudentPerformance.fromJson(Map<String, dynamic> json) {
    return StudentPerformance(
      studentId: json['student_id'] ?? json['studentId'] ?? '',
      name: json['name'] ?? '',
      overallScore: (json['overall_score'] ?? 0).toDouble(),
      attendanceRate: (json['attendance_rate'] ?? 0).toDouble(),
      totalAssessments: json['total_assessments'] ?? 0,
      completedAssessments: json['completed_assessments'] ?? 0,
      averageGrade: (json['average_grade'] ?? 0).toDouble(),
      courseProgress: json['course_progress'] != null
          ? (json['course_progress'] as List)
              .map((progressJson) => CourseProgress.fromJson(progressJson))
              .toList()
          : [],
      additionalData: json,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'student_id': studentId,
      'name': name,
      'overall_score': overallScore,
      'attendance_rate': attendanceRate,
      'total_assessments': totalAssessments,
      'completed_assessments': completedAssessments,
      'average_grade': averageGrade,
      'course_progress': courseProgress.map((p) => p.toJson()).toList(),
    };
  }
}

class CourseProgress {
  final String courseId;
  final String title;
  final double completionPercentage;
  final double averageGrade;
  final int enrolledStudents;
  final int completedStudents;
  final DateTime startDate;
  final DateTime endDate;
  final List<StudentPerformance> topPerformers;
  final Map<String, dynamic>? additionalData;

  CourseProgress({
    required this.courseId,
    required this.title,
    required this.completionPercentage,
    required this.averageGrade,
    required this.enrolledStudents,
    required this.completedStudents,
    required this.startDate,
    required this.endDate,
    required this.topPerformers,
    this.additionalData,
  });

  // Factory constructor to create from JSON
  factory CourseProgress.fromJson(Map<String, dynamic> json) {
    return CourseProgress(
      courseId: json['course_id'] ?? json['courseId'] ?? '',
      title: json['title'] ?? '',
      completionPercentage: (json['completion_percentage'] ?? 0).toDouble(),
      averageGrade: (json['average_grade'] ?? 0).toDouble(),
      enrolledStudents: json['enrolled_students'] ?? 0,
      completedStudents: json['completed_students'] ?? 0,
      startDate: json['start_date'] != null 
          ? DateTime.parse(json['start_date']) 
          : DateTime.now(),
      endDate: json['end_date'] != null 
          ? DateTime.parse(json['end_date']) 
          : DateTime.now(),
      topPerformers: json['top_performers'] != null
          ? (json['top_performers'] as List)
              .map((performerJson) => StudentPerformance.fromJson(performerJson))
              .toList()
          : [],
      additionalData: json,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'course_id': courseId,
      'title': title,
      'completion_percentage': completionPercentage,
      'average_grade': averageGrade,
      'enrolled_students': enrolledStudents,
      'completed_students': completedStudents,
      'start_date': startDate.toIso8601String(),
      'end_date': endDate.toIso8601String(),
      'top_performers': topPerformers.map((p) => p.toJson()).toList(),
    };
  }
}

class ClassPerformance {
  final String classId;
  final String className;
  final int totalStudents;
  final double averageScore;
  final double attendanceRate;
  final List<StudentPerformance> students;
  final Map<String, dynamic>? additionalData;

  ClassPerformance({
    required this.classId,
    required this.className,
    required this.totalStudents,
    required this.averageScore,
    required this.attendanceRate,
    required this.students,
    this.additionalData,
  });

  // Factory constructor to create from JSON
  factory ClassPerformance.fromJson(Map<String, dynamic> json) {
    return ClassPerformance(
      classId: json['class_id'] ?? json['classId'] ?? '',
      className: json['class_name'] ?? '',
      totalStudents: json['total_students'] ?? 0,
      averageScore: (json['average_score'] ?? 0).toDouble(),
      attendanceRate: (json['attendance_rate'] ?? 0).toDouble(),
      students: json['students'] != null
          ? (json['students'] as List)
              .map((studentJson) => StudentPerformance.fromJson(studentJson))
              .toList()
          : [],
      additionalData: json,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'class_id': classId,
      'class_name': className,
      'total_students': totalStudents,
      'average_score': averageScore,
      'attendance_rate': attendanceRate,
      'students': students.map((s) => s.toJson()).toList(),
    };
  }
}

class TeacherPerformance {
  final String teacherId;
  final String name;
  final double averageStudentScore;
  final double courseCompletionRate;
  final int totalCourses;
  final int totalStudents;
  final List<CourseAnalytics> courseAnalytics;
  final Map<String, dynamic>? additionalData;

  TeacherPerformance({
    required this.teacherId,
    required this.name,
    required this.averageStudentScore,
    required this.courseCompletionRate,
    required this.totalCourses,
    required this.totalStudents,
    required this.courseAnalytics,
    this.additionalData,
  });

  // Factory constructor to create from JSON
  factory TeacherPerformance.fromJson(Map<String, dynamic> json) {
    return TeacherPerformance(
      teacherId: json['teacher_id'] ?? json['teacherId'] ?? '',
      name: json['name'] ?? '',
      averageStudentScore: (json['average_student_score'] ?? 0).toDouble(),
      courseCompletionRate: (json['course_completion_rate'] ?? 0).toDouble(),
      totalCourses: json['total_courses'] ?? 0,
      totalStudents: json['total_students'] ?? 0,
      courseAnalytics: json['course_analytics'] != null
          ? (json['course_analytics'] as List)
              .map((courseJson) => CourseAnalytics.fromJson(courseJson))
              .toList()
          : [],
      additionalData: json,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'teacher_id': teacherId,
      'name': name,
      'average_student_score': averageStudentScore,
      'course_completion_rate': courseCompletionRate,
      'total_courses': totalCourses,
      'total_students': totalStudents,
      'course_analytics': courseAnalytics.map((c) => c.toJson()).toList(),
    };
  }
}

class CourseAnalytics {
  final String courseId;
  final String title;
  final double averageGrade;
  final double completionRate;
  final int enrolledStudents;
  final int completedStudents;
  final List<EnrollmentTrend> enrollmentTrends;
  final Map<String, dynamic>? additionalData;

  CourseAnalytics({
    required this.courseId,
    required this.title,
    required this.averageGrade,
    required this.completionRate,
    required this.enrolledStudents,
    required this.completedStudents,
    required this.enrollmentTrends,
    this.additionalData,
  });

  // Factory constructor to create from JSON
  factory CourseAnalytics.fromJson(Map<String, dynamic> json) {
    return CourseAnalytics(
      courseId: json['course_id'] ?? json['courseId'] ?? '',
      title: json['title'] ?? '',
      averageGrade: (json['average_grade'] ?? 0).toDouble(),
      completionRate: (json['completion_rate'] ?? 0).toDouble(),
      enrolledStudents: json['enrolled_students'] ?? 0,
      completedStudents: json['completed_students'] ?? 0,
      enrollmentTrends: json['enrollment_trends'] != null
          ? (json['enrollment_trends'] as List)
              .map((trendJson) => EnrollmentTrend.fromJson(trendJson))
              .toList()
          : [],
      additionalData: json,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'course_id': courseId,
      'title': title,
      'average_grade': averageGrade,
      'completion_rate': completionRate,
      'enrolled_students': enrolledStudents,
      'completed_students': completedStudents,
      'enrollment_trends': enrollmentTrends.map((t) => t.toJson()).toList(),
    };
  }
}

class EnrollmentTrend {
  final DateTime date;
  final int newEnrollments;
  final int dropouts;
  final int activeStudents;

  EnrollmentTrend({
    required this.date,
    required this.newEnrollments,
    required this.dropouts,
    required this.activeStudents,
  });

  // Factory constructor to create from JSON
  factory EnrollmentTrend.fromJson(Map<String, dynamic> json) {
    return EnrollmentTrend(
      date: json['date'] != null 
          ? DateTime.parse(json['date']) 
          : DateTime.now(),
      newEnrollments: json['new_enrollments'] ?? 0,
      dropouts: json['dropouts'] ?? 0,
      activeStudents: json['active_students'] ?? 0,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'date': date.toIso8601String(),
      'new_enrollments': newEnrollments,
      'dropouts': dropouts,
      'active_students': activeStudents,
    };
  }
}