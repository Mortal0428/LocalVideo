import { api } from './client'

export interface McpToolParam {
  type: string
  description?: string
  default?: any
}

export interface McpToolSchema {
  name: string
  description: string
  parameters: {
    type: string
    properties: Record<string, McpToolParam>
    required?: string[]
  }
}

export interface McpResourceSchema {
  uri: string
  name: string
  description: string
}

export interface McpPromptSchema {
  name: string
  description: string
  arguments: Array<{
    name: string
    description?: string
    required?: boolean
  }>
}

export interface McpServerNode {
  name: string
  url: string
  type: string
  status: string
  ping_ms: number
}

export interface McpOverviewData {
  server_name: string
  instructions: string
  version: string
  protocol: string
  status: string
  transport: string
  counts: {
    tools: number
    resources: number
    prompts: number
  }
  tools: McpToolSchema[]
  resources: McpResourceSchema[]
  prompts: McpPromptSchema[]
  server_nodes: McpServerNode[]
}

export const mcpApi = {
  getOverview: async () => {
    const res = await api.get('/mcp-admin/overview')
    return res.data as McpOverviewData
  },

  listNodes: async () => {
    const res = await api.get('/mcp-admin/nodes')
    return res.data as McpServerNode[]
  },

  registerNode: async (payload: { name: string; url: string; type?: string }) => {
    const res = await api.post('/mcp-admin/nodes', payload)
    return res.data as McpServerNode
  },

  testSandbox: async (payload: {
    method: 'tools/call' | 'resources/read' | 'prompts/get'
    target: string
    arguments?: Record<string, any>
  }) => {
    const res = await api.post('/mcp-admin/sandbox/test', payload)
    return res.data
  },

  /**
   * ==============================================================================
   * 【全链路前端 API】：callJsonRpc (标准 MCP 协议 JSON-RPC 2.0 在线执行)
   * 【调用来源】：CinemaAgentMcpCenter.vue 在线沙盒执行按钮
   * 【对应后端路由】：POST /api/v1/mcp
   * 【对应后端文件】：backend/app/mcp/server/router.py -> handle_mcp_jsonrpc()
   * 【后续流向】：router.py 解析 method (如 tools/call) -> 调度 core.py FastMCP 工具池 -> 返回执行报文
   * ==============================================================================
   */
  callJsonRpc: async (payload: {
    jsonrpc: string
    id: number | string
    method: string
    params: Record<string, any>
  }) => {
    const res = await api.post('/mcp', payload)
    return res
  }
}
