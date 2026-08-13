"""
Test Program Model

This module provides comprehensive tests for the ProgramModel.
It includes unit tests for all methods and functionality.

Author: Edu-Flow Team
"""

import unittest
from datetime import datetime, date
import pytest
from unittest.mock import patch, MagicMock
import json

from src.infrastructure.models.program_model import ProgramModel
from src.core.exceptions import ValidationError


class TestProgramModel(unittest.TestCase):
    """Test cases for ProgramModel."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.program_data = {
            'id': 'prog_001',
            'code': 'CS101',
            'name': 'Computer Science',
            'short_name': 'BSc CS',
            'type': 'undergraduate',
            'level': 'bachelors',
            'duration_years': 4,
            'duration_months': 0,
            'total_credits': 120,
            'total_semesters': 8,
            'department_id': 'dept_001',
            'has_specializations': True,
            'specializations': ['AI', 'Data Science', 'Cybersecurity'],
            'core_courses': [
                {'code': 'CS101', 'name': 'Introduction to Programming', 'credits': 4}
            ],
            'elective_courses': [
                {'code': 'CS201', 'name': 'Advanced Programming', 'credits': 3}
            ],
            'foundation_courses': [
                {'code': 'MATH101', 'name': 'Calculus', 'credits': 3}
            ],
            'max_capacity': 100,
            'current_enrollment': 75,
            'minimum_gpa': 3.0,
            'status': 'active',
            'is_active': True,
            'is_open_for_admission': True,
            'delivery_mode': 'full_time',
            'has_online_components': False,
            'has_practical_components': True,
            'tuition_fee': {
                'currency': 'USD',
                'tuition_per_semester': 5000,
                'total_tuition': 40000
            },
            'additional_fees': {
                'registration_fee': 500,
                'lab_fee': 1000
            },
            'graduation_rate': 85,
            'employment_rate': 90,
            'average_gpa': 3.5
        }
    
    def test_program_creation(self):
        """Test program creation with valid data."""
        program = ProgramModel(**self.program_data)
        
        self.assertEqual(program.id, 'prog_001')
        self.assertEqual(program.code, 'CS101')
        self.assertEqual(program.name, 'Computer Science')
        self.assertEqual(program.short_name, 'BSc CS')
        self.assertEqual(program.type, 'undergraduate')
        self.assertEqual(program.level, 'bachelors')
        self.assertEqual(program.duration_years, 4)
        self.assertEqual(program.duration_months, 0)
        self.assertEqual(program.total_credits, 120)
        self.assertEqual(program.total_semesters, 8)
        self.assertEqual(program.department_id, 'dept_001')
        self.assertTrue(program.has_specializations)
        self.assertEqual(len(program.specializations), 3)
        self.assertEqual(program.max_capacity, 100)
        self.assertEqual(program.current_enrollment, 75)
        self.assertEqual(program.minimum_gpa, 3.0)
        self.assertEqual(program.status, 'active')
        self.assertTrue(program.is_active)
        self.assertTrue(program.is_open_for_admission)
        self.assertEqual(program.delivery_mode, 'full_time')
        self.assertFalse(program.has_online_components)
        self.assertTrue(program.has_practical_components)
        self.assertEqual(program.graduation_rate, 85)
        self.assertEqual(program.employment_rate, 90)
        self.assertEqual(program.average_gpa, 3.5)
        
        # Test default values
        self.assertEqual(program.semester_credits, [15, 15, 15, 15, 15, 15, 15, 15])
        self.assertEqual(program.core_subject_ids, [])
        self.assertEqual(program.elective_subject_ids, [])
        self.assertEqual(program.mandatory_subject_ids, [])
        self.assertEqual(program.program_outcomes, [])
        self.assertEqual(program.course_outcomes, [])
        self.assertEqual(program.graduate_attributes, [])
        self.assertEqual(program.admission_requirements, {})
        self.assertEqual(program.is_joint_program, False)
        self.assertEqual(program.is_online_program, False)
        self.assertEqual(program.is_accredited, True)
        self.assertEqual(program.is_flexible, False)
        self.assertEqual(program.scholarship_available, True)
        self.assertEqual(program.financial_aid_available, True)
        self.assertEqual(program.total_enrollments, 0)
    
    def test_program_type_validation(self):
        """Test program type validation."""
        # Valid types
        valid_types = ['undergraduate', 'postgraduate', 'diploma', 'certificate', 'vocational']
        for program_type in valid_types:
            program = ProgramModel(**self.program_data, type=program_type)
            self.assertEqual(program.type, program_type)
        
        # Invalid type
        with self.assertRaises(ValidationError):
            ProgramModel(**self.program_data, type='invalid_type')
    
    def test_program_level_validation(self):
        """Test program level validation."""
        # Valid levels
        valid_levels = ['bachelors', 'masters', 'phd', 'diploma', 'certificate']
        for level in valid_levels:
            program = ProgramModel(**self.program_data, level=level)
            self.assertEqual(program.level, level)
        
        # Invalid level
        with self.assertRaises(ValidationError):
            ProgramModel(**self.program_data, level='invalid_level')
    
    def test_duration_validation(self):
        """Test duration validation."""
        # Valid duration
        program = ProgramModel(**self.program_data)
        self.assertEqual(program.duration_years, 4)
        self.assertEqual(program.duration_months, 0)
        
        # Negative years
        with self.assertRaises(ValidationError):
            ProgramModel(**self.program_data, duration_years=-1)
        
        # Negative months
        with self.assertRaises(ValidationError):
            ProgramModel(**self.program_data, duration_months=-1)
    
    def test_credits_validation(self):
        """Test credits validation."""
        # Valid credits
        program = ProgramModel(**self.program_data)
        self.assertEqual(program.total_credits, 120)
        
        # Negative credits
        with self.assertRaises(ValidationError):
            ProgramModel(**self.program_data, total_credits=-1)
        
        # Zero credits
        with self.assertRaises(ValidationError):
            ProgramModel(**self.program_data, total_credits=0)
    
    def test_semester_credits_initialization(self):
        """Test semester credits initialization."""
        # Test with valid semesters
        program = ProgramModel(**self.program_data)
        self.assertEqual(len(program.semester_credits), 8)
        self.assertEqual(sum(program.semester_credits), 120)
        
        # Test with no semesters
        program_no_semesters = ProgramModel(**self.program_data, total_semesters=0)
        self.assertEqual(program_no_semesters.semester_credits, [])
    
    def test_to_dict(self):
        """Test program to dictionary conversion."""
        program = ProgramModel(**self.program_data)
        program_dict = program.to_dict()
        
        # Check basic fields
        self.assertEqual(program_dict['id'], 'prog_001')
        self.assertEqual(program_dict['code'], 'CS101')
        self.assertEqual(program_dict['name'], 'Computer Science')
        
        # Check calculated fields
        self.assertEqual(program_dict['total_duration_months'], 48)
        self.assertEqual(program_dict['enrollment_percentage'], 75.0)
        self.assertTrue(program_dict['is_full'])
        self.assertEqual(program_dict['program_type'], 'undergraduate')
        
        # Check JSON fields
        self.assertEqual(len(program_dict['specializations']), 3)
        self.assertEqual(len(program_dict['core_courses']), 1)
        self.assertEqual(len(program_dict['elective_courses']), 1)
        self.assertEqual(len(program_dict['foundation_courses']), 1)
        
        # Check tuition fee structure
        self.assertEqual(program_dict['tuition_fee']['currency'], 'USD')
        self.assertEqual(program_dict['tuition_fee']['tuition_per_semester'], 5000)
        self.assertEqual(program_dict['tuition_fee']['total_tuition'], 40000)
    
    def test_add_specialization(self):
        """Test adding specializations."""
        program = ProgramModel(**self.program_data)
        
        # Add specialization
        program.add_specialization('AI', 'Artificial Intelligence specialization')
        self.assertEqual(len(program.specializations), 1)
        self.assertEqual(program.specializations[0]['specialization_name'], 'AI')
        self.assertTrue(program.has_specializations)
        
        # Add same specialization again (should not duplicate)
        program.add_specialization('AI', 'AI specialization')
        self.assertEqual(len(program.specializations), 1)
        
        # Add different specialization
        program.add_specialization('Data Science', 'Data Science specialization')
        self.assertEqual(len(program.specializations), 2)
    
    def test_remove_specialization(self):
        """Test removing specializations."""
        program = ProgramModel(**self.program_data)
        
        # Add specializations first
        program.add_specialization('AI', 'AI specialization')
        program.add_specialization('Data Science', 'Data Science specialization')
        self.assertEqual(len(program.specializations), 2)
        
        # Remove specialization
        program.remove_specialization('AI')
        self.assertEqual(len(program.specializations), 1)
        self.assertEqual(program.specializations[0]['specialization_name'], 'Data Science')
        
        # Remove non-existent specialization
        program.remove_specialization('Cybersecurity')
        self.assertEqual(len(program.specializations), 1)
        
        # Remove last specialization
        program.remove_specialization('Data Science')
        self.assertEqual(len(program.specializations), 0)
        self.assertFalse(program.has_specializations)
    
    def test_add_core_course(self):
        """Test adding core courses."""
        program = ProgramModel(**self.program_data)
        
        # Add core course
        program.add_core_course('CS101', 'Introduction to Programming', 4, [])
        self.assertEqual(len(program.core_courses), 1)
        self.assertEqual(program.core_courses[0]['course_code'], 'CS101')
        
        # Add course with prerequisites
        program.add_core_course('CS201', 'Data Structures', 4, ['CS101'])
        self.assertEqual(len(program.core_courses), 2)
        self.assertEqual(program.core_courses[1]['prerequisites'], ['CS101'])
        
        # Add same course again (should not duplicate)
        program.add_core_course('CS101', 'Programming Basics', 3, [])
        self.assertEqual(len(program.core_courses), 2)
    
    def test_remove_core_course(self):
        """Test removing core courses."""
        program = ProgramModel(**self.program_data)
        
        # Add courses first
        program.add_core_course('CS101', 'Programming', 4)
        program.add_core_course('CS201', 'Data Structures', 4)
        self.assertEqual(len(program.core_courses), 2)
        
        # Remove course
        program.remove_core_course('CS101')
        self.assertEqual(len(program.core_courses), 1)
        self.assertEqual(program.core_courses[0]['course_code'], 'CS201')
        
        # Remove non-existent course
        program.remove_core_course('CS301')
        self.assertEqual(len(program.core_courses), 1)
    
    def test_add_elective_course(self):
        """Test adding elective courses."""
        program = ProgramModel(**self.program_data)
        
        # Add elective course
        program.add_elective_course('CS301', 'Machine Learning', 3, [], 'AI')
        self.assertEqual(len(program.elective_courses), 1)
        self.assertEqual(program.elective_courses[0]['course_code'], 'CS301')
        self.assertEqual(program.elective_courses[0]['category'], 'AI')
        
        # Add course with category
        program.add_elective_course('CS401', 'Deep Learning', 3, [], 'AI')
        self.assertEqual(len(program.elective_courses), 2)
        
        # Add same course again (should not duplicate)
        program.add_elective_course('CS301', 'ML Basics', 2, [], 'AI')
        self.assertEqual(len(program.elective_courses), 2)
    
    def test_remove_elective_course(self):
        """Test removing elective courses."""
        program = ProgramModel(**self.program_data)
        
        # Add courses first
        program.add_elective_course('CS301', 'Machine Learning', 3, [], 'AI')
        program.add_elective_course('CS401', 'Deep Learning', 3, [], 'AI')
        self.assertEqual(len(program.elective_courses), 2)
        
        # Remove course
        program.remove_elective_course('CS301')
        self.assertEqual(len(program.elective_courses), 1)
        self.assertEqual(program.elective_courses[0]['course_code'], 'CS401')
        
        # Remove non-existent course
        program.remove_elective_course('CS501')
        self.assertEqual(len(program.elective_courses), 1)
    
    def test_add_foundation_course(self):
        """Test adding foundation courses."""
        program = ProgramModel(**self.program_data)
        
        # Add foundation course
        program.add_foundation_course('MATH101', 'Calculus', 3, [])
        self.assertEqual(len(program.foundation_courses), 1)
        self.assertEqual(program.foundation_courses[0]['course_code'], 'MATH101')
        
        # Add course with prerequisites
        program.add_foundation_course('MATH201', 'Linear Algebra', 3, ['MATH101'])
        self.assertEqual(len(program.foundation_courses), 2)
        self.assertEqual(program.foundation_courses[1]['prerequisites'], ['MATH101'])
        
        # Add same course again (should not duplicate)
        program.add_foundation_course('MATH101', 'Advanced Calculus', 4, [])
        self.assertEqual(len(program.foundation_courses), 2)
    
    def test_remove_foundation_course(self):
        """Test removing foundation courses."""
        program = ProgramModel(**self.program_data)
        
        # Add courses first
        program.add_foundation_course('MATH101', 'Calculus', 3)
        program.add_foundation_course('MATH201', 'Linear Algebra', 3)
        self.assertEqual(len(program.foundation_courses), 2)
        
        # Remove course
        program.remove_foundation_course('MATH101')
        self.assertEqual(len(program.foundation_courses), 1)
        self.assertEqual(program.foundation_courses[0]['course_code'], 'MATH201')
        
        # Remove non-existent course
        program.remove_foundation_course('MATH301')
        self.assertEqual(len(program.foundation_courses), 1)
    
    def test_update_tuition_fee(self):
        """Test updating tuition fee structure."""
        program = ProgramModel(**self.program_data)
        
        # Update tuition fee
        new_fee_structure = {
            'tuition_per_semester': 6000,
            'total_tuition': 48000,
            'lab_fee': 1000
        }
        program.update_tuition_fee(new_fee_structure, 'USD')
        
        self.assertEqual(program.tuition_fee['currency'], 'USD')
        self.assertEqual(program.tuition_fee['fee_structure'], new_fee_structure)
        self.assertTrue(program.updated_at > datetime.now() - timedelta(seconds=1))
    
    def test_update_additional_fees(self):
        """Test updating additional fees."""
        program = ProgramModel(**self.program_data)
        
        # Update additional fees
        new_fees = {
            'registration_fee': 600,
            'lab_fee': 1200,
            'material_fee': 300
        }
        program.update_additional_fees(new_fees)
        
        self.assertEqual(program.additional_fees['fees'], new_fees)
        self.assertTrue(program.updated_at > datetime.now() - timedelta(seconds=1))
    
    def test_add_program_coordinator(self):
        """Test adding program coordinators."""
        program = ProgramModel(**self.program_data)
        
        # Add coordinator
        program.add_program_coordinator('coord_001', 'Dr. Smith', 'Program Director')
        self.assertEqual(len(program.program_coordinators), 1)
        self.assertEqual(program.program_coordinators[0]['coordinator_id'], 'coord_001')
        self.assertEqual(program.program_coordinators[0]['coordinator_name'], 'Dr. Smith')
        
        # Add same coordinator again (should not duplicate)
        program.add_program_coordinator('coord_001', 'Prof. Smith', 'Director')
        self.assertEqual(len(program.program_coordinators), 1)
        
        # Add different coordinator
        program.add_program_coordinator('coord_002', 'Dr. Johnson', 'Academic Coordinator')
        self.assertEqual(len(program.program_coordinators), 2)
    
    def test_remove_program_coordinator(self):
        """Test removing program coordinators."""
        program = ProgramModel(**self.program_data)
        
        # Add coordinators first
        program.add_program_coordinator('coord_001', 'Dr. Smith', 'Program Director')
        program.add_program_coordinator('coord_002', 'Dr. Johnson', 'Academic Coordinator')
        self.assertEqual(len(program.program_coordinators), 2)
        
        # Remove coordinator
        program.remove_program_coordinator('coord_001')
        self.assertEqual(len(program.program_coordinators), 1)
        self.assertEqual(program.program_coordinators[0]['coordinator_id'], 'coord_002')
        
        # Remove non-existent coordinator
        program.remove_program_coordinator('coord_003')
        self.assertEqual(len(program.program_coordinators), 1)
    
    def test_add_industry_partner(self):
        """Test adding industry partners."""
        program = ProgramModel(**self.program_data)
        
        # Add partner
        program.add_industry_partner('Tech Corp', 'Corporate Partnership', 'Annual internship program')
        self.assertEqual(len(program.industry_partners), 1)
        self.assertEqual(program.industry_partners[0]['partner_name'], 'Tech Corp')
        self.assertEqual(program.industry_partners[0]['partner_type'], 'Corporate Partnership')
        
        # Add same partner again (should not duplicate)
        program.add_industry_partner('Tech Corp', 'Internship', 'Paid internships')
        self.assertEqual(len(program.industry_partners), 1)
        
        # Add different partner
        program.add_industry_partner('StartUp Inc', 'Incubation', 'Startup incubation program')
        self.assertEqual(len(program.industry_partners), 2)
    
    def test_remove_industry_partner(self):
        """Test removing industry partners."""
        program = ProgramModel(**self.program_data)
        
        # Add partners first
        program.add_industry_partner('Tech Corp', 'Corporate Partnership')
        program.add_industry_partner('StartUp Inc', 'Incubation')
        self.assertEqual(len(program.industry_partners), 2)
        
        # Remove partner
        program.remove_industry_partner('Tech Corp')
        self.assertEqual(len(program.industry_partners), 1)
        self.assertEqual(program.industry_partners[0]['partner_name'], 'StartUp Inc')
        
        # Remove non-existent partner
        program.remove_industry_partner('NonExistent Corp')
        self.assertEqual(len(program.industry_partners), 1)
    
    def test_add_research_area(self):
        """Test adding research areas."""
        program = ProgramModel(**self.program_data)
        
        # Add research area
        program.add_research_area('Artificial Intelligence', 'Machine learning and neural networks')
        self.assertEqual(len(program.research_areas), 1)
        self.assertEqual(program.research_areas[0]['research_area'], 'Artificial Intelligence')
        
        # Add same research area again (should not duplicate)
        program.add_research_area('AI', 'Advanced intelligence systems')
        self.assertEqual(len(program.research_areas), 1)
        
        # Add different research area
        program.add_research_area('Data Science', 'Big data analytics')
        self.assertEqual(len(program.research_areas), 2)
    
    def test_remove_research_area(self):
        """Test removing research areas."""
        program = ProgramModel(**self.program_data)
        
        # Add research areas first
        program.add_research_area('AI', 'Machine learning')
        program.add_research_area('Data Science', 'Big data')
        self.assertEqual(len(program.research_areas), 2)
        
        # Remove research area
        program.remove_research_area('AI')
        self.assertEqual(len(program.research_areas), 1)
        self.assertEqual(program.research_areas[0]['research_area'], 'Data Science')
        
        # Remove non-existent research area
        program.remove_research_area('Cybersecurity')
        self.assertEqual(len(program.research_areas), 1)
    
    def test_update_enrollment_statistics(self):
        """Test updating enrollment statistics."""
        program = ProgramModel(**self.program_data)
        
        # Update statistics
        program.update_enrollment_statistics(150, 120, 85, 90, 3.5)
        
        self.assertEqual(program.total_enrollments, 150)
        self.assertEqual(program.current_enrollments, 120)
        self.assertEqual(program.graduation_rate, 85)
        self.assertEqual(program.employment_rate, 90)
        self.assertEqual(program.average_gpa, 3.5)
        
        # Test validation
        with self.assertRaises(ValidationError):
            program.update_enrollment_statistics(-1, 100)  # Negative total
        
        with self.assertRaises(ValidationError):
            program.update_enrollment_statistics(100, 150)  # Current > total
        
        with self.assertRaises(ValidationError):
            program.update_enrollment_statistics(100, 100, 101)  # Invalid graduation rate
        
        with self.assertRaises(ValidationError):
            program.update_enrollment_statistics(100, 100, 85, 101)  # Invalid employment rate
    
    def test_update_accreditation(self):
        """Test updating accreditation information."""
        program = ProgramModel(**self.program_data)
        
        # Update accreditation
        accreditation_expiry = datetime.now() + timedelta(days=365)
        program.update_accreditation(True, 'ABET', accreditation_expiry)
        
        self.assertTrue(program.is_accredited)
        self.assertEqual(program.accreditation_body, 'ABET')
        self.assertEqual(program.accreditation_expiry_date, accreditation_expiry)
        
        # Test validation - past expiry date
        past_expiry = datetime.now() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            program.update_accreditation(True, 'ABET', past_expiry)
        
        # Test de-accreditation
        program.update_accreditation(False)
        self.assertFalse(program.is_accredited)
    
    def test_update_delivery_mode(self):
        """Test updating program delivery mode."""
        program = ProgramModel(**self.program_data)
        
        # Update delivery mode
        program.update_delivery_mode('hybrid', True, True, True)
        
        self.assertEqual(program.delivery_mode, 'hybrid')
        self.assertTrue(program.is_flexible)
        self.assertTrue(program.has_online_components)
        self.assertTrue(program.has_practical_components)
        
        # Test validation - invalid mode
        with self.assertRaises(ValidationError):
            program.update_delivery_mode('invalid_mode')
    
    def test_update_program_status(self):
        """Test updating program status."""
        program = ProgramModel(**self.program_data)
        
        # Update status
        program.update_program_status(False, False)
        
        self.assertFalse(program.is_active)
        self.assertFalse(program.is_open_for_admission)
        
        # Test validation - invalid status
        with self.assertRaises(ValidationError):
            program.update_program_status('invalid_status')
    
    def test_get_program_status(self):
        """Test program status calculation."""
        program = ProgramModel(**self.program_data)
        
        # Test active program
        self.assertEqual(program.get_program_status(), 'active')
        
        # Test inactive program
        program.is_active = False
        self.assertEqual(program.get_program_status(), 'inactive')
        
        # Test closed program
        program.is_active = True
        program.is_open_for_admission = False
        self.assertEqual(program.get_program_status(), 'not_open')
        
        # Test unaccredited program
        program.is_open_for_admission = True
        program.is_accredited = False
        self.assertEqual(program.get_program_status(), 'not_accredited')
        
        # Test expired accreditation
        program.is_accredited = True
        program.accreditation_expiry_date = datetime.now() - timedelta(days=1)
        self.assertEqual(program.get_program_status(), 'accreditation_expired')
    
    def test_get_enrollment_percentage(self):
        """Test enrollment percentage calculation."""
        program = ProgramModel(**self.program_data)
        
        # Test with capacity
        self.assertEqual(program.get_enrollment_percentage(), 75.0)
        
        # Test with no capacity
        program.max_capacity = 0
        self.assertEqual(program.get_enrollment_percentage(), 0.0)
        
        # Test with full capacity
        program.max_capacity = 75
        self.assertEqual(program.get_enrollment_percentage(), 100.0)
    
    def test_get_credits_completed(self):
        """Test credits completed calculation."""
        program = ProgramModel(**self.program_data)
        
        # Test with no enrollments (placeholder)
        self.assertEqual(program.get_credits_completed(), 0)
    
    def test_get_semester_progress(self):
        """Test semester progress calculation."""
        program = ProgramModel(**self.program_data)
        
        progress = program.get_semester_progress()
        
        self.assertEqual(progress['total_semesters'], 8)
        self.assertEqual(progress['current_semester'], 1)  # Placeholder
        self.assertEqual(progress['progress_percentage'], 0)  # Placeholder
        self.assertEqual(progress['remaining_semesters'], 7)  # Placeholder
        self.assertEqual(progress['credits_per_semester'], 15)
        self.assertEqual(progress['total_credits'], 120)
        self.assertEqual(len(progress['semester_credits']), 8)
    
    def test_get_time_to_completion(self):
        """Test time to completion calculation."""
        program = ProgramModel(**self.program_data)
        
        time_info = program.get_time_to_completion()
        
        self.assertEqual(time_info['duration_years'], 4)
        self.assertEqual(time_info['duration_months'], 0)
        self.assertEqual(time_info['total_months'], 48)
        self.assertEqual(time_info['estimated_completion_date'], None)  # Placeholder
        self.assertEqual(time_info['remaining_time_years'], 4)  # Placeholder
        self.assertEqual(time_info['remaining_time_months'], 0)  # Placeholder
        self.assertTrue(time_info['is_on_schedule'])  # Placeholder
    
    def test_get_program_summary(self):
        """Test program summary generation."""
        program = ProgramModel(**self.program_data)
        
        summary = program.get_program_summary()
        
        self.assertEqual(summary['id'], 'prog_001')
        self.assertEqual(summary['code'], 'CS101')
        self.assertEqual(summary['name'], 'Computer Science')
        self.assertEqual(summary['type'], 'undergraduate')
        self.assertEqual(summary['level'], 'bachelors')
        self.assertEqual(summary['status'], 'active')
        self.assertEqual(summary['department_id'], 'dept_001')
        self.assertTrue(summary['is_active'])
        self.assertTrue(summary['is_open_for_admission'])
        self.assertTrue(summary['is_accredited'])
        self.assertEqual(summary['delivery_mode'], 'full_time')
        self.assertFalse(summary['is_flexible'])
        self.assertTrue(summary['has_specializations'])
        self.assertEqual(summary['specializations_count'], 3)
        self.assertEqual(summary['total_credits'], 120)
        self.assertEqual(summary['total_semesters'], 8)
        self.assertEqual(summary['enrollment_percentage'], 75.0)
        self.assertEqual(summary['graduation_rate'], 85)
        self.assertEqual(summary['employment_rate'], 90)
        self.assertEqual(summary['average_gpa'], 3.5)
        self.assertTrue(summary['scholarship_available'])
        self.assertTrue(summary['financial_aid_available'])
    
    def test_get_fee_structure_summary(self):
        """Test fee structure summary generation."""
        program = ProgramModel(**self.program_data)
        
        fee_summary = program.get_fee_structure_summary()
        
        self.assertEqual(fee_summary['currency'], 'USD')
        self.assertEqual(fee_summary['tuition_fees']['tuition_per_semester'], 5000)
        self.assertEqual(fee_summary['tuition_fees']['total_tuition'], 40000)
        self.assertEqual(fee_summary['additional_fees']['registration_fee'], 500)
        self.assertEqual(fee_summary['additional_fees']['lab_fee'], 1000)
        self.assertEqual(fee_summary['total_estimated_fees'], 41500)
        self.assertTrue(fee_summary['scholarship_available'])
        self.assertTrue(fee_summary['financial_aid_available'])
    
    def test_get_enrollment_trends(self):
        """Test enrollment trends calculation."""
        program = ProgramModel(**self.program_data)
        
        trends = program.get_enrollment_trends()
        
        self.assertEqual(trends['total_enrollments'], 0)  # Placeholder
        self.assertEqual(trends['current_enrollments'], 75)
        self.assertEqual(trends['enrollment_percentage'], 75.0)
        self.assertEqual(trends['graduation_rate'], 85)
        self.assertEqual(trends['employment_rate'], 90)
        self.assertEqual(trends['average_gpa'], 3.5)
        self.assertEqual(trends['enrollment_growth_rate'], 0)  # Placeholder
    
    def test_get_program_metrics(self):
        """Test program metrics calculation."""
        program = ProgramModel(**self.program_data)
        
        metrics = program.get_program_metrics()
        
        # All metrics are placeholders for now
        self.assertEqual(metrics['student_sat_rate'], 0)
        self.assertEqual(metrics['course_completion_rate'], 0)
        self.assertEqual(metrics['retention_rate'], 0)
        self.assertEqual(metrics['faculty_student_ratio'], 0)
        self.assertEqual(metrics['course_utilization_rate'], 0)
        self.assertEqual(metrics['program_duration_actual'], 0)
        self.assertEqual(metrics['alumni_satisfaction_rate'], 0)
    
    def test_program_representation(self):
        """Test program string representation."""
        program = ProgramModel(**self.program_data)
        
        expected_repr = "<ProgramModel(code='CS101', name='Computer Science', type='undergraduate', level='bachelors', status='active')>"
        self.assertEqual(repr(program), expected_repr)


if __name__ == '__main__':
    unittest.main()