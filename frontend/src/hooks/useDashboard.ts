import { useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

export const useWebSocket = () => {
  const queryClient = useQueryClient();

  useEffect(() => {
    let isUnmounted = false;
    let ws: WebSocket | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout>;

    const getWsUrl = () => {
      const apiBase = import.meta.env.VITE_API_BASE_URL;
      if (apiBase) {
        const proto = apiBase.startsWith('https') ? 'wss:' : 'ws:';
        const host = apiBase.replace(/^https?:\/\//, '');
        return `${proto}//${host}/ws/dashboard`;
      }
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${proto}//${window.location.host}/ws/dashboard`;
    };

    const connect = () => {
      if (isUnmounted) return;

      try {
        ws = new WebSocket(getWsUrl());

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            if (message.type === 'AUDIT_EVENT') {
              // Invalidate React Query cache for real-time instant UI update
              queryClient.invalidateQueries({ queryKey: ['auditEvents'] });
              queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
              queryClient.invalidateQueries({ queryKey: ['ruleStats'] });
              queryClient.invalidateQueries({ queryKey: ['toolStats'] });
              queryClient.invalidateQueries({ queryKey: ['riskStats'] });
            }
          } catch {
            // Fallback parsing
          }
        };

        ws.onclose = () => {
          if (!isUnmounted) {
            reconnectTimeout = setTimeout(connect, 3000);
          }
        };

        ws.onerror = () => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.close();
          }
        };
      } catch {
        if (!isUnmounted) {
          reconnectTimeout = setTimeout(connect, 5000);
        }
      }
    };

    connect();

    return () => {
      isUnmounted = true;
      clearTimeout(reconnectTimeout);
      if (ws) {
        ws.onclose = null;
        ws.onerror = null;
        ws.close();
      }
    };
  }, [queryClient]);
};

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
