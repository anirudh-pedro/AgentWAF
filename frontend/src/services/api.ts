import axios from 'axios';
import type {
  AuditEvent,
  DashboardSummary,
  RiskStatistics,
  RuleStatistics,
  SystemHealth,
  ToolStatistics,
  UserQueryRequest,
  UserQueryResponse,
  AgentRunResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL !== undefined 
  ? import.meta.env.VITE_API_BASE_URL 
  : '';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  getSummary: async (): Promise<DashboardSummary> => {
    const response = await apiClient.get<DashboardSummary>('/dashboard/summary');
    return response.data;
  },

  getAuditEvents: async (params?: {
    tool?: string;
    decision?: string;
    rule?: string;
    limit?: number;
  }): Promise<AuditEvent[]> => {
    const response = await apiClient.get('/dashboard/audit', { params });
    const data = response.data as any;
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.events)) return data.events;
    if (data && Array.isArray(data.data)) return data.data;
    return [];
  },

  getRuleStats: async (): Promise<RuleStatistics[]> => {
    const response = await apiClient.get<RuleStatistics[]>('/dashboard/rules');
    return Array.isArray(response.data) ? response.data : [];
  },

  getToolStats: async (): Promise<ToolStatistics[]> => {
    const response = await apiClient.get<ToolStatistics[]>('/dashboard/tools');
    return Array.isArray(response.data) ? response.data : [];
  },

  getRiskStats: async (): Promise<RiskStatistics> => {
    const response = await apiClient.get<RiskStatistics>('/dashboard/risk');
    return response.data;
  },

  getSystemHealth: async (): Promise<SystemHealth> => {
    const response = await apiClient.get<SystemHealth>('/dashboard/health');
    return response.data;
  },

  executeAgentQuery: async (payload: UserQueryRequest): Promise<UserQueryResponse> => {
    const response = await apiClient.post<UserQueryResponse>('/agent/execute', payload);
    return response.data;
  },

  executeAgentWorkflow: async (goal: string, sessionId?: string): Promise<AgentRunResponse> => {
    const response = await apiClient.post<AgentRunResponse>('/agent/run', {
      goal,
      session_id: sessionId,
    });
    return response.data;
  },
};
