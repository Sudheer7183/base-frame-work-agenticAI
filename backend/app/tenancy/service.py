# """Tenant management service with provisioning and deprovisioning"""

# import logging
# from datetime import datetime
# from typing import Optional, List, Dict, Any
# from sqlalchemy import text
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import SQLAlchemyError
# from .models import Tenant, TenantStatus
# from .validators import validate_schema_name, validate_slug
# from .exceptions import (
#     TenantProvisionError,
#     TenantDeprovisionError,
#     InvalidTenantError,
#     TenantNotFoundError
# )
# from .db import get_engine

# logger = logging.getLogger(__name__)


# class TenantService:
#     """Service for managing tenant lifecycle"""
    
#     def __init__(self, db: Session):
#         self.db = db
#         self.engine = get_engine()
    
#     def create_tenant(
#         self,
#         slug: str,
#         name: str,
#         schema_name: Optional[str] = None,
#         admin_email: Optional[str] = None,
#         description: Optional[str] = None,
#         config: Optional[Dict[str, Any]] = None,
#         max_users: Optional[int] = None
#     ) -> Tenant:
#         """
#         Create and provision a new tenant
        
#         Args:
#             slug: Tenant slug (unique identifier)
#             name: Display name
#             schema_name: PostgreSQL schema name (auto-generated if not provided)
#             admin_email: Admin contact email
#             description: Tenant description
#             config: Additional configuration
#             max_users: Maximum users allowed
            
#         Returns:
#             Created Tenant object
            
#         Raises:
#             InvalidTenantError: If validation fails
#             TenantProvisionError: If provisioning fails
#         """
#         # Validate inputs
#         validate_slug(slug)
        
#         # Auto-generate schema name if not provided
#         if not schema_name:
#             schema_name = f"tenant_{slug}"
        
#         validate_schema_name(schema_name)
        
#         # Check if tenant already exists
#         if Tenant.exists(self.db, slug=slug):
#             raise InvalidTenantError(f"Tenant with slug '{slug}' already exists")
        
#         if Tenant.exists(self.db, schema=schema_name):
#             raise InvalidTenantError(f"Schema '{schema_name}' already exists")
        
#         logger.info(f"Creating tenant: slug={slug}, schema={schema_name}")
        
#         # Create tenant record with provisioning status
#         tenant = Tenant(
#             slug=slug,
#             schema_name=schema_name,
#             name=name,
#             description=description,
#             status=TenantStatus.PROVISIONING.value,
#             config=config or {},
#             max_users=max_users,
#             admin_email=admin_email,
#             created_at=datetime.utcnow(),
#             updated_at=datetime.utcnow()
#         )
        
#         try:
#             # Add to database
#             self.db.add(tenant)
#             self.db.commit()
            
#             # Provision schema
#             self._provision_schema(schema_name)
            
#             # Run migrations (implement based on your migration tool)
#             self._run_migrations(schema_name)
            
#             # Update status to active
#             tenant.status = TenantStatus.ACTIVE.value
#             tenant.updated_at = datetime.utcnow()
#             self.db.commit()
            
#             logger.info(f"Tenant created successfully: {slug}")
#             return tenant
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Failed to create tenant {slug}: {e}")
            
#             # Cleanup on failure
#             try:
#                 self._cleanup_failed_provision(schema_name)
#             except Exception as cleanup_error:
#                 logger.error(f"Cleanup failed for {schema_name}: {cleanup_error}")
            
#             raise TenantProvisionError(f"Failed to provision tenant: {e}")
    
#     def _provision_schema(self, schema_name: str) -> None:
#         """Create PostgreSQL schema"""
#         validate_schema_name(schema_name)
        
#         logger.info(f"Creating schema: {schema_name}")
        
#         try:
#             with self.engine.connect() as conn:
#                 # Use identifier quoting for safety
#                 conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
#                 conn.commit()
                
#             logger.info(f"Schema created: {schema_name}")
            
