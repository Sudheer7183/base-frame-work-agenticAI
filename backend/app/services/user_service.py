# # """User management service"""

# # import logging
# # from typing import Optional, List
# # from datetime import datetime, timedelta
# # from sqlalchemy.orm import Session
# # from sqlalchemy.exc import IntegrityError
# # from passlib.context import CryptContext

# # from app.models.user import User
# # from app.schemas.user import UserCreate, UserUpdate, UserStats
# # from app.core.exceptions import (
# #     NotFoundException,
# #     BadRequestException,
# #     ConflictException
# # )
# # from app.tenancy.context import get_tenant_slug

# # logger = logging.getLogger(__name__)

# # # Password hashing
# # pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# # class UserService:
# #     """Service for user management operations"""
    
# #     def __init__(self, db: Session):
# #         self.db = db
    
# #     def hash_password(self, password: str) -> str:
# #         """Hash a password"""
# #         return pwd_context.hash(password)
    
# #     def verify_password(self, plain_password: str, hashed_password: str) -> bool:
# #         """Verify a password"""
# #         return pwd_context.verify(plain_password, hashed_password)
    
# #     def create_user(
# #         self,
# #         user_data: UserCreate,
# #         tenant_slug: Optional[str] = None
# #     ) -> User:
# #         """
# #         Create a new user in the current tenant
        
# #         Args:
# #             user_data: User creation data
# #             tenant_slug: Tenant slug (auto-detected if not provided)
            
# #         Returns:
# #             Created User object
            
# #         Raises:
# #             ConflictException: If user with email already exists
# #             BadRequestException: If validation fails
# #         """
# #         # Get tenant context
# #         if not tenant_slug:
# #             tenant_slug = get_tenant_slug()
# #             if not tenant_slug:
# #                 raise BadRequestException("No tenant context available")
        
# #         logger.info(f"Creating user {user_data.email} in tenant {tenant_slug}")
        
# #         # Check if user exists
# #         existing = User.get_by_email(self.db, user_data.email)
# #         if existing:
# #             raise ConflictException(f"User with email {user_data.email} already exists")
        
# #         # Hash password if provided
# #         hashed_password = None
# #         if user_data.password:
# #             hashed_password = self.hash_password(user_data.password)
        
# #         # Create user
# #         user = User(
# #             email=user_data.email,
# #             username=user_data.username or user_data.email.split('@')[0],
# #             full_name=user_data.full_name,
# #             phone=user_data.phone,
# #             hashed_password=hashed_password,
# #             roles=user_data.roles,
# #             permissions=user_data.permissions,
# #             tenant_slug=tenant_slug,
# #             is_active=user_data.is_active,
# #             is_verified=user_data.is_verified,
# #             created_at=datetime.utcnow(),
# #             updated_at=datetime.utcnow()
# #         )
        
# #         try:
# #             self.db.add(user)
# #             self.db.commit()
# #             self.db.refresh(user)
            
# #             logger.info(f"User created successfully: {user.id}")
# #             return user
            
# #         except IntegrityError as e:
# #             self.db.rollback()
# #             logger.error(f"Failed to create user: {e}")
# #             raise ConflictException("User creation failed due to duplicate data")
    
# #     def get_user(self, user_id: int) -> User:
# #         """
# #         Get user by ID
        
# #         Raises:
# #             NotFoundException: If user not found
# #         """
# #         user = self.db.query(User).filter(User.id == user_id).first()
# #         if not user:
# #             raise NotFoundException(f"User with ID {user_id} not found")
# #         return user
    
# #     def get_user_by_email(self, email: str) -> Optional[User]:
# #         """Get user by email"""
# #         return User.get_by_email(self.db, email)
    
# #     def list_users(
# #         self,
# #         tenant_slug: Optional[str] = None,
# #         active_only: bool = False,
# #         role: Optional[str] = None,
# #         search: Optional[str] = None,
# #         limit: int = 100,
# #         offset: int = 0
# #     ) -> tuple[List[User], int]:
# #         """
# #         List users with filtering and pagination
        
# #         Returns:
# #             Tuple of (users list, total count)
# #         """
# #         if not tenant_slug:
# #             tenant_slug = get_tenant_slug()
        
# #         query = self.db.query(User).filter(User.tenant_slug == tenant_slug)
        
# #         # Apply filters
# #         if active_only:
# #             query = query.filter(User.is_active == True)
        
# #         if role:
# #             query = query.filter(User.roles.contains([role]))
        
# #         if search:
# #             search_term = f"%{search}%"
# #             query = query.filter(
# #                 (User.email.ilike(search_term)) |
# #                 (User.username.ilike(search_term)) |
# #                 (User.full_name.ilike(search_term))
# #             )
        
# #         # Get total count
# #         total = query.count()
        
# #         # Apply pagination
# #         users = query.offset(offset).limit(limit).all()
        
# #         return users, total
    
# #     def update_user(self, user_id: int, user_data: UserUpdate) -> User:
# #         """
# #         Update user
        
# #         Raises:
# #             NotFoundException: If user not found
# #         """
# #         user = self.get_user(user_id)
        
# #         # Update fields
# #         if user_data.username is not None:
# #             user.username = user_data.username
# #         if user_data.full_name is not None:
# #             user.full_name = user_data.full_name
# #         if user_data.phone is not None:
# #             user.phone = user_data.phone
# #         if user_data.avatar_url is not None:
# #             user.avatar_url = user_data.avatar_url
# #         if user_data.roles is not None:
# #             user.roles = user_data.roles
# #         if user_data.permissions is not None:
# #             user.permissions = user_data.permissions
# #         if user_data.is_active is not None:
# #             user.is_active = user_data.is_active
# #         if user_data.is_verified is not None:
# #             user.is_verified = user_data.is_verified
# #         if user_data.preferences is not None:
# #             user.preferences = user_data.preferences
        
# #         user.updated_at = datetime.utcnow()
        
# #         self.db.commit()
# #         self.db.refresh(user)
        
# #         logger.info(f"User {user_id} updated successfully")
# #         return user
    
# #     def delete_user(self, user_id: int) -> None:
# #         """
# #         Delete user
        
# #         Raises:
# #             NotFoundException: If user not found
# #         """
# #         user = self.get_user(user_id)
        
