import asyncio
from app.agent_langgraph.async_executor import AsyncLangGraphExecutor
from core.audit import AuditLogger
from core.notifications import NotificationService
from core.database import get_session

async def main():
    db = get_session()

    audit_logger = AuditLogger(db)
    notification_service = NotificationService(db)
    executor = AsyncLangGraphExecutor(db, audit_logger, notification_service)

    # Execute agent (non-streaming)
    result = await executor.execute(
        agent_id=1,
        input_data={"message": "Hello"},
        user_id=1
    )
    print("Execution result:", result)

    # Execute agent with streaming
    async for event in executor.execute_with_streaming(
        agent_id=1,
        input_data={"message": "Hello"},
        user_id=1
    ):
        print("Stream event:", event)

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
