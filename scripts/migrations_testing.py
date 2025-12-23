from backend.app.tenancy.db import init_db, get_session
from backend.app.tenancy.service import TenantService

init_db('postgresql://postgres:postgres@localhost:5433/agenticbase2')
db = get_session()
service = TenantService(db)

# This will now actually run migrations!
tenant = service.create_tenant('testfix', 'Test Fix Tenant')
print(f'✅ Tenant created with migrations: {tenant.schema_name}')
db.close()