# #         self.db.delete(user)
# #         self.db.commit()
        
# #         logger.info(f"User {user_id} deleted successfully")
    
# #     def change_password(
# #         self,
# #         user_id: int,
# #         current_password: str,
# #         new_password: str
# #     ) -> User:
# #         """
# #         Change user password
        
# #         Raises:
# #             NotFoundException: If user not found
# #             BadRequestException: If current password is incorrect
# #         """
# #         user = self.get_user(user_id)
        
# #         if not user.hashed_password:
# #             raise BadRequestException("User does not have a password set")
        
# #         # Verify current password
# #         if not self.verify_password(current_password, user.hashed_password):
# #             raise BadRequestException("Current password is incorrect")
        
# #         # Set new password
# #         user.hashed_password = self.hash_password(new_password)
# #         user.updated_at = datetime.utcnow()
        
# #         self.db.commit()
# #         self.db.refresh(user)
        
# #         logger.info(f"Password changed for user {user_id}")
# #         return user
    
# #     def update_last_login(self, user_id: int) -> None:
# #         """Update user's last login timestamp"""
# #         user = self.get_user(user_id)
# #         user.last_login = datetime.utcnow()
# #         self.db.commit()
    
# #     def get_user_stats(self, tenant_slug: Optional[str] = None) -> UserStats:
# #         """Get user statistics for a tenant"""
# #         if not tenant_slug:
# #             tenant_slug = get_tenant_slug()
        
# #         query = self.db.query(User).filter(User.tenant_slug == tenant_slug)
        
# #         total_users = query.count()
# #         active_users = query.filter(User.is_active == True).count()
# #         verified_users = query.filter(User.is_verified == True).count()
        
# #         # Users by role
# #         users_by_role = {}
# #         all_users = query.all()
# #         for user in all_users:
# #             for role in (user.roles or []):
# #                 users_by_role[role] = users_by_role.get(role, 0) + 1
        
# #         # Recent activity
# #         week_ago = datetime.utcnow() - timedelta(days=7)
# #         recent_signups = query.filter(User.created_at >= week_ago).count()
# #         recent_logins = query.filter(User.last_login >= week_ago).count()
        
# #         return UserStats(
# #             total_users=total_users,
# #             active_users=active_users,
# #             verified_users=verified_users,
# #             users_by_role=users_by_role,
# #             recent_signups=recent_signups,
# #             recent_logins=recent_logins
# #         )


# """User management service"""

# import logging
# import bcrypt
# from typing import Optional, List
# from datetime import datetime, timedelta
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError

# from app.models.user import User
# from app.schemas.user import UserCreate, UserUpdate, UserStats
# from app.core.exceptions import (
#     NotFoundException,
#     BadRequestException,
#     ConflictException
# )
# from app.tenancy.context import get_tenant_slug

# logger = logging.getLogger(__name__)


# class UserService:
#     """Service for user management operations"""
    
#     def __init__(self, db: Session):
#         self.db = db
    
#     def hash_password(self, password: str) -> str:
#         """Hash a password using bcrypt"""
#         # Truncate password to 72 bytes if needed (bcrypt limitation)
#         password_bytes = password.encode('utf-8')
#         if len(password_bytes) > 72:
#             logger.warning("Password exceeds 72 bytes, truncating for bcrypt")
#             password_bytes = password_bytes[:72]
        
#         # Generate salt and hash
#         salt = bcrypt.gensalt(rounds=12)
#         hashed = bcrypt.hashpw(password_bytes, salt)
        
#         # Return as string
#         return hashed.decode('utf-8')
    
#     def verify_password(self, plain_password: str, hashed_password: str) -> bool:
#         """Verify a password against its hash"""
#         # Truncate password to 72 bytes if needed (bcrypt limitation)
#         password_bytes = plain_password.encode('utf-8')
#         if len(password_bytes) > 72:
#             password_bytes = password_bytes[:72]
        
#         # Convert hash string to bytes if needed
#         if isinstance(hashed_password, str):
#             hashed_password = hashed_password.encode('utf-8')
        
#         return bcrypt.checkpw(password_bytes, hashed_password)
    
#     def create_user(
#         self,
#         user_data: UserCreate,
#         tenant_slug: Optional[str] = None
#     ) -> User:
#         """
#         Create a new user in the current tenant
        
#         Args:
#             user_data: User creation data
#             tenant_slug: Tenant slug (auto-detected if not provided)
            
#         Returns:
#             Created User object
            
#         Raises:
#             ConflictException: If user with email already exists
#             BadRequestException: If validation fails
#         """
#         # Get tenant context
#         if not tenant_slug:
#             tenant_slug = get_tenant_slug()
#             if not tenant_slug:
#                 raise BadRequestException("No tenant context available")
        
#         logger.info(f"Creating user {user_data.email} in tenant {tenant_slug}")
        
#         # Check if user exists
#         existing = User.get_by_email(self.db, user_data.email)
#         if existing:
#             raise ConflictException(f"User with email {user_data.email} already exists")
        
#         # Hash password if provided
#         hashed_password = None
#         if user_data.password:
#             hashed_password = self.hash_password(user_data.password)
        
#         # Create user
#         user = User(
#             email=user_data.email,
#             username=user_data.username or user_data.email.split('@')[0],
#             full_name=user_data.full_name,
#             phone=user_data.phone,
#             hashed_password=hashed_password,
#             roles=user_data.roles,
#             permissions=user_data.permissions,
#             tenant_slug=tenant_slug,
#             is_active=user_data.is_active,
#             is_verified=user_data.is_verified,
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow()
#         )
        
#         try:
#             self.db.add(user)
#             self.db.commit()
#             self.db.refresh(user)
            
#             logger.info(f"User created successfully: {user.id}")
#             return user
            
#         except IntegrityError as e:
#             self.db.rollback()
#             logger.error(f"Failed to create user: {e}")
#             raise ConflictException("User creation failed due to duplicate data")
    
#     def get_user(self, user_id: int) -> User:
#         """
#         Get user by ID
        
#         Raises:
#             NotFoundException: If user not found
#         """
#         user = self.db.query(User).filter(User.id == user_id).first()
#         if not user:
#             raise NotFoundException(f"User with ID {user_id} not found")
#         return user
    
