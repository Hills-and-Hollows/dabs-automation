#!/usr/bin/env python3
"""
MCP Client for Archon - Connects Cursor to Archon MCP Server
"""
import asyncio
import json
import os
import sys
from typing import Any, Dict

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    """Main MCP client entry point"""
    try:
        # Get environment variables
        server_url = os.getenv("ARCHON_MCP_URL", "http://localhost:8151")
        project_id = os.getenv("ARCHON_PROJECT_ID", "d010ff76-0202-48e4-8362-40c45e9de39a")
        
        # Connect to Archon MCP server via HTTP
        async with httpx.AsyncClient() as client:
            # Initialize session
            response = await client.post(f"{server_url}/mcp/init", 
                                       json={"project_id": project_id})
            
            if response.status_code != 200:
                print(f"Failed to initialize MCP session: {response.text}", file=sys.stderr)
                sys.exit(1)
            
            session_data = response.json()
            session_id = session_data.get("session_id")
            
            # Start MCP stdio bridge
            server_params = StdioServerParameters(
                command="python3",
                args=["-c", f"""
import asyncio
from archon.mcp.server import create_mcp_server

async def main():
    server = create_mcp_server(
        server_url="{server_url}",
        session_id="{session_id}",
        project_id="{project_id}"
    )
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
"""],
                env=dict(os.environ)
            )
            
            async with stdio_client(server_params) as (read, write):
                session = ClientSession(read, write)
                
                # Initialize the session
                await session.initialize()
                
                # Keep the session alive
                while True:
                    await asyncio.sleep(1)
                    
    except Exception as e:
        print(f"MCP Client error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
