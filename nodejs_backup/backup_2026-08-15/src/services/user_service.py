"""
User Management Service

This service handles all user-related operations including:
- User creation, update, and deletion
- User authentication and authorization
- User profile management
- User search and filtering
- User activity logging
- User audit trail
- User permission management

Author: Edu-Flow Team
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import re
import hashlib
import hmac
from uuid import uuid4

from ..core.security import AuthService
from ..core.exceptions import ValidationError, NotFoundError, AuthenticationError
from ..services.database_manager import db_manager


class UserService:
    """User Management Service"""
    
    def __init__(self, auth_service = None):
        """Initialize the user service"""
        self.auth_service = auth_service or AuthService()
        self.users = {}  # In-memory storage for demo
        self.user_activities = {}  # User activity logging
        self.audit_trail = {}  # User audit trail
        self._db_initialized = False
        
    async def initialize(self):
        """Initialize the user service"""
        # Initialize database manager
        await db_manager.initialize()
        self._db_initialized = True
        
    async def dispose(self):
        """Dispose of the user service resources"""
        # Clean up database connections
        if self._db_initialized:
            await db_manager.close()
        self._db_initialized = False
        
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*(),.?":{}|<>' for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def validate_role(self, role: str) -> bool:
        """Validate user role"""
        valid_roles = ['student', 'teacher', 'admin', 'staff']
        return role in valid_roles
    
    async def create_user(self, email: str, password: str, name: str, role: str, **kwargs) -> Dict[str, Any]:
        """
        Create a new user
        
        Args:
            email: User email address
            password: User password
            name: User display name
            role: User role (student, teacher, admin, staff)
            **kwargs: Additional user data
            
        Returns:
            Dict containing user information
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate inputs
        if not self.validate_email(email):
            raise ValidationError("Invalid email format")
        
        if not self.validate_password(password):
            raise ValidationError("Password does not meet requirements")
        
        if not self.validate_role(role):
            raise ValidationError("Invalid role")
        
        # Check if user already exists
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise ValidationError("User with this email already exists")
        
        # Create user
        user_id = str(uuid4())
        now = datetime.now()
        
        user = {
            'user_id': user_id,
            'email': email,
            'name': name,
            'role': role,
            'password_hash': password,  # Password is already hashed by auth service
            'is_active': True,
            'created_at': now,
            'updated_at': now,
            'last_login': None,
            'deactivated_at': None,
            **kwargs
        }
        
        # Store user in database
        try:
            # Use database transaction
            async with db_manager.transaction():
                # Insert user
                insert_query = """
                    INSERT INTO users (user_id, email, name, role, password_hash, is_active, 
                                     created_at, updated_at, last_login, deactivated_at, department)
                    VALUES (:user_id, :email, :name, :role, :password_hash, :is_active,
                           :created_at, :updated_at, :last_login, :deactivated_at, :department)
                """
                
                await db_manager.execute_update(insert_query, {
                    'user_id': user_id,
                    'email': email,
                    'name': name,
                    'role': role,
                    'password_hash': user['password_hash'],
                    'is_active': True,
                    'created_at': now,
                    'updated_at': now,
                    'last_login': None,
                    'deactivated_at': None,
                    'department': kwargs.get('department')
                })
                
                # Log audit trail
                await self._log_audit_trail_db(user_id, 'create_user', {'email': email, 'role': role})
                
                # Cache user in memory
                self.users[user_id] = user
        
        except Exception as e:
            raise DatabaseError(f"Failed to create user: {e}")
        
        return {
            **user,
            'password_hash': None  # Don't return password hash
        }
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        # Check cache first
        user = self.users.get(user_id)
        if user:
            user_data = user.copy()
            user_data['password_hash'] = None
            return user_data
        
        # Query database
        query = "SELECT * FROM users WHERE user_id = :user_id"
        result = await db_manager.execute_query(query, {'user_id': user_id})
        
        if not result:
            raise NotFoundError("User not found")
        
        user = result[0]
        # Cache user
        self.users[user_id] = user
        
        # Don't return password hash
        user_data = user.copy()
        user_data['password_hash'] = None
        
        return user_data
    
    async def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """Get user by email"""
        # Check cache first
        for user in self.users.values():
            if user['email'] == email:
                # Return user with password hash for internal authentication
                return user.copy()
        
        # Query database
        query = "SELECT * FROM users WHERE email = :email"
        result = await db_manager.execute_query(query, {'email': email})
        
        if not result:
            raise NotFoundError("User not found")
        
        user = result[0]
        # Cache user
        self.users[user['user_id']] = user
        
        # Return user with password hash for internal authentication
        return user.copy()
    
    def update_user(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update user information"""
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Validate email if provided
        if 'email' in kwargs and kwargs['email'] != user['email']:
            if not self.validate_email(kwargs['email']):
                raise ValidationError("Invalid email format")
            
            # Check if email already exists
            if any(u['email'] == kwargs['email'] for u in self.users.values() if u['user_id'] != user_id):
                raise ValidationError("User with this email already exists")
        
        # Update user
        update_data = kwargs.copy()
        update_data['updated_at'] = datetime.now()
        
        for key, value in update_data.items():
            if key != 'password_hash':  # Don't update password hash directly
                user[key] = value
        
        self.users[user_id] = user
        
        # Log audit trail
        self._log_audit_trail(user_id, 'update_user', update_data)
        
        # Don't return password hash
        user_data = user.copy()
        user_data['password_hash'] = None
        
        return user_data
    
    def update_user_profile(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update user profile information"""
        return self.update_user(user_id, **kwargs)
    
    def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Deactivate a user"""
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Update user
        user['is_active'] = False
        user['deactivated_at'] = datetime.now()
        user['updated_at'] = datetime.now()
        self.users[user_id] = user
        
        # Log audit trail
        self._log_audit_trail(user_id, 'deactivate_user', {'deactivated_at': user['deactivated_at']})
        
        # Don't return password hash
        user_data = user.copy()
        user_data['password_hash'] = None
        
        return user_data
    
    def reactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Reactivate a deactivated user"""
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Update user
        user['is_active'] = True
        user['deactivated_at'] = None
        user['updated_at'] = datetime.now()
        self.users[user_id] = user
        
        # Log audit trail
        self._log_audit_trail(user_id, 'reactivate_user', {'reactivated_at': datetime.now()})
        
        # Don't return password hash
        user_data = user.copy()
        user_data['password_hash'] = None
        
        return user_data
    
    def change_user_role(self, user_id: str, new_role: str) -> Dict[str, Any]:
        """Change user role"""
        if not self.validate_role(new_role):
            raise ValidationError("Invalid role")
        
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        old_role = user['role']
        
        # Update user
        user['role'] = new_role
        user['updated_at'] = datetime.now()
        self.users[user_id] = user
        
        # Log audit trail
        self._log_audit_trail(user_id, 'change_user_role', {'old_role': old_role, 'new_role': new_role})
        
        # Don't return password hash
        user_data = user.copy()
        user_data['password_hash'] = None
        
        return user_data
    
    def change_user_password(self, user_id: str, new_password: str) -> Dict[str, Any]:
        """Change user password"""
        if not self.validate_password(new_password):
            raise ValidationError("Password does not meet requirements")
        
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Update password
        user['password_hash'] = self.auth_service.get_password_hash(new_password)
        user['updated_at'] = datetime.now()
        self.users[user_id] = user
        
        # Log audit trail
        self._log_audit_trail(user_id, 'change_password', {'changed_at': datetime.now()})
        
        # Don't return password hash
        user_data = user.copy()
        user_data['password_hash'] = None
        
        return user_data
    
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user (soft delete)"""
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Update user
        user['is_active'] = False
        user['deleted_at'] = datetime.now()
        user['updated_at'] = datetime.now()
        self.users[user_id] = user
        
        # Log audit trail
        self._log_audit_trail(user_id, 'delete_user', {'deleted_at': datetime.now()})
        
        # Don't return password hash
        user_data = user.copy()
        user_data['password_hash'] = None
        
        return user_data
    
    def search_users(self, query: str = "", role: str = None, department: str = None, 
                    is_active: bool = None, page: int = 1, page_size: int = 10) -> List[Dict[str, Any]]:
        """
        Search users with filtering and pagination
        
        Args:
            query: Search query for name/email
            role: Filter by role
            department: Filter by department
            is_active: Filter by active status
            page: Page number
            page_size: Number of items per page
            
        Returns:
            List of users matching the criteria
        """
        # Filter users
        filtered_users = []
        
        for user in self.users.values():
            # Apply filters
            if query:
                query_lower = query.lower()
                if not (query_lower in user['name'].lower() or query_lower in user['email'].lower()):
                    continue
            
            if role and user['role'] != role:
                continue
            
            if department and user.get('department') != department:
                continue
            
            if is_active is not None and user['is_active'] != is_active:
                continue
            
            filtered_users.append(user)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        paginated_users = filtered_users[start_idx:end_idx]
        
        # Don't return password hash
        result = []
        for user in paginated_users:
            user_data = user.copy()
            user_data['password_hash'] = None
            result.append(user_data)
        
        return result
    
    def get_user_count(self, role: str = None, is_active: bool = None) -> int:
        """Get user count with optional filters"""
        count = 0
        for user in self.users.values():
            if role and user['role'] != role:
                continue
            
            if is_active is not None and user['is_active'] != is_active:
                continue
            
            count += 1
        
        return count
    
    def bulk_deactivate_users(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """Bulk deactivate users"""
        deactivated_users = []
        
        for user_id in user_ids:
            try:
                user = self.deactivate_user(user_id)
                deactivated_users.append(user)
            except NotFoundError:
                continue
        
        return deactivated_users
    
    def bulk_reactivate_users(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """Bulk reactivate users"""
        reactivated_users = []
        
        for user_id in user_ids:
            try:
                user = self.reactivate_user(user_id)
                reactivated_users.append(user)
            except NotFoundError:
                continue
        
        return reactivated_users
    
    def bulk_change_user_role(self, user_ids: List[str], new_role: str) -> List[Dict[str, Any]]:
        """Bulk change user roles"""
        if not self.validate_role(new_role):
            raise ValidationError("Invalid role")
        
        updated_users = []
        
        for user_id in user_ids:
            try:
                user = self.change_user_role(user_id, new_role)
                updated_users.append(user)
            except NotFoundError:
                continue
        
        return updated_users
    
    def log_user_activity(self, user_id: str, action: str, ip: str = None, 
                         details: Dict[str, Any] = None) -> None:
        """Log user activity"""
        if user_id not in self.user_activities:
            self.user_activities[user_id] = []
        
        activity = {
            'activity_id': str(uuid4()),
            'user_id': user_id,
            'action': action,
            'ip': ip,
            'details': details or {},
            'timestamp': datetime.now()
        }
        
        self.user_activities[user_id].append(activity)
    
    def get_user_activities(self, user_id: str, action: str = None, 
                           start_date: datetime = None, end_date: datetime = None,
                           limit: int = 50) -> List[Dict[str, Any]]:
        """Get user activities with optional filtering"""
        if user_id not in self.user_activities:
            return []
        
        activities = self.user_activities[user_id]
        
        # Filter by action
        if action:
            activities = [a for a in activities if a['action'] == action]
        
        # Filter by date range
        if start_date:
            activities = [a for a in activities if a['timestamp'] >= start_date]
        
        if end_date:
            activities = [a for a in activities if a['timestamp'] <= end_date]
        
        # Sort by timestamp (newest first)
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply limit
        activities = activities[:limit]
        
        return activities
    
    def check_permission(self, user_id: str, action: str, target_user_id: str = None, 
                        resource: str = None) -> bool:
        """Check if user has permission for action"""
        user = self.users.get(user_id)
        if not user or not user['is_active']:
            return False
        
        # Admin has all permissions
        if user['role'] == 'admin':
            return True
        
        # Role-based permissions
        permissions = {
            'student': {
                'view_profile': ['own'],
                'update_profile': ['own'],
                'view_courses': ['own'],
                'enroll_courses': ['own']
            },
            'teacher': {
                'view_profile': ['own', 'students'],
                'update_profile': ['own'],
                'view_courses': ['own', 'students'],
                'manage_courses': ['own'],
                'view_students': ['own']
            },
            'admin': {
                'view_profile': ['all'],
                'update_profile': ['all'],
                'view_courses': ['all'],
                'manage_courses': ['all'],
                'view_students': ['all'],
                'manage_users': ['all']
            }
        }
        
        user_permissions = permissions.get(user['role'], {})
        action_permissions = user_permissions.get(action, [])
        
        # Check if user has permission for the action
        if 'all' in action_permissions:
            return True
        
        if target_user_id:
            if 'own' in action_permissions and target_user_id == user_id:
                return True
            
            if 'students' in action_permissions:
                # Check if target user is a student managed by this teacher
                target_user = self.users.get(target_user_id)
                if target_user and target_user['role'] == 'student':
                    # In a real system, we'd check course enrollment/teaching assignments
                    return True
        
        return False
    
    def _log_audit_trail(self, user_id: str, action: str, details: Dict[str, Any]) -> None:
        """Log user audit trail"""
        if user_id not in self.audit_trail:
            self.audit_trail[user_id] = []
        
        audit_entry = {
            'audit_id': str(uuid4()),
            'user_id': user_id,
            'action': action,
            'details': details,
            'timestamp': datetime.now(),
            'performed_by': user_id  # In a real system, this would be the admin performing the action
        }
        
        self.audit_trail[user_id].append(audit_entry)
    
    def get_user_audit_trail(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user audit trail"""
        if user_id not in self.audit_trail:
            return []
        
        # Sort by timestamp (newest first)
        audit_trail = sorted(self.audit_trail[user_id], key=lambda x: x['timestamp'], reverse=True)
        
        # Apply limit
        audit_trail = audit_trail[:limit]
        
        return audit_trail
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        total_users = len(self.users)
        active_users = len([u for u in self.users.values() if u['is_active']])
        
        role_counts = {}
        for user in self.users.values():
            role = user['role']
            role_counts[role] = role_counts.get(role, 0) + 1
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'role_distribution': role_counts
        }