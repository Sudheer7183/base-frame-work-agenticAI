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

"""User management service"""

import logging
import bcrypt
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserStats
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException
)
from app.tenancy.context import get_tenant_slug

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _ensure_schema_context(self, tenant_slug: str):
        """Ensure the correct schema search path is set"""
        schema_name = f"tenant_{tenant_slug}"
        self.db.execute(text(f"SET search_path TO {schema_name}, public"))
        logger.debug(f"Set search_path to {schema_name}")
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        # Truncate password to 72 bytes if needed (bcrypt limitation)
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            logger.warning("Password exceeds 72 bytes, truncating for bcrypt")
            password_bytes = password_bytes[:72]
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        # Truncate password to 72 bytes if needed (bcrypt limitation)
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Convert hash string to bytes if needed
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        
        return bcrypt.checkpw(password_bytes, hashed_password)
    
    def create_user(
        self,
        user_data: UserCreate,
        tenant_slug: Optional[str] = None
    ) -> User:
        """
        Create a new user in the current tenant
        
        Args:
            user_data: User creation data
            tenant_slug: Tenant slug (auto-detected if not provided)
            
        Returns:
            Created User object
            
        Raises:
            ConflictException: If user with email already exists
            BadRequestException: If validation fails
        """
        # Get tenant context
        if not tenant_slug:
            tenant_slug = get_tenant_slug()
            if not tenant_slug:
                raise BadRequestException("No tenant context available")
        
        logger.info(f"Creating user {user_data.email} in tenant {tenant_slug}")
        
        # Ensure schema context before operations
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
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            
            # Re-establish schema context after commit
            self._ensure_schema_context(tenant_slug)
            
            # Query the user back with explicit schema context
            user = self.db.query(User).filter(User.id == user.id).first()
            
            if not user:
                raise BadRequestException(f"User created but could not be retrieved from tenant schema")
            
            logger.info(f"User created successfully: {user.id}")
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create user: {e}")
            raise ConflictException("User creation failed due to duplicate data")
    
    def get_user(self, user_id: int) -> User:
        """
        Get user by ID
        
        Raises:
            NotFoundException: If user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException(f"User with ID {user_id} not found")
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return User.get_by_email(self.db, email)
    
    def list_users(
        self,
        tenant_slug: Optional[str] = None,
        active_only: bool = False,
        role: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[User], int]:
        """
        List users with filtering and pagination
        
        Returns:
            Tuple of (users list, total count)
        """
        if not tenant_slug:
            tenant_slug = get_tenant_slug()
        
        query = self.db.query(User).filter(User.tenant_slug == tenant_slug)
        
        # Apply filters
        if active_only:
            query = query.filter(User.is_active == True)
        
        if role:
            query = query.filter(User.roles.contains([role]))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.email.ilike(search_term)) |
                (User.username.ilike(search_term)) |
                (User.full_name.ilike(search_term))
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.offset(offset).limit(limit).all()
        
        return users, total
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """
        Update user
        
        Raises:
            NotFoundException: If user not found
        """
        user = self.get_user(user_id)
        tenant_slug = user.tenant_slug
        
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
        
        # Re-establish schema context after commit
        self._ensure_schema_context(tenant_slug)
        
        # Query back instead of refresh
        user = self.db.query(User).filter(User.id == user_id).first()
        
        logger.info(f"User {user_id} updated successfully")
        return user
    
    def delete_user(self, user_id: int) -> None:
        """
        Delete user
        
        Raises:
            NotFoundException: If user not found
        """
        user = self.get_user(user_id)
        
        self.db.delete(user)
        self.db.commit()
        
        logger.info(f"User {user_id} deleted successfully")
    
    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> User:
        """
        Change user password
        
        Raises:
            NotFoundException: If user not found
            BadRequestException: If current password is incorrect
        """
        user = self.get_user(user_id)
        tenant_slug = user.tenant_slug
        
        if not user.hashed_password:
            raise BadRequestException("User does not have a password set")
        
        # Verify current password
        if not self.verify_password(current_password, user.hashed_password):
            raise BadRequestException("Current password is incorrect")
        
        # Set new password
        user.hashed_password = self.hash_password(new_password)
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Re-establish schema context after commit
        self._ensure_schema_context(tenant_slug)
        
        # Query back instead of refresh
        user = self.db.query(User).filter(User.id == user_id).first()
        
        logger.info(f"Password changed for user {user_id}")
        return user
    
    def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp"""
        user = self.get_user(user_id)
        user.last_login = datetime.utcnow()
        self.db.commit()
    
    def get_user_stats(self, tenant_slug: Optional[str] = None) -> UserStats:
        """Get user statistics for a tenant"""
        if not tenant_slug:
            tenant_slug = get_tenant_slug()
        
        query = self.db.query(User).filter(User.tenant_slug == tenant_slug)
        
        total_users = query.count()
        active_users = query.filter(User.is_active == True).count()
        verified_users = query.filter(User.is_verified == True).count()
        
        # Users by role
        users_by_role = {}
        all_users = query.all()
        for user in all_users:
            for role in (user.roles or []):
                users_by_role[role] = users_by_role.get(role, 0) + 1
        
        # Recent activity
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_signups = query.filter(User.created_at >= week_ago).count()
        recent_logins = query.filter(User.last_login >= week_ago).count()
        
        return UserStats(
            total_users=total_users,
            active_users=active_users,
            verified_users=verified_users,
            users_by_role=users_by_role,
            recent_signups=recent_signups,
            recent_logins=recent_logins
        )