#     def get_user_by_email(self, email: str) -> Optional[User]:
#         """Get user by email"""
#         return User.get_by_email(self.db, email)
    
#     def list_users(
#         self,
#         tenant_slug: Optional[str] = None,
#         active_only: bool = False,
#         role: Optional[str] = None,
#         search: Optional[str] = None,
#         limit: int = 100,
#         offset: int = 0
#     ) -> tuple[List[User], int]:
#         """
#         List users with filtering and pagination
        
#         Returns:
#             Tuple of (users list, total count)
#         """
#         if not tenant_slug:
#             tenant_slug = get_tenant_slug()
        
#         query = self.db.query(User).filter(User.tenant_slug == tenant_slug)
        
#         # Apply filters
#         if active_only:
#             query = query.filter(User.is_active == True)
        
#         if role:
#             query = query.filter(User.roles.contains([role]))
        
#         if search:
#             search_term = f"%{search}%"
#             query = query.filter(
#                 (User.email.ilike(search_term)) |
#                 (User.username.ilike(search_term)) |
#                 (User.full_name.ilike(search_term))
#             )
        
#         # Get total count
#         total = query.count()
        
#         # Apply pagination
#         users = query.offset(offset).limit(limit).all()
        
#         return users, total
    
#     def update_user(self, user_id: int, user_data: UserUpdate) -> User:
#         """
#         Update user
        
#         Raises:
#             NotFoundException: If user not found
#         """
#         user = self.get_user(user_id)
        
#         # Update fields
#         if user_data.username is not None:
#             user.username = user_data.username
#         if user_data.full_name is not None:
#             user.full_name = user_data.full_name
#         if user_data.phone is not None:
#             user.phone = user_data.phone
#         if user_data.avatar_url is not None:
#             user.avatar_url = user_data.avatar_url
#         if user_data.roles is not None:
#             user.roles = user_data.roles
#         if user_data.permissions is not None:
#             user.permissions = user_data.permissions
#         if user_data.is_active is not None:
#             user.is_active = user_data.is_active
#         if user_data.is_verified is not None:
#             user.is_verified = user_data.is_verified
#         if user_data.preferences is not None:
#             user.preferences = user_data.preferences
        
#         user.updated_at = datetime.utcnow()
        
#         self.db.commit()
#         self.db.refresh(user)
        
#         logger.info(f"User {user_id} updated successfully")
#         return user
    
#     def delete_user(self, user_id: int) -> None:
#         """
#         Delete user
        
#         Raises:
#             NotFoundException: If user not found
#         """
#         user = self.get_user(user_id)
        
#         self.db.delete(user)
#         self.db.commit()
        
#         logger.info(f"User {user_id} deleted successfully")
    
#     def change_password(
#         self,
#         user_id: int,
#         current_password: str,
#         new_password: str
#     ) -> User:
#         """
#         Change user password
        
#         Raises:
#             NotFoundException: If user not found
#             BadRequestException: If current password is incorrect
#         """
#         user = self.get_user(user_id)
        
#         if not user.hashed_password:
#             raise BadRequestException("User does not have a password set")
        
#         # Verify current password
#         if not self.verify_password(current_password, user.hashed_password):
#             raise BadRequestException("Current password is incorrect")
        
#         # Set new password
#         user.hashed_password = self.hash_password(new_password)
#         user.updated_at = datetime.utcnow()
        
#         self.db.commit()
#         self.db.refresh(user)
        
#         logger.info(f"Password changed for user {user_id}")
#         return user
    
#     def update_last_login(self, user_id: int) -> None:
#         """Update user's last login timestamp"""
#         user = self.get_user(user_id)
#         user.last_login = datetime.utcnow()
#         self.db.commit()
    
#     def get_user_stats(self, tenant_slug: Optional[str] = None) -> UserStats:
#         """Get user statistics for a tenant"""
#         if not tenant_slug:
#             tenant_slug = get_tenant_slug()
        
#         query = self.db.query(User).filter(User.tenant_slug == tenant_slug)
        
#         total_users = query.count()
#         active_users = query.filter(User.is_active == True).count()
#         verified_users = query.filter(User.is_verified == True).count()
        
#         # Users by role
#         users_by_role = {}
#         all_users = query.all()
#         for user in all_users:
#             for role in (user.roles or []):
#                 users_by_role[role] = users_by_role.get(role, 0) + 1
        
#         # Recent activity
#         week_ago = datetime.utcnow() - timedelta(days=7)
#         recent_signups = query.filter(User.created_at >= week_ago).count()
#         recent_logins = query.filter(User.last_login >= week_ago).count()
        
#         return UserStats(
#             total_users=total_users,
#             active_users=active_users,
#             verified_users=verified_users,
#             users_by_role=users_by_role,
#             recent_signups=recent_signups,
#             recent_logins=recent_logins
#         )

# """User management service"""

# import logging
# import bcrypt
# from typing import Optional, List
# from datetime import datetime, timedelta
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError
# from sqlalchemy import text

# from app.models.user import User
# from app.schemas.user import UserCreate, UserUpdate, UserStats
# from app.core.exceptions import (
#     NotFoundException,
#     BadRequestException,
#     ConflictException
# )
# from app.tenancy.context import get_tenant_slug

# logger = logging.getLogger(__name__)


# class UserService:
#     """Service for user management operations"""
    
#     def __init__(self, db: Session):
#         self.db = db
    
#     def _ensure_schema_context(self, tenant_slug: str):
#         """Ensure the correct schema search path is set"""
#         schema_name = f"tenant_{tenant_slug}"
#         self.db.execute(text(f"SET search_path TO {schema_name}, public"))
#         logger.debug(f"Set search_path to {schema_name}")
    
#     def hash_password(self, password: str) -> str:
#         """Hash a password using bcrypt"""
#         # Truncate password to 72 bytes if needed (bcrypt limitation)
#         password_bytes = password.encode('utf-8')
#         if len(password_bytes) > 72:
#             logger.warning("Password exceeds 72 bytes, truncating for bcrypt")
#             password_bytes = password_bytes[:72]
        
