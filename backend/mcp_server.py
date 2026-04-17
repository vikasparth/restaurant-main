from fastmcp import FastMCP
from tools.health import check_health_endpoint
from tools.render_logs import get_render_logs
from tools.github_commits import get_recent_commits
from tools.db_queries import query_request_logs, query_notification_failures
from tools.provider_status import check_provider_status

mcp = FastMCP("monitor")

mcp.tool()(check_health_endpoint)
mcp.tool()(get_render_logs)
mcp.tool()(get_recent_commits)
mcp.tool()(query_request_logs)
mcp.tool()(query_notification_failures)
mcp.tool()(check_provider_status)
mcp.run()
