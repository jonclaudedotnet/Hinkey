#!/bin/bash
# Start MCP Server for DOCMACK Network Connection

echo "🌐 Starting Perplexity MCP Server for DOCMACK Connection"
echo "🔌 Network: 10.0.0.212:3000"
echo "📡 DOCMACK can connect from 10.0.0.200"

cd "/Users/jonclaude/PODCAST LIVE"

# Start the network MCP server
echo "Starting server..."
python3.12 perplexity_mcp_server.py --network

echo "✅ MCP Server ready for DOCMACK connection!"