#         # Generate salt and hash
#         salt = bcrypt.gensalt(rounds=12)
#         hashed = bcrypt.hashpw(password_bytes, salt)
        
#         # Return as string
#         return hashed.decode('utf-8')
    
#     def verify_password(self, plain_password: str, hashed_password: str) -> bool:
#         """Verify a password against its hash"""
#         # Truncate password to 72 bytes if needed (bcrypt limitation)
#         password_bytes = plain_password.encode('utf-8')
#         if len(password_bytes) > 72:
#             password_bytes = password_bytes[:72]
        
#         # Convert hash string to bytes if needed
#         if isinstance(hashed_password, str):
#             hashed_password = hashed_password.encode('utf-8')
        
#         return bcrypt.checkpw(password_bytes, hashed_password)
    
#     def create_user(
#         self,
#         user_data: UserCreate,
#         tenant_slug: Optional[str] = None
#     ) -> User:
#         """
#         Create a new user in the current tenant
        
#         Args:
#             user_data: User creation data
#             tenant_slug: Tenant slug (auto-detected if not provided)
            
#         Returns:
#             Created User object
            
#         Raises:
#             ConflictException: If user with email already exists
#             BadRequestException: If validation fails
#         """
#         # Get tenant context
#         if not tenant_slug:
#             tenant_slug = get_tenant_slug()
#             if not tenant_slug:
#                 raise BadRequestException("No tenant context available")
        
#         logger.info(f"Creating user {user_data.email} in tenant {tenant_slug}")
        
#         # Ensure schema context before operations
#         self._ensure_schema_context(tenant_slug)
        
#         # Check if user exists
#         existing = User.get_by_email(self.db, user_data.email)
#         if existing:
#             raise ConflictException(f"User with email {user_data.email} already exists")
        
#         # Hash password if provided
#         hashed_password = None
#         if user_data.password:
#             hashed_password = self.hash_password(user_data.password)
        
#         # Create user
#         user = User(
#             email=user_data.email,
#             username=user_data.username or user_data.email.split('@')[0],
#             full_name=user_data.full_name,
#             phone=user_data.phone,
#             hashed_password=hashed_password,
#             roles=user_data.roles,
#             permissions=user_data.permissions,
#             tenant_slug=tenant_slug,
#             is_active=user_data.is_active,
#             is_verified=user_data.is_verified,
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow()
#         )
        
#         try:
#             self.db.add(user)
#             self.db.commit()
            
#             # Re-establish schema context after commit
#             self._ensure_schema_context(tenant_slug)
            
#             # Query the user back with explicit schema context
#             user = self.db.query(User).filter(User.id == user.id).first()
            
#             if not user:
#                 raise BadRequestException(f"User created but could not be retrieved from tenant schema")
            
#             logger.info(f"User created successfully: {user.id}")
#             return user
            
#         except IntegrityError as e:
#             self.db.rollback()
#             logger.error(f"Failed to create user: {e}")
#             raise ConflictException("User creation failed due to duplicate data")
    
#     def get_user(self, user_id: int) -> User:
#         """
#         Get user by ID
        
#         Raises:
#             NotFoundException: If user not found
#         """
#         user = self.db.query(User).filter(User.id == user_id).first()
#         if not user:
#             raise NotFoundException(f"User with ID {user_id} not found")
#         return user
    
#     def get_user_by_email(self, email: str) -> Optional[User]:
#         """Get user by email"""
#         return User.get_by_email(self.db, email)
    
#     def list_users(
#         self,
#         tenant_slug: Optional[str] = None,
#         active_only: bool = False,
#         role: Optional[str] = None,
#         search: Optional[str] = None,
#         limit: int = 100,
#         offset: int = 0
#     ) -> tuple[List[User], int]:
#         """
#         List users with filtering and pagination
        
#         Returns:
#             Tuple of (users list, total count)
#         """
#         if not tenant_slug:
#             tenant_slug = get_tenant_slug()
        
#         query = self.db.query(User).filter(User.tenant_slug == tenant_slug)
        
#         # Apply filters
#         if active_only:
#             query = query.filter(User.is_active == True)
        
#         if role:
#             query = query.filter(User.roles.contains([role]))
        
#         if search:
#             search_term = f"%{search}%"
#             query = query.filter(
#                 (User.email.ilike(search_term)) |
#                 (User.username.ilike(search_term)) |
#                 (User.full_name.ilike(search_term))
#             )
        
#         # Get total count
#         total = query.count()
        
#         # Apply pagination
#         users = query.offset(offset).limit(limit).all()
        
#         return users, total
    
#     def update_user(self, user_id: int, user_data: UserUpdate) -> User:
#         """
#         Update user
        
#         Raises:
#             NotFoundException: If user not found
#         """
#         user = self.get_user(user_id)
#         tenant_slug = user.tenant_slug
        
#         # Update fields
#         if user_data.username is not None:
#             user.username = user_data.username
#         if user_data.full_name is not None:
#             user.full_name = user_data.full_name
#         if user_data.phone is not None:
#             user.phone = user_data.phone
#         if user_data.avatar_url is not None:
#             user.avatar_url = user_data.avatar_url
#         if user_data.roles is not None:
#             user.roles = user_data.roles
#         if user_data.permissions is not None:
#             user.permissions = user_data.permissions
#         if user_data.is_active is not None:
#             user.is_active = user_data.is_active
#         if user_data.is_verified is not None:
#             user.is_verified = user_data.is_verified
#         if user_data.preferences is not None:
#             user.preferences = user_data.preferences
        
#         user.updated_at = datetime.utcnow()
        
#         self.db.commit()
        
#         # Re-establish schema context after commit
#         self._ensure_schema_context(tenant_slug)
        
#         # Query back instead of refresh
#         user = self.db.query(User).filter(User.id == user_id).first()
        
#         logger.info(f"User {user_id} updated successfully")
#         return user
    
#     def delete_user(self, user_id: int) -> None:
#         """
#         Delete user
        
#         Raises:
#             NotFoundException: If user not found
#         """
#         user = self.get_user(user_id)
        
#         self.db.delete(user)
#         self.db.commit()
        
#         logger.info(f"User {user_id} deleted successfully")
    
