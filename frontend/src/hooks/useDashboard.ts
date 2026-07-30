import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export const useDashboardSummary = () => {
  return useQuery({
    queryKey: ['dashboardSummary'],
    queryFn: api.getSummary,
    refetchInterval: 5000,
  });
};

export const useAuditEvents = (params?: {
  tool?: string;
  decision?: string;
  rule?: string;
  limit?: number;
}) => {
  return useQuery({
    queryKey: ['auditEvents', params],
    queryFn: () => api.getAuditEvents(params),
    refetchInterval: 5000,
  });
};

export const useRuleStats = () => {
  return useQuery({
    queryKey: ['ruleStats'],
    queryFn: api.getRuleStats,
    refetchInterval: 5000,
  });
};

export const useToolStats = () => {
  return useQuery({
    queryKey: ['toolStats'],
    queryFn: api.getToolStats,
    refetchInterval: 5000,
  });
};

export const useRiskStats = () => {
  return useQuery({
    queryKey: ['riskStats'],
    queryFn: api.getRiskStats,
    refetchInterval: 5000,
  });
};

export const useSystemHealth = () => {
  return useQuery({
    queryKey: ['systemHealth'],
    queryFn: api.getSystemHealth,
    refetchInterval: 10000,
  });
};
