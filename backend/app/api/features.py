"""
API Routes for P2 Features
Endpoints for tools, monitoring, templates, and exports
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.tools.registry import get_tool_registry, ToolDefinition
from app.workflows.templates import get_workflow_registry, WorkflowType
from app.export.exporter import get_exporter, get_report_generator, ExportFormat
from app.core.monitoring import get_monitoring
from app.core.cache import get_cache_manager
from app.models.agent import AgentExecutionLog
from app.models.hitl import HITLRecord
logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Tool Management
# =============================================================================

@router.get("/tools", response_model=List[dict])
async def list_tools(
    category: Optional[str] = Query(None, description="Filter by category"),
    enabled_only: bool = Query(True, description="Only return enabled tools")
):
    """List all registered tools"""
    registry = get_tool_registry()
    tools = registry.list_tools(category=category, enabled_only=enabled_only)
    
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "version": tool.version,
            "enabled": tool.enabled,
            "timeout_seconds": tool.timeout_seconds,
            "requires_auth": tool.requires_auth,
            "parameters": tool.parameters
        }
        for tool in tools
    ]


@router.get("/tools/{tool_name}")
async def get_tool_details(tool_name: str):
    """Get detailed information about a specific tool"""
    registry = get_tool_registry()
    definition = registry.get_definition(tool_name)
    
    if not definition:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    tool = registry.get_tool(tool_name)
    
    return {
        "name": definition.name,
        "description": definition.description,
        "category": definition.category,
        "version": definition.version,
        "enabled": definition.enabled,
        "timeout_seconds": definition.timeout_seconds,
        "requires_auth": definition.requires_auth,
        "parameters": definition.parameters,
        "execution_count": tool.execution_count if tool else 0,
        "last_execution": tool.last_execution.isoformat() if tool and tool.last_execution else None
    }


@router.post("/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    parameters: dict
):
    """Execute a tool directly"""
    registry = get_tool_registry()
    
    try:
        result = await registry.execute(tool_name, parameters)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Tool execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Tool execution failed")


# =============================================================================
# Workflow Templates
# =============================================================================

@router.get("/workflow-templates")
async def list_workflow_templates(
    workflow_type: Optional[WorkflowType] = Query(None, description="Filter by type"),
    requires_hitl: Optional[bool] = Query(None, description="Filter by HITL requirement")
):
    """List available workflow templates"""
    registry = get_workflow_registry()
    templates = registry.list(workflow_type=workflow_type, requires_hitl=requires_hitl)
    
    return [
        {
            "name": template.name,
            "type": template.type.value,
            "description": template.description,
            "required_tools": template.required_tools or [],
            "recommended_llm": template.recommended_llm,
            "estimated_cost_per_run": template.estimated_cost_per_run,
            "hitl_enabled": template.config.get("hitl", {}).get("enabled", False)
        }
        for template in templates
    ]


@router.get("/workflow-templates/{template_name}")
async def get_workflow_template(template_name: str):
    """Get detailed workflow template configuration"""
    registry = get_workflow_registry()
    template = registry.get(template_name)
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Template not found: {template_name}")
    
    return template.to_dict()


@router.post("/workflow-templates/{template_name}/create")
async def create_from_template(
    template_name: str,
    custom_config: Optional[dict] = None
):
    """Create a workflow configuration from template"""
    registry = get_workflow_registry()
    
    try:
        workflow_config = registry.create_from_template(template_name, custom_config)
        return workflow_config
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/workflow-templates/{template_name}/export")
async def export_template(template_name: str):
    """Export template as JSON"""
    registry = get_workflow_registry()
    
    try:
        template_json = registry.export_template(template_name)
        return Response(
            content=template_json,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={template_name}.json"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# Monitoring & Metrics
# =============================================================================

@router.get("/monitoring/health")
async def get_monitoring_health():
    """Get monitoring system health status"""
    monitoring = get_monitoring()
    return monitoring.get_health_status()


@router.get("/monitoring/metrics/summary")
async def get_metrics_summary():
    """Get summary of all metrics"""
    monitoring = get_monitoring()
    
    return {
        "metrics_enabled": monitoring.metrics.enabled,
        "tracing_enabled": monitoring.tracer.enabled,
        "performance_stats": monitoring.performance.get_all_stats()
    }


@router.get("/monitoring/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        cache = get_cache_manager()
        return cache.get_stats()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/monitoring/cache/clear")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Pattern to match keys (e.g., 'user:*')")
):
    """Clear cache entries"""
    try:
        cache = get_cache_manager()
        
        if pattern:
            count = await cache.backend.clear_pattern(pattern)
            return {"message": f"Cleared {count} cache entries matching pattern: {pattern}"}
        else:
            # Clear all - use wildcard pattern
            count = await cache.backend.clear_pattern("*")
            return {"message": f"Cleared all {count} cache entries"}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# =============================================================================
# Data Export
# =============================================================================

@router.post("/export/executions")
async def export_executions(
    format: ExportFormat = Query(ExportFormat.CSV, description="Export format"),
    agent_id: Optional[int] = Query(None, description="Filter by agent ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records"),
    db: Session = Depends(get_db)
):
    """Export agent execution logs"""
    
    # Query executions
    query = db.query(AgentExecutionLog)
    
    if agent_id:
        query = query.filter(AgentExecutionLog.agent_id == agent_id)
    
    if status:
        query = query.filter(AgentExecutionLog.status == status)
    
    if start_date:
        query = query.filter(AgentExecutionLog.started_at >= start_date)
    
    if end_date:
        query = query.filter(AgentExecutionLog.started_at <= end_date)
    
    executions = query.order_by(AgentExecutionLog.started_at.desc()).limit(limit).all()
    
    # Convert to dictionaries
    execution_dicts = [
        {
            "id": e.id,
            "agent_id": e.agent_id,
            "execution_id": e.execution_id,
            "status": e.status,
            "input_data": e.input,
            "output_data": e.output,
            "error": e.error,
            "duration_ms": e.duration_ms,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None
        }
        for e in executions
    ]
    
    # Export
    exporter = get_exporter()
    export_data = exporter.export_executions(execution_dicts, format=format)
    
    # Determine content type and filename
    content_types = {
        ExportFormat.CSV: "text/csv",
        ExportFormat.JSON: "application/json",
        ExportFormat.JSONL: "application/x-ndjson",
        ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    
    extensions = {
        ExportFormat.CSV: "csv",
        ExportFormat.JSON: "json",
        ExportFormat.JSONL: "jsonl",
        ExportFormat.EXCEL: "xlsx"
    }
    
    filename = f"executions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{extensions[format]}"
    
    return Response(
        content=export_data,
        media_type=content_types[format],
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/export/hitl-records")
async def export_hitl_records(
    format: ExportFormat = Query(ExportFormat.CSV, description="Export format"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records"),
    db: Session = Depends(get_db)
):
    """Export HITL records"""
    
    # Query HITL records
    query = db.query(HITLRecord)
    
    if status:
        query = query.filter(HITLRecord.status == status)
    
    if priority:
        query = query.filter(HITLRecord.priority == priority)
    
    if start_date:
        query = query.filter(HITLRecord.created_at >= start_date)
    
    if end_date:
        query = query.filter(HITLRecord.created_at <= end_date)
    
    records = query.order_by(HITLRecord.created_at.desc()).limit(limit).all()
    
    # Convert to dictionaries
    record_dicts = [
        {
            "id": r.id,
            "agent_id": r.agent_id,
            "agent_name": r.agent_name,
            "execution_id": r.execution_id,
            "status": r.status,
            "priority": r.priority,
            "input_data": r.input_data,
            "output_data": r.output_data,
            "decision": r.decision,
            "decision_reason": r.decision_reason,
            "assigned_to": r.assigned_to,
            "reviewed_by": r.reviewed_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None
        }
        for r in records
    ]
    
    # Export
    exporter = get_exporter()
    export_data = exporter.export_hitl_records(record_dicts, format=format)
    
    # Content type and filename
    content_types = {
        ExportFormat.CSV: "text/csv",
        ExportFormat.JSON: "application/json",
        ExportFormat.JSONL: "application/x-ndjson",
        ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    
    extensions = {
        ExportFormat.CSV: "csv",
        ExportFormat.JSON: "json",
        ExportFormat.JSONL: "jsonl",
        ExportFormat.EXCEL: "xlsx"
    }
    
    filename = f"hitl_records_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{extensions[format]}"
    
    return Response(
        content=export_data,
        media_type=content_types[format],
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/export/report/executions")
async def generate_execution_report(
    format: ExportFormat = Query(ExportFormat.EXCEL, description="Report format"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    db: Session = Depends(get_db)
):
    """Generate comprehensive execution report with analytics"""
    
    # Query executions
    query = db.query(AgentExecutionLog)
    
    if start_date:
        query = query.filter(AgentExecutionLog.started_at >= start_date)
    
    if end_date:
        query = query.filter(AgentExecutionLog.started_at <= end_date)
    
    executions = query.all()
    
    # Convert to dictionaries
    execution_dicts = [
        {
            "id": e.id,
            "agent_id": e.agent_id,
            "execution_id": e.execution_id,
            "status": e.status,
            "duration_ms": e.duration_ms,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None
        }
        for e in executions
    ]
    
    # Generate report
    report_gen = get_report_generator()
    report_data = report_gen.generate_execution_report(
        execution_dicts,
        start_date=start_date,
        end_date=end_date,
        format=format
    )
    
    filename = f"execution_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return Response(
        content=report_data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