#     def change_password(
#         self,
#         user_id: int,
#         current_password: str,
#         new_password: str
#     ) -> User:
#         """
#         Change user password
        
#         Raises:
#             NotFoundException: If user not found
#             BadRequestException: If current password is incorrect
#         """
#         user = self.get_user(user_id)
#         tenant_slug = user.tenant_slug
        
#         if not user.hashed_password:
#             raise BadRequestException("User does not have a password set")
        
#         # Verify current password
#         if not self.verify_password(current_password, user.hashed_password):
#             raise BadRequestException("Current password is incorrect")
        
#         # Set new password
#         user.hashed_password = self.hash_password(new_password)
#         user.updated_at = datetime.utcnow()
        
#         self.db.commit()
        
#         # Re-establish schema context after commit
#         self._ensure_schema_context(tenant_slug)
        
#         # Query back instead of refresh
#         user = self.db.query(User).filter(User.id == user_id).first()
        
#         logger.info(f"Password changed for user {user_id}")
#         return user
    
#     def update_last_login(self, user_id: int) -> None:
#         """Update user's last login timestamp"""
#         user = self.get_user(user_id)
#         user.last_login = datetime.utcnow()
#         self.db.commit()
    
#     def get_user_stats(self, tenant_slug: Optional[str] = None) -> UserStats:
#         """Get user statistics for a tenant"""
#         if not tenant_slug:
#             tenant_slug = get_tenant_slug()
        
#         query = self.db.query(User).filter(User.tenant_slug == tenant_slug)
        
#         total_users = query.count()
#         active_users = query.filter(User.is_active == True).count()
#         verified_users = query.filter(User.is_verified == True).count()
        
#         # Users by role
#         users_by_role = {}
#         all_users = query.all()
#         for user in all_users:
#             for role in (user.roles or []):
#                 users_by_role[role] = users_by_role.get(role, 0) + 1
        
#         # Recent activity
#         week_ago = datetime.utcnow() - timedelta(days=7)
#         recent_signups = query.filter(User.created_at >= week_ago).count()
#         recent_logins = query.filter(User.last_login >= week_ago).count()
        
#         return UserStats(
#             total_users=total_users,
#             active_users=active_users,
#             verified_users=verified_users,
#             users_by_role=users_by_role,
#             recent_signups=recent_signups,
#             recent_logins=recent_logins
#         )

"""
Enhanced User Service with SSO Invitation Support

File: backend/app/services/user_service.py
Purpose: User management with email invitation workflow
"""

import logging
import secrets
import bcrypt
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text, or_