#         except SQLAlchemyError as e:
#             logger.error(f"Failed to create schema {schema_name}: {e}")
#             raise TenantProvisionError(f"Schema creation failed: {e}")
    
#     def _run_migrations(self, schema_name: str) -> None:
#         """
#         Run database migrations for tenant schema
        
#         Override this method to integrate with your migration tool
#         (Alembic, etc.)
#         """
#         logger.info(f"Running migrations for schema: {schema_name}")
        
#         # Example: Run Alembic migrations
#         # from alembic import command
#         # from alembic.config import Config
#         # 
#         # alembic_cfg = Config("alembic.ini")
#         # alembic_cfg.set_main_option("schema", schema_name)
#         # command.upgrade(alembic_cfg, "head")
        
#         # For now, just log
#         logger.info(f"Migrations completed for schema: {schema_name}")
    
#     def _cleanup_failed_provision(self, schema_name: str) -> None:
#         """Cleanup after failed provisioning"""
#         logger.warning(f"Cleaning up failed provision: {schema_name}")
        
#         try:
#             with self.engine.connect() as conn:
#                 conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
#                 conn.commit()
#         except Exception as e:
#             logger.error(f"Cleanup failed for {schema_name}: {e}")
    
#     def get_tenant(self, slug: str) -> Tenant:
#         """
#         Get tenant by slug
        
#         Raises:
#             TenantNotFoundError: If tenant doesn't exist
#         """
#         tenant = Tenant.get_by_slug(self.db, slug)
#         if not tenant:
#             raise TenantNotFoundError(slug)
#         return tenant
    
#     def list_tenants(
#         self,
#         status: Optional[TenantStatus] = None,
#         limit: int = 100,
#         offset: int = 0
#     ) -> List[Tenant]:
#         """List tenants with optional filtering"""
#         query = self.db.query(Tenant)
        
#         if status:
#             query = query.filter(Tenant.status == status.value)
        
#         return query.offset(offset).limit(limit).all()
    
#     def update_tenant(
#         self,
#         slug: str,
#         name: Optional[str] = None,
#         description: Optional[str] = None,
#         admin_email: Optional[str] = None,
#         config: Optional[Dict[str, Any]] = None,
#         max_users: Optional[int] = None
#     ) -> Tenant:
#         """Update tenant metadata"""
#         tenant = self.get_tenant(slug)
        
#         if name is not None:
#             tenant.name = name
#         if description is not None:
#             tenant.description = description
#         if admin_email is not None:
#             tenant.admin_email = admin_email
#         if config is not None:
#             tenant.config = config
#         if max_users is not None:
#             tenant.max_users = max_users
        
#         tenant.updated_at = datetime.utcnow()
        
#         self.db.commit()
#         logger.info(f"Tenant updated: {slug}")
        
#         return tenant
    
#     def suspend_tenant(self, slug: str, reason: Optional[str] = None) -> Tenant:
#         """Suspend a tenant (soft disable)"""
#         tenant = self.get_tenant(slug)
        
#         tenant.status = TenantStatus.SUSPENDED.value
#         tenant.suspended_at = datetime.utcnow()
#         tenant.updated_at = datetime.utcnow()
        
#         if reason:
#             tenant.config = tenant.config or {}
#             tenant.config['suspension_reason'] = reason
        
#         self.db.commit()
#         logger.warning(f"Tenant suspended: {slug}, reason: {reason}")
        
#         return tenant
    
#     def activate_tenant(self, slug: str) -> Tenant:
#         """Activate a suspended tenant"""
#         tenant = self.get_tenant(slug)
        
#         tenant.status = TenantStatus.ACTIVE.value
#         tenant.suspended_at = None
#         tenant.updated_at = datetime.utcnow()
        
#         if tenant.config and 'suspension_reason' in tenant.config:
#             del tenant.config['suspension_reason']
        
#         self.db.commit()
#         logger.info(f"Tenant activated: {slug}")
        
#         return tenant
    
#     def deprovision_tenant(
#         self,
#         slug: str,
#         delete_schema: bool = False,
#         backup_first: bool = True
#     ) -> None:
#         """
#         Deprovision a tenant
        
