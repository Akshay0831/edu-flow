import 'dart:convert';

class Feedback {
  final String id;
  final String courseId;
  final String studentId;
  final String teacherId;
  final String type; // 'student_feedback', 'teacher_feedback', 'course_evaluation'
  final String rating;
  final String comment;
  final List<String> tags;
  final DateTime submittedAt;
  final DateTime updatedAt;
  final Map<String, dynamic>? additionalData;

  Feedback({
    required this.id,
    required this.courseId,
    required this.studentId,
    required this.teacherId,
    required this.type,
    required this.rating,
    required this.comment,
    required this.tags,
    required this.submittedAt,
    required this.updatedAt,
    this.additionalData,
  });

  // Factory constructor to create from JSON
  factory Feedback.fromJson(Map<String, dynamic> json) {
    return Feedback(
      id: json['id'] ?? json['feedback_id'] ?? '',
      courseId: json['course_id'] ?? json['courseId'] ?? '',
      studentId: json['student_id'] ?? json['studentId'] ?? '',
      teacherId: json['teacher_id'] ?? json['teacherId'] ?? '',
      type: json['type'] ?? 'student_feedback',
      rating: json['rating'] ?? '5',
      comment: json['comment'] ?? '',
      tags: json['tags'] != null 
          ? List<String>.from(json['tags']) 
          : [],
      submittedAt: json['submitted_at'] != null 
          ? DateTime.parse(json['submitted_at']) 
          : DateTime.now(),
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at']) 
          : DateTime.now(),
      additionalData: json,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'course_id': courseId,
      'student_id': studentId,
      'teacher_id': teacherId,
      'type': type,
      'rating': rating,
      'comment': comment,
      'tags': tags,
      'submitted_at': submittedAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}

class FeedbackSummary {
  final String courseId;
  final double averageRating;
  final int totalFeedbacks;
  final Map<String, int> ratingDistribution;
  final List<String> commonTags;
  final List<String> positiveComments;
  final List<String> negativeComments;
  final DateTime lastUpdated;
  final Map<String, dynamic>? additionalData;

  FeedbackSummary({
    required this.courseId,
    required this.averageRating,
    required this.totalFeedbacks,
    required this.ratingDistribution,
    required this.commonTags,
    required this.positiveComments,
    required this.negativeComments,
    required this.lastUpdated,
    this.additionalData,
  });

  // Factory constructor to create from JSON
  factory FeedbackSummary.fromJson(Map<String, dynamic> json) {
    return FeedbackSummary(
      courseId: json['course_id'] ?? json['courseId'] ?? '',
      averageRating: (json['average_rating'] ?? 0).toDouble(),
      totalFeedbacks: json['total_feedbacks'] ?? 0,
      ratingDistribution: json['rating_distribution'] != null 
          ? Map<String, int>.from(json['rating_distribution']) 
          : {},
      commonTags: json['common_tags'] != null 
          ? List<String>.from(json['common_tags']) 
          : [],
      positiveComments: json['positive_comments'] != null 
          ? List<String>.from(json['positive_comments']) 
          : [],
      negativeComments: json['negative_comments'] != null 
          ? List<String>.from(json['negative_comments']) 
          : [],
      lastUpdated: json['last_updated'] != null 
          ? DateTime.parse(json['last_updated']) 
          : DateTime.now(),
      additionalData: json,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'course_id': courseId,
      'average_rating': averageRating,
      'total_feedbacks': totalFeedbacks,
      'rating_distribution': ratingDistribution,
      'common_tags': commonTags,
      'positive_comments': positiveComments,
      'negative_comments': negativeComments,
      'last_updated': lastUpdated.toIso8601String(),
    };
  }
}

class SentimentAnalysis {
  final String feedbackId;
  final String sentiment; // 'positive', 'negative', 'neutral'
  final double confidence;
  final Map<String, double> emotionScores;
  final List<String> keywords;
  final List<String> suggestions;
  final DateTime analyzedAt;
  final Map<String, dynamic>? additionalData;

  SentimentAnalysis({
    required this.feedbackId,
    required this.sentiment,
    required this.confidence,
    required this.emotionScores,
    required this.keywords,
    required this.suggestions,
    required this.analyzedAt,
    this.additionalData,
  });

  // Factory constructor to create from JSON
  factory SentimentAnalysis.fromJson(Map<String, dynamic> json) {
    return SentimentAnalysis(
      feedbackId: json['feedback_id'] ?? json['feedbackId'] ?? '',
      sentiment: json['sentiment'] ?? 'neutral',
      confidence: (json['confidence'] ?? 0).toDouble(),
      emotionScores: json['emotion_scores'] != null 
          ? Map<String, double>.from(json['emotion_scores']) 
          : {},
      keywords: json['keywords'] != null 
          ? List<String>.from(json['keywords']) 
          : [],
      suggestions: json['suggestions'] != null 
          ? List<String>.from(json['suggestions']) 
          : [],
      analyzedAt: json['analyzed_at'] != null 
          ? DateTime.parse(json['analyzed_at']) 
          : DateTime.now(),
      additionalData: json,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'feedback_id': feedbackId,
      'sentiment': sentiment,
      'confidence': confidence,
      'emotion_scores': emotionScores,
      'keywords': keywords,
      'suggestions': suggestions,
      'analyzed_at': analyzedAt.toIso8601String(),
    };
  }
}

class FeedbackReport {
  final String courseId;
  final String title;
  final DateTime generatedAt;
  final FeedbackSummary summary;
  final List<Feedback> feedbacks;
  final List<ActionItem> actionItems;
  final List<String> recommendations;
  final Map<String, dynamic>? additionalData;

  FeedbackReport({
    required this.courseId,
    required this.title,
    required this.generatedAt,
    required this.summary,
    required this.feedbacks,
    required this.actionItems,
    required this.recommendations,
    this.additionalData,
  });

  // Factory constructor to create from JSON
  factory FeedbackReport.fromJson(Map<String, dynamic> json) {
    return FeedbackReport(
      courseId: json['course_id'] ?? json['courseId'] ?? '',
      title: json['title'] ?? '',
      generatedAt: json['generated_at'] != null 
          ? DateTime.parse(json['generated_at']) 
          : DateTime.now(),
      summary: FeedbackSummary.fromJson(json['summary'] ?? {}),
      feedbacks: json['feedbacks'] != null
          ? (json['feedbacks'] as List)
              .map((feedbackJson) => Feedback.fromJson(feedbackJson))
              .toList()
          : [],
      actionItems: json['action_items'] != null
          ? (json['action_items'] as List)
              .map((itemJson) => ActionItem.fromJson(itemJson))
              .toList()
          : [],
      recommendations: json['recommendations'] != null 
          ? List<String>.from(json['recommendations']) 
          : [],
      additionalData: json,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'course_id': courseId,
      'title': title,
      'generated_at': generatedAt.toIso8601String(),
      'summary': summary.toJson(),
      'feedbacks': feedbacks.map((f) => f.toJson()).toList(),
      'action_items': actionItems.map((a) => a.toJson()).toList(),
      'recommendations': recommendations,
    };
  }
}

class ActionItem {
  final String id;
  final String title;
  final String description;
  final String priority; // 'high', 'medium', 'low'
  final String assigneeId;
  final String assigneeName;
  final DateTime dueDate;
  final String status; // 'pending', 'in_progress', 'completed'
  final DateTime createdAt;
  final DateTime updatedAt;
  final Map<String, dynamic>? additionalData;

  ActionItem({
    required this.id,
    required this.title,
    required this.description,
    required this.priority,
    required this.assigneeId,
    required this.assigneeName,
    required this.dueDate,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    this.additionalData,
  });

  // Factory constructor to create from JSON
  factory ActionItem.fromJson(Map<String, dynamic> json) {
    return ActionItem(
      id: json['id'] ?? json['action_id'] ?? '',
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      priority: json['priority'] ?? 'medium',
      assigneeId: json['assignee_id'] ?? json['assigneeId'] ?? '',
      assigneeName: json['assignee_name'] ?? json['assigneeName'] ?? '',
      dueDate: json['due_date'] != null 
          ? DateTime.parse(json['due_date']) 
          : DateTime.now(),
      status: json['status'] ?? 'pending',
      createdAt: json['created_at'] != null 
          ? DateTime.parse(json['created_at']) 
          : DateTime.now(),
      updatedAt: json['updated_at'] != null 
          ? DateTime.parse(json['updated_at']) 
          : DateTime.now(),
      additionalData: json,
    );
  }

  // Method to convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'priority': priority,
      'assignee_id': assigneeId,
      'assignee_name': assigneeName,
      'due_date': dueDate.toIso8601String(),
      'status': status,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}