from app.models.user import User
from app.schemas.user import (
    UserCreate, UserUpdate, UserStats, UserInvite,
    UserInviteResponse, InvitationAcceptRequest
)
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException
)
from app.tenancy.context import get_tenant_slug
from app.services.email_service import get_email_service
from app.core.audit import AuditLogger, AuditAction
from app.tenancy.models import Tenant, TenantStatus
logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations with SSO invitation support"""
    
    # Invitation configuration
    INVITATION_EXPIRY_DAYS = 7
    INVITATION_TOKEN_BYTES = 32
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = get_email_service()
        self.audit_logger = AuditLogger(db)
    
    # ========================================================================
    # PASSWORD HASHING (Existing)
    # ========================================================================
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def _ensure_schema_context(self, tenant_slug: str):
        """Ensure database session is in correct schema context"""
        try:
            from app.tenancy.models import Tenant
            tenant = Tenant.get_by_slug(self.db, tenant_slug)
            if tenant:
                self.db.execute(text(f'SET search_path TO "{tenant.schema_name}", public'))
        except Exception as e:
            logger.warning(f"Could not set schema context: {e}")
    
    # ========================================================================
    # USER INVITATION METHODS (NEW)
    # ========================================================================
    
    def create_invitation(
        self,
        invitation_data: UserInvite,
        tenant_slug: str,
        invited_by_user_id: int,
        invited_by_email: str,
        tenant_name: str
    ) -> User:
        """
        Create a user invitation for SSO
        
        This creates a 'pending' user record that will be activated when
        they accept the invitation and login via SSO.
        
        Args:
            invitation_data: Invitation data (email, roles, etc.)
            tenant_slug: Tenant slug
            invited_by_user_id: ID of user sending invitation
            invited_by_email: Email of user sending invitation
            tenant_name: Name of tenant for email
            
        Returns:
            Created user with pending status
            
        Raises:
            ConflictException: If user already exists
            BadRequestException: If validation fails
        """
        logger.info(f"Creating invitation for {invitation_data.email} in tenant {tenant_slug}")
        
        # Ensure we're in correct schema
        self._ensure_schema_context(tenant_slug)
        
        # Check if user already exists
        existing = User.get_by_email(self.db, invitation_data.email)
        if existing:
            if existing.invitation_status == 'accepted':
                raise ConflictException(
                    f"User {invitation_data.email} already exists and is active"
                )
            elif existing.invitation_status == 'pending':
                # Resend invitation
                logger.info(f"User {invitation_data.email} has pending invitation, resending")
                return self.resend_invitation(existing.id, tenant_name, invited_by_email)
            elif existing.invitation_status in ['expired', 'cancelled']:
                # Recreate invitation
                logger.info(f"Recreating invitation for {invitation_data.email}")
                return self._recreate_invitation(
                    existing, 
                    invitation_data,
                    invited_by_user_id,
                    invited_by_email,
                    tenant_name
                )
        
        # Generate secure invitation token
        invitation_token = secrets.token_urlsafe(self.INVITATION_TOKEN_BYTES)
        
        # Calculate expiry
        invited_at = datetime.utcnow()
        expires_at = invited_at + timedelta(days=self.INVITATION_EXPIRY_DAYS)
        
        # Create pending user
        user = User(
            email=invitation_data.email,
            username=invitation_data.email.split('@')[0],  # Temporary, will be updated from SSO
            full_name=invitation_data.full_name,
            roles=invitation_data.roles,
            tenant_slug=tenant_slug,
            
            # Invitation fields
            invitation_status='pending',
            invitation_token=invitation_token,
            invited_by=invited_by_user_id,
            invited_at=invited_at,
            invitation_expires_at=expires_at,
            provisioning_method='invitation',
            
            # Not active until invitation accepted
            is_active=False,
            is_verified=False,
            
            # No password - SSO only
            hashed_password=None,
            keycloak_id=None,  # Will be set when they login
            
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Pending user created: {user.id} for {user.email}")
            
            # Send invitation email
            if invitation_data.send_email:
                self._send_invitation_email(
                    user=user,
                    tenant_name=tenant_name,
                    invited_by_email=invited_by_email,
                    custom_message=invitation_data.custom_message
                )
            
            # Audit log
            self.audit_logger.log(
                action=AuditAction.USER_CREATED,
                resource_type="user",
                resource_id=str(user.id),
                details={
                    "email": user.email,
                    "invitation_status": "pending",
                    "invited_by": invited_by_user_id
                },
                user_id=invited_by_user_id
            )
            
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create invitation: {e}")
            raise ConflictException("Invitation creation failed due to duplicate data")
    
    def _recreate_invitation(
        self,
        existing_user: User,
        invitation_data: UserInvite,
        invited_by_user_id: int,
        invited_by_email: str,
        tenant_name: str
    ) -> User:
        """Recreate an invitation for expired/cancelled user"""
        
        # Generate new token
        existing_user.invitation_token = secrets.token_urlsafe(self.INVITATION_TOKEN_BYTES)
        existing_user.invitation_status = 'pending'
        existing_user.invited_at = datetime.utcnow()
        existing_user.invitation_expires_at = datetime.utcnow() + timedelta(days=self.INVITATION_EXPIRY_DAYS)
        existing_user.invited_by = invited_by_user_id
        
        # Update roles if changed
        existing_user.roles = invitation_data.roles
        existing_user.full_name = invitation_data.full_name or existing_user.full_name
        
        existing_user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(existing_user)
        
        # Send email
        if invitation_data.send_email:
            self._send_invitation_email(
                user=existing_user,
                tenant_name=tenant_name,
                invited_by_email=invited_by_email,
                custom_message=invitation_data.custom_message
            )
        
        logger.info(f"Invitation recreated for user {existing_user.id}")
        return existing_user
    
    def _send_invitation_email(
        self,
        user: User,
        tenant_name: str,
        invited_by_email: str,
        custom_message: Optional[str] = None
    ):
        """Send invitation email to user"""
        try:
            # Get inviter details
            inviter = None
            inviter_name = "Someone"
            
            if user.invited_by:
                inviter = User.get_by_id(self.db, user.invited_by)
                if inviter:
                    inviter_name = inviter.full_name or inviter.email
            
            # Send email via email service
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create task if loop running
                asyncio.create_task(
                    self.email_service.send_invitation_email(
                        recipient_email=user.email,
                        invitation_token=user.invitation_token,
                        tenant_name=tenant_name,
                        invited_by_name=inviter_name,
                        invited_by_email=invited_by_email,
                        recipient_name=user.full_name,
                        roles=user.roles,
                        custom_message=custom_message,
                        expires_at=user.invitation_expires_at
                    )
                )
            else:
                # Run until complete if loop not running
                loop.run_until_complete(
                    self.email_service.send_invitation_email(
                        recipient_email=user.email,
                        invitation_token=user.invitation_token,
                        tenant_name=tenant_name,
                        invited_by_name=inviter_name,
                        invited_by_email=invited_by_email,
                        recipient_name=user.full_name,
                        roles=user.roles,
                        custom_message=custom_message,
                        expires_at=user.invitation_expires_at
                    )
                )
            
            logger.info(f"Invitation email sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send invitation email: {e}", exc_info=True)
            # Don't fail the invitation creation if email fails
    
    def resend_invitation(
        self,
        user_id: int,
        tenant_name: str,
        invited_by_email: str
    ) -> User:
        """
        Resend invitation email to pending user
        
        Args:
            user_id: User ID
            tenant_name: Tenant name for email
            invited_by_email: Email of person resending
            
        Returns:
            Updated user
            
        Raises:
            NotFoundException: If user not found
            BadRequestException: If user not in pending state
        """
        user = User.get_by_id(self.db, user_id)
        
        if not user:
            raise NotFoundException(f"User {user_id} not found")
        
        if user.invitation_status != 'pending':
            raise BadRequestException(
                f"Cannot resend invitation - user status is {user.invitation_status}"
            )
        
        # Check if invitation expired
        if user.invitation_expires_at and datetime.utcnow() > user.invitation_expires_at:
            # Extend expiry
            user.invitation_expires_at = datetime.utcnow() + timedelta(days=self.INVITATION_EXPIRY_DAYS)
            user.invitation_status = 'pending'  # Reset from expired
        
        # Regenerate token for security
        user.invitation_token = secrets.token_urlsafe(self.INVITATION_TOKEN_BYTES)
        user.invited_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        # Resend email
        self._send_invitation_email(
            user=user,
            tenant_name=tenant_name,
            invited_by_email=invited_by_email
        )
        
        logger.info(f"Invitation resent to {user.email}")
        return user
    """
    Enhanced User Service with SSO Invitation Support - Part 2

    File: backend/app/services/user_service.py (continued)
    """

    # ========================================================================
    # INVITATION ACCEPTANCE (NEW)
    # ========================================================================
    
    # def accept_invitation(self,invitation_token: str,keycloak_id: str,sso_data: Dict[str, Any]) -> User:
    #     """
    #     Accept invitation when user logs in via SSO
        
    #     This activates the pending user account and links it to SSO
        
    #     Args:
    #         invitation_token: Invitation token from email
    #         keycloak_id: Keycloak user ID from SSO login
    #         sso_data: Additional data from SSO (email, name, etc.)
            
    #     Returns:
    #         Activated user
            
    #     Raises:
    #         NotFoundException: If invitation not found
    #         BadRequestException: If invitation expired or invalid
    #     """
    #     logger.info(f"Accepting invitation with token: {invitation_token[:10]}...")
        
    #     # Find user by invitation token
    #     user = User.get_by_invitation_token(self.db, invitation_token)
        
    #     if not user:
    #         raise NotFoundException("Invalid or expired invitation token")
        
    #     # Check invitation status
    #     if user.invitation_status != 'pending':
    #         raise BadRequestException(
    #             f"Invitation already {user.invitation_status}"
    #         )
        
    #     # Check expiry
    #     if user.invitation_expires_at and datetime.utcnow() > user.invitation_expires_at:
    #         user.invitation_status = 'expired'
    #         self.db.commit()
    #         raise BadRequestException("Invitation has expired. Please request a new invitation.")
        
    #     # Ensure schema context
    #     self._ensure_schema_context(user.tenant_slug)
        
    #     # Activate user and link to SSO
    #     user.keycloak_id = keycloak_id
    #     user.username = sso_data.get('preferred_username', user.email)
    #     user.full_name = sso_data.get('name') or user.full_name
    #     user.invitation_status = 'accepted'
    #     user.accepted_at = datetime.utcnow()
    #     user.is_active = True
    #     user.is_verified = True
    #     user.last_login = datetime.utcnow()
    #     user.updated_at = datetime.utcnow()
        
    #     # Clear sensitive invitation data
    #     user.invitation_token = None
        
    #     self.db.commit()
    #     self.db.refresh(user)
        
    #     logger.info(f"Invitation accepted for user {user.id} ({user.email})")
        
    #     # Audit log
    #     self.audit_logger.log(
    #         action="user.invitation.accepted",
    #         resource_type="user",
    #         resource_id=str(user.id),
    #         details={
    #             "email": user.email,
    #             "keycloak_id": keycloak_id,
    #             "sso_provider": sso_data.get('idp_hint', 'keycloak')
    #         },
    #         user_id=user.id
    #     )
        
    #     return user
    

    def find_invitation_across_tenants(
        self,
        invitation_token: str
    ) -> tuple[User, str] | None:
        """
        Search for invitation token across ALL tenant schemas
        
        Returns:
            Tuple of (User, tenant_schema_name) or None if not found
        """
        from sqlalchemy import text
        
        # Get all active tenants
        tenants = self.db.query(Tenant).filter(
            Tenant.status == TenantStatus.ACTIVE.value
        ).all()
        
        logger.info(f"Searching for invitation token across {len(tenants)} tenants")
        
        for tenant in tenants:
            try:
                # Set search path to this tenant's schema
                self.db.execute(text(f'SET search_path TO "{tenant.schema_name}", public'))
                
                # Try to find user with this invitation token
                user = self.db.query(User).filter(
                    User.invitation_token == invitation_token,
                    User.invitation_status == 'pending'
                ).first()
                
                if user:
                    logger.info(
                        f"Found invitation in tenant '{tenant.slug}' "
                        f"(schema: {tenant.schema_name}) for email: {user.email}"
                    )
                    return (user, tenant.schema_name)
                    
            except Exception as e:
                logger.warning(f"Error searching tenant {tenant.slug}: {e}")
                continue
        
        logger.warning(f"Invitation token not found in any tenant")
        return None
    
    def accept_invitation(
        self,
        invitation_token: str,
        keycloak_id: str,
        sso_data: Dict[str, Any]
    ) -> User:
        """
        Accept invitation when user logs in via SSO
        NOW searches across all tenants to find the invitation
        """
        logger.info(f"Accepting invitation with token: {invitation_token[:10]}...")
        
        # Search across all tenant schemas for this invitation
        result = self.find_invitation_across_tenants(invitation_token)
        
        if not result:
            raise NotFoundException(
                "Invalid or expired invitation token. "
                "Please request a new invitation from your administrator."
            )
        
        user, tenant_schema = result
        
        # Ensure we're in the correct tenant schema
        self.db.execute(text(f'SET search_path TO "{tenant_schema}", public'))
        
        # Check invitation hasn't expired
        if user.invitation_expires_at and datetime.utcnow() > user.invitation_expires_at:
            user.invitation_status = 'expired'
            self.db.commit()
            raise BadRequestException(
                f"Invitation has expired. Please request a new invitation from "
                f"your administrator at {user.tenant_slug}."
            )
        
        # Activate user and link to SSO
        user.keycloak_id = keycloak_id
        user.username = sso_data.get('preferred_username', user.email)
        user.full_name = sso_data.get('name') or user.full_name
        user.invitation_status = 'accepted'
        user.accepted_at = datetime.utcnow()
        user.is_active = True
        user.is_verified = True
        user.last_login = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
        # Clear sensitive invitation data
        user.invitation_token = None
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(
            f"✓ Invitation accepted for user {user.id} ({user.email}) "
            f"in tenant '{user.tenant_slug}'"
        )
        
        # Audit log
        self.audit_logger.log(
            action="user.invitation.accepted",
            resource_type="user",
            resource_id=str(user.id),
            details={
                "email": user.email,
                "tenant": user.tenant_slug,
                "keycloak_id": keycloak_id,
                "sso_provider": sso_data.get('idp_hint', 'keycloak')
            },
            user_id=user.id
        )
        
        return user

    def cancel_invitation(self, user_id: int, cancelled_by_user_id: int) -> User:
        """
        Cancel a pending invitation
        
        Args:
            user_id: User ID
            cancelled_by_user_id: ID of user cancelling
            
        Returns:
            Updated user
        """
        user = User.get_by_id(self.db, user_id)
        
        if not user:
            raise NotFoundException(f"User {user_id} not found")
        
        if user.invitation_status != 'pending':
            raise BadRequestException(
                f"Cannot cancel - invitation status is {user.invitation_status}"
            )
        
        user.invitation_status = 'cancelled'
        user.invitation_token = None
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Invitation cancelled for user {user.id} by user {cancelled_by_user_id}")
        
        # Audit log
        self.audit_logger.log(
            action="user.invitation.cancelled",
            resource_type="user",
            resource_id=str(user.id),
            details={"email": user.email},
            user_id=cancelled_by_user_id
        )
        
        return user
    
    def get_pending_invitation_by_email(self, email: str) -> Optional[User]:
        """
        Get pending invitation by email
        
        Used to match SSO login to invitation even without token
        """
        return self.db.query(User).filter(
            User.email == email,
            User.invitation_status == 'pending'
        ).first()
    
    # ========================================================================
    # EXISTING USER CRUD METHODS (Updated)
    # ========================================================================
    
    def create_user(
        self,
        user_data: UserCreate,
        tenant_slug: Optional[str] = None
    ) -> User:
        """
        Create a new user (manual creation, not invitation)
        
        Args:
            user_data: User creation data
            tenant_slug: Tenant slug
            
        Returns:
            Created user
        """
        if not tenant_slug:
            tenant_slug = get_tenant_slug()
            if not tenant_slug:
                raise BadRequestException("No tenant context available")
        
        logger.info(f"Creating user {user_data.email} in tenant {tenant_slug}")
        
        # Ensure schema context
        self._ensure_schema_context(tenant_slug)
        
        # Check if user exists
        existing = User.get_by_email(self.db, user_data.email)
        if existing:
            raise ConflictException(f"User with email {user_data.email} already exists")
        
        # Hash password if provided
        hashed_password = None
        if user_data.password:
            hashed_password = self.hash_password(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username or user_data.email.split('@')[0],
            full_name=user_data.full_name,
            phone=user_data.phone,
            hashed_password=hashed_password,
            roles=user_data.roles,
            permissions=user_data.permissions,
            tenant_slug=tenant_slug,
            is_active=user_data.is_active,
            is_verified=user_data.is_verified,
            invitation_status='accepted',  # Manual creation = auto-accepted
            provisioning_method='manual',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User created successfully: {user.id}")
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create user: {e}")
            raise ConflictException("User creation failed due to duplicate data")
    
    def get_user(self, user_id: int) -> User:
        """Get user by ID"""
        user = User.get_by_id(self.db, user_id)
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")
        return user
    
    def get_user_by_email(self, email: str, tenant_slug: Optional[str] = None) -> Optional[User]:
        """Get user by email"""
        query = self.db.query(User).filter(User.email == email)
        if tenant_slug:
            query = query.filter(User.tenant_slug == tenant_slug)
        return query.first()
    
    def get_by_keycloak_id(self, keycloak_id: str) -> Optional[User]:
        """Get user by Keycloak ID"""
        return User.get_by_keycloak_id(self.db, keycloak_id)
    
    def list_users(
        self,
        tenant_slug: Optional[str] = None,
        active_only: bool = False,
        invitation_status: Optional[str] = None,
        role: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[User], int]:
        """
        List users with filtering and pagination
        
        Args:
            tenant_slug: Filter by tenant
            active_only: Only active users
            invitation_status: Filter by invitation status
            role: Filter by role
            search: Search in email/name
            limit: Page size
            offset: Page offset
            
        Returns:
            Tuple of (users list, total count)
        """
        if not tenant_slug:
            tenant_slug = get_tenant_slug()
        
        query = self.db.query(User).filter(User.tenant_slug == tenant_slug)
        
        # Apply filters
        if active_only:
            query = query.filter(User.is_active == True)
        
        if invitation_status:
            query = query.filter(User.invitation_status == invitation_status)
        
        if role:
            query = query.filter(User.roles.contains([role]))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_term),
                    User.username.ilike(search_term),
                    User.full_name.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.order_by(User.created_at.desc()).limit(limit).offset(offset).all()
        
        return users, total
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user"""
        user = self.get_user(user_id)
        
        # Update fields
        if user_data.username is not None:
            user.username = user_data.username
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        if user_data.phone is not None:
            user.phone = user_data.phone
        if user_data.avatar_url is not None:
            user.avatar_url = user_data.avatar_url
        if user_data.roles is not None:
            user.roles = user_data.roles
        if user_data.permissions is not None:
            user.permissions = user_data.permissions
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.is_verified is not None:
            user.is_verified = user_data.is_verified
        if user_data.preferences is not None:
            user.preferences = user_data.preferences
        
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"User {user_id} updated")
        return user
    
    def delete_user(self, user_id: int) -> None:
        """Delete user"""
        user = self.get_user(user_id)
        self.db.delete(user)
        self.db.commit()
        logger.info(f"User {user_id} deleted")
    
    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> User:
        """Change user password"""
        user = self.get_user(user_id)
        
        if not user.hashed_password:
            raise BadRequestException("User uses SSO authentication, no password to change")
        
        if not self.verify_password(current_password, user.hashed_password):
            raise BadRequestException("Current password is incorrect")
        
        user.hashed_password = self.hash_password(new_password)
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Password changed for user {user_id}")
        return user
    
    def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp"""
        user = self.get_user(user_id)
        user.last_login = datetime.utcnow()
        self.db.commit()
    
    def get_user_stats(self, tenant_slug: Optional[str] = None) -> UserStats:
        """
        Get user statistics for a tenant
        
        Returns:
            UserStats with counts and metrics
        """
        if not tenant_slug:
            tenant_slug = get_tenant_slug()
        
        query = self.db.query(User).filter(User.tenant_slug == tenant_slug)
        
        total_users = query.count()
        active_users = query.filter(User.is_active == True).count()
        verified_users = query.filter(User.is_verified == True).count()
        pending_invitations = query.filter(User.invitation_status == 'pending').count()
        
        # Users by role
        users_by_role = {}
        all_users = query.all()
        for user in all_users:
            for role in (user.roles or []):
                users_by_role[role] = users_by_role.get(role, 0) + 1
        
        # Users by provisioning method
        users_by_provisioning_method = {}
        for user in all_users:
            method = user.provisioning_method or 'manual'
            users_by_provisioning_method[method] = users_by_provisioning_method.get(method, 0) + 1
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_signups = query.filter(User.created_at >= week_ago).count()
        recent_logins = query.filter(User.last_login >= week_ago).count()
        recent_invitations_sent = query.filter(
            User.invitation_status == 'pending',
            User.invited_at >= week_ago
        ).count()
        recent_invitations_accepted = query.filter(
            User.invitation_status == 'accepted',
            User.accepted_at >= week_ago,
            User.provisioning_method == 'invitation'
        ).count()
        
        return UserStats(
            total_users=total_users,
            active_users=active_users,
            verified_users=verified_users,
            pending_invitations=pending_invitations,
            users_by_role=users_by_role,
            users_by_provisioning_method=users_by_provisioning_method,
            recent_signups=recent_signups,
            recent_logins=recent_logins,
            recent_invitations_sent=recent_invitations_sent,
            recent_invitations_accepted=recent_invitations_accepted
        )