#         Args:
#             slug: Tenant slug
#             delete_schema: Whether to drop the schema (dangerous!)
#             backup_first: Whether to backup data before deletion
#         """
#         tenant = self.get_tenant(slug)
        
#         logger.warning(f"Deprovisioning tenant: {slug}, delete_schema={delete_schema}")
        
#         try:
#             # Update status
#             tenant.status = TenantStatus.DEPROVISIONING.value
#             tenant.updated_at = datetime.utcnow()
#             self.db.commit()
            
#             # Backup if requested
#             if backup_first:
#                 self._backup_tenant_data(tenant.schema_name)
            
#             # Delete schema if requested
#             if delete_schema:
#                 self._drop_schema(tenant.schema_name)
            
#             # Mark as inactive
#             tenant.status = TenantStatus.INACTIVE.value
#             tenant.updated_at = datetime.utcnow()
#             self.db.commit()
            
#             logger.info(f"Tenant deprovisioned: {slug}")
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Failed to deprovision tenant {slug}: {e}")
#             raise TenantDeprovisionError(f"Deprovision failed: {e}")
    
#     def _backup_tenant_data(self, schema_name: str) -> None:
#         """
#         Backup tenant data before deletion
        
#         Override this method to implement actual backup logic
#         """
#         logger.info(f"Backing up tenant data: {schema_name}")
        
#         # Example: Use pg_dump
#         # import subprocess
#         # subprocess.run([
#         #     "pg_dump",
#         #     "-n", schema_name,
#         #     "-f", f"/backups/{schema_name}_{datetime.now()}.sql"
#         # ])
        
#         logger.info(f"Backup completed: {schema_name}")
    
#     def _drop_schema(self, schema_name: str) -> None:
#         """Drop PostgreSQL schema (DANGEROUS!)"""
#         validate_schema_name(schema_name)
        
#         logger.warning(f"DROPPING SCHEMA: {schema_name}")
        
#         try:
#             with self.engine.connect() as conn:
#                 conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
#                 conn.commit()
                
#             logger.warning(f"Schema dropped: {schema_name}")
            
#         except SQLAlchemyError as e:
#             logger.error(f"Failed to drop schema {schema_name}: {e}")
#             raise TenantDeprovisionError(f"Schema deletion failed: {e}")


"""Tenant management service with provisioning and deprovisioning"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from alembic.config import Config
from alembic import command
from .models import Tenant, TenantStatus
from .validators import validate_schema_name, validate_slug
from .exceptions import (
    TenantProvisionError,
    TenantDeprovisionError,
    InvalidTenantError,
    TenantNotFoundError
)
from .db import get_engine

logger = logging.getLogger(__name__)


class TenantService:
    """Service for managing tenant lifecycle"""
    
    def __init__(self, db: Session):
        self.db = db
        self.engine = get_engine()
    
    def create_tenant(
        self,
        slug: str,
        name: str,
        schema_name: Optional[str] = None,
        admin_email: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        max_users: Optional[int] = None
    ) -> Tenant:
        """
        Create and provision a new tenant
        
        Args:
            slug: Tenant slug (unique identifier)
            name: Display name
            schema_name: PostgreSQL schema name (auto-generated if not provided)
            admin_email: Admin contact email
            description: Tenant description
            config: Additional configuration
            max_users: Maximum users allowed
            
        Returns:
            Created Tenant object
            
        Raises:
            InvalidTenantError: If validation fails
            TenantProvisionError: If provisioning fails
        """
        # Validate inputs
        validate_slug(slug)
        
        # Auto-generate schema name if not provided
        if not schema_name:
            schema_name = f"tenant_{slug}"
        
        validate_schema_name(schema_name)
        
        # Check if tenant already exists
        if Tenant.exists(self.db, slug=slug):
            raise InvalidTenantError(f"Tenant with slug '{slug}' already exists")
        
        if Tenant.exists(self.db, schema=schema_name):
            raise InvalidTenantError(f"Schema '{schema_name}' already exists")
        
        logger.info(f"Creating tenant: slug={slug}, schema={schema_name}")
        
        # Create tenant record with provisioning status
        tenant = Tenant(
            slug=slug,
            schema_name=schema_name,
            name=name,
            description=description,
            status=TenantStatus.PROVISIONING.value,
            config=config or {},
            max_users=max_users,
            admin_email=admin_email,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            # Add to database
            self.db.add(tenant)
            self.db.commit()
            
            # Provision schema - use separate connection to avoid transaction conflict
            self._provision_schema(schema_name)
            
            # Run migrations (implement based on your migration tool)
            self._run_migrations(schema_name)
            
            # Update status to active
            tenant.status = TenantStatus.ACTIVE.value
            tenant.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Tenant created successfully: {slug}")
            return tenant
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create tenant {slug}: {e}")
            
            # Cleanup on failure
            try:
                self._cleanup_failed_provision(schema_name)
            except Exception as cleanup_error:
                logger.error(f"Cleanup failed for {schema_name}: {cleanup_error}")
            
            raise TenantProvisionError(f"Failed to provision tenant: {e}")
    
    def _provision_schema(self, schema_name: str) -> None:
        """Create PostgreSQL schema using isolation level AUTOCOMMIT"""
        validate_schema_name(schema_name)
        
        logger.info(f"Creating schema: {schema_name}")
        
        try:
            # Use AUTOCOMMIT isolation level for DDL operations
            # This avoids transaction conflicts and is the proper way to execute CREATE SCHEMA
            with self.engine.connect().execution_options(
                isolation_level="AUTOCOMMIT"
            ) as conn:
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
                logger.info(f"Schema created: {schema_name}")
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create schema {schema_name}: {e}")
            raise TenantProvisionError(f"Schema creation failed: {e}")
    
    def _run_migrations(self, schema_name: str) -> None:
        """
        ✅ ACTUALLY RUN DATABASE MIGRATIONS FOR TENANT SCHEMA
        
        Integrates with Alembic to run migrations programmatically
        """
        validate_schema_name(schema_name)
        
        logger.info(f"Running migrations for schema: {schema_name}")
        
        try:
            # Find alembic.ini
            backend_dir = Path(__file__).parent.parent.parent
            alembic_ini = backend_dir / "alembic.ini"
            
            if not alembic_ini.exists():
                raise TenantProvisionError(f"alembic.ini not found at {alembic_ini}")
            
            # Create Alembic config
            alembic_cfg = Config(str(alembic_ini))
            
            # Set the schema in the config
            # This gets read by env.py via config.get_main_option("schema")
            alembic_cfg.set_main_option("schema", schema_name)
            
            # Set script location
            alembic_cfg.set_main_option(
                "script_location", 
                str(backend_dir / "alembic")
            )
            
            # Run upgrade to head
            logger.info(f"Running: alembic upgrade head for schema {schema_name}")
            command.upgrade(alembic_cfg, "head")
            
            logger.info(f"✅ Migrations completed for schema: {schema_name}")
            
        except Exception as e:
            logger.error(f"Migration failed for {schema_name}: {e}")
            raise TenantProvisionError(f"Migration failed: {e}")
    
    def _cleanup_failed_provision(self, schema_name: str) -> None:
        """Cleanup after failed provisioning"""
        logger.warning(f"Cleaning up failed provision: {schema_name}")
        
        try:
            conn = self.engine.connect()
            try:
                with conn.begin():
                    conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Cleanup failed for {schema_name}: {e}")
    
    def get_tenant(self, slug: str) -> Tenant:
        """
        Get tenant by slug
        
        Raises:
            TenantNotFoundError: If tenant doesn't exist
        """
        tenant = Tenant.get_by_slug(self.db, slug)
        if not tenant:
            raise TenantNotFoundError(slug)
        return tenant
    
    def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tenant]:
        """List tenants with optional filtering"""
        query = self.db.query(Tenant)
        
        if status:
            query = query.filter(Tenant.status == status.value)
        
        return query.offset(offset).limit(limit).all()
    
    def update_tenant(
        self,
        slug: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        admin_email: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        max_users: Optional[int] = None
    ) -> Tenant:
        """Update tenant metadata"""
        tenant = self.get_tenant(slug)
        
        if name is not None:
            tenant.name = name
        if description is not None:
            tenant.description = description
        if admin_email is not None:
            tenant.admin_email = admin_email
        if config is not None:
            tenant.config = config
        if max_users is not None:
            tenant.max_users = max_users
        
        tenant.updated_at = datetime.utcnow()
        
        self.db.commit()
        logger.info(f"Tenant updated: {slug}")
        
        return tenant
    
    def suspend_tenant(self, slug: str, reason: Optional[str] = None) -> Tenant:
        """Suspend a tenant (soft disable)"""
        tenant = self.get_tenant(slug)
        
        tenant.status = TenantStatus.SUSPENDED.value
        tenant.suspended_at = datetime.utcnow()
        tenant.updated_at = datetime.utcnow()
        
        if reason:
            tenant.config = tenant.config or {}
            tenant.config['suspension_reason'] = reason
        
        self.db.commit()
        logger.warning(f"Tenant suspended: {slug}, reason: {reason}")
        
        return tenant
    
    def activate_tenant(self, slug: str) -> Tenant:
        """Activate a suspended tenant"""
        tenant = self.get_tenant(slug)
        
        tenant.status = TenantStatus.ACTIVE.value
        tenant.suspended_at = None
        tenant.updated_at = datetime.utcnow()
        
        if tenant.config and 'suspension_reason' in tenant.config:
            del tenant.config['suspension_reason']
        
        self.db.commit()
        logger.info(f"Tenant activated: {slug}")
        
        return tenant
    
    def deprovision_tenant(
        self,
        slug: str,
        delete_schema: bool = False,
        backup_first: bool = True
    ) -> None:
        """
        Deprovision a tenant
        
        Args:
            slug: Tenant slug
            delete_schema: Whether to drop the schema (dangerous!)
            backup_first: Whether to backup data before deletion
        """
        tenant = self.get_tenant(slug)
        
        logger.warning(f"Deprovisioning tenant: {slug}, delete_schema={delete_schema}")
        
        try:
            # Update status
            tenant.status = TenantStatus.DEPROVISIONING.value
            tenant.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Backup if requested
            if backup_first:
                self._backup_tenant_data(tenant.schema_name)
            
            # Delete schema if requested
            if delete_schema:
                self._drop_schema(tenant.schema_name)
            
            # Mark as inactive
            tenant.status = TenantStatus.INACTIVE.value
            tenant.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Tenant deprovisioned: {slug}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to deprovision tenant {slug}: {e}")
            raise TenantDeprovisionError(f"Deprovision failed: {e}")
    
    def _backup_tenant_data(self, schema_name: str) -> None:
        """
        Backup tenant data before deletion
        
        Override this method to implement actual backup logic
        """
        logger.info(f"Backing up tenant data: {schema_name}")
        
        # Example: Use pg_dump
        # import subprocess
        # subprocess.run([
        #     "pg_dump",
        #     "-n", schema_name,
        #     "-f", f"/backups/{schema_name}_{datetime.now()}.sql"
        # ])
        
        logger.info(f"Backup completed: {schema_name}")
    
    def _drop_schema(self, schema_name: str) -> None:
        """Drop PostgreSQL schema (DANGEROUS!)"""
        validate_schema_name(schema_name)
        
        logger.warning(f"DROPPING SCHEMA: {schema_name}")
        
        try:
            conn = self.engine.connect()
            try:
                with conn.begin():
                    conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
                
                logger.warning(f"Schema dropped: {schema_name}")
            finally:
                conn.close()
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop schema {schema_name}: {e}")
            raise TenantDeprovisionError(f"Schema deletion failed: {e}")