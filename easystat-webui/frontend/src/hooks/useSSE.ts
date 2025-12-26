/**
 * EasySTAT WebUI 前端 - SSE 连接 Hook
 * 
 * 主要功能：
 * - 封装 EventSource API，提供 React Hook 接口
 * - 管理 SSE 连接的生命周期（连接、断开、重连）
 * - 将接收到的事件转换为 React 状态
 * - 支持 Phase 2 的结构化事件格式（agent_start、tool_start 等）
 * 
 * 使用方式：
 *   const { logs, files, isConnected, error, connect, disconnect } = useSSE();
 *   connect('/api/stream?query=分析茅台');
 */

import { useState, useCallback, useRef } from 'react';

/**
 * 日志条目接口
 */
export interface LogEntry {
  /** 事件类型：start, agent_start, tool_start, task_start, error, crew_complete 等 */
  type: string;
  /** 日志内容（格式化后的可读文本） */
  message: string;
  /** 时间戳 */
  timestamp: Date;
  /** 原始数据（解析后的 JSON 对象，如果有的话） */
  rawData?: Record<string, unknown>;
}

/**
 * SSE Hook 返回值接口
 */
interface UseSSEReturn {
  /** 日志列表 */
  logs: LogEntry[];
  /** 生成的文件列表 */
  files: string[];
  /** 执行报告内容 */
  report: string | null;
  /** 是否已连接 */
  isConnected: boolean;
  /** 错误信息 */
  error: string | null;
  /** 建立连接 */
  connect: (url: string) => void;
  /** 断开连接 */
  disconnect: () => void;
  /** 停止执行（调用后端接口） */
  stopExecution: () => Promise<void>;
  /** 清空日志 */
  clearLogs: () => void;
}

/**
 * 格式化事件数据为可读消息
 * 
 * 根据事件类型和数据对象，生成用户友好的日志消息。
 * 
 * @param type 事件类型
 * @param data 解析后的事件数据对象
 * @returns 格式化的消息字符串
 */
function formatMessage(type: string, data: Record<string, unknown>): string {
  switch (type) {
    case 'agent_start':
      return `Agent 开始: ${data.agent || '未知'} - ${data.task || ''}`;
    case 'agent_complete':
      return `Agent 完成: ${data.agent || '未知'}`;
    case 'task_start':
      return `任务开始: ${data.task || '未知'}`;
    case 'task_complete':
      return `任务完成: ${data.task || '未知'}`;
    case 'tool_start':
      return `工具调用: ${data.tool || '未知'} (${data.args || ''})`;
    case 'tool_finish':
      return `工具完成: ${data.tool || '未知'}`;
    case 'files_generated': {
      const fileList = Array.isArray(data.files) ? data.files : [];
      return `生成文件: ${fileList.join(', ')}`;
    }
    case 'crew_complete':
      return `执行完成`;
    case 'error':
      return `错误: ${data.error || data.message || '未知错误'}`;
    default:
      return JSON.stringify(data);
  }
}

/**
 * SSE 连接 Hook
 * 
 * 封装 Server-Sent Events 的连接和状态管理。
 * 自动处理连接状态、错误和日志收集。
 * 支持 Phase 2 的结构化事件格式。
 * 
 * @returns {UseSSEReturn} SSE 状态和控制函数
 */
export function useSSE(): UseSSEReturn {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [files, setFiles] = useState<string[]>([]);
  const [report, setReport] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 使用 ref 保存 EventSource 实例，避免闭包问题
  const eventSourceRef = useRef<EventSource | null>(null);

  /**
   * 添加日志条目
   * 
   * Phase 2 改进：支持解析 JSON 格式的 event.data
   * 
   * @param type 事件类型
   * @param data 事件数据（可能是 JSON 字符串或普通字符串）
   */
  const addLog = useCallback((type: string, data: string) => {
    let message = data;
    let rawData: Record<string, unknown> | undefined;
    
    // 尝试解析 JSON 数据
    try {
      const parsed = JSON.parse(data);
      if (typeof parsed === 'object' && parsed !== null) {
        rawData = parsed;
        message = formatMessage(type, parsed);
      }
    } catch {
      // 不是 JSON，保持原样
    }
    
    setLogs(prev => [...prev, {
      type,
      message,
      timestamp: new Date(),
      rawData
    }]);
  }, []);

  /**
   * 建立 SSE 连接
   * 
   * @param url 后端 SSE 接口地址
   */
  const connect = useCallback((url: string) => {
    // 如果已有连接，先断开
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setError(null);
    setIsConnected(true);
    setFiles([]); // 清空之前的文件列表
    setReport(null); // 清空之前的报告
    
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    // ========== Phase 1 兼容事件 ==========
    
    // 处理 start 事件
    eventSource.addEventListener('start', (event) => {
      addLog('start', event.data);
    });

    // 处理 log 事件（Phase 1 通用日志）
    eventSource.addEventListener('log', (event) => {
      addLog('log', event.data);
    });

    // 处理 complete 事件（Phase 1 兼容）
    eventSource.addEventListener('complete', (event) => {
      addLog('complete', event.data);
      setIsConnected(false);
      eventSource.close();
    });

    // ========== Phase 2 新增事件 ==========
    
    // Agent 事件
    eventSource.addEventListener('agent_start', (event) => {
      addLog('agent_start', event.data);
    });

    eventSource.addEventListener('agent_complete', (event) => {
      addLog('agent_complete', event.data);
    });

    // Task 事件
    eventSource.addEventListener('task_start', (event) => {
      addLog('task_start', event.data);
    });

    eventSource.addEventListener('task_complete', (event) => {
      addLog('task_complete', event.data);
    });

    // Tool 事件
    eventSource.addEventListener('tool_start', (event) => {
      addLog('tool_start', event.data);
    });

    eventSource.addEventListener('tool_finish', (event) => {
      addLog('tool_finish', event.data);
    });

    // 文件生成事件
    eventSource.addEventListener('files_generated', (event) => {
      addLog('files_generated', event.data);
      // 解析并存储文件列表
      try {
        const parsed = JSON.parse(event.data);
        if (parsed.files && Array.isArray(parsed.files)) {
          setFiles(parsed.files);
        }
      } catch {
        // 忽略解析错误
      }
    });

    // CrewAI 执行完成事件（替代 complete）
    eventSource.addEventListener('crew_complete', (event) => {
      addLog('crew_complete', event.data);
      // 提取报告内容
      try {
        const parsed = JSON.parse(event.data);
        if (parsed.result) {
          setReport(parsed.result);
        }
      } catch {
        // 如果不是 JSON，直接使用原始数据作为报告
        setReport(event.data);
      }
      setIsConnected(false);
      eventSource.close();
    });

    // 错误事件
    eventSource.addEventListener('error', (event) => {
      if (event instanceof MessageEvent) {
        addLog('error', event.data);
      } else {
        setError('连接出错');
        addLog('error', '连接出错或已断开');
      }
    });

    // 处理连接错误
    eventSource.onerror = () => {
      if (eventSource.readyState === EventSource.CLOSED) {
        setIsConnected(false);
      }
    };
  }, [addLog]);

  /**
   * 断开 SSE 连接
   */
  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsConnected(false);
    addLog('complete', '用户手动断开连接');
  }, [addLog]);

  /**
   * 停止执行（调用后端接口）
   */
  const stopExecution = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/stop', {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error('停止请求失败');
      }
      addLog('log', '已向后端发送停止指令，正在中断...');
    } catch (err) {
      console.error('停止执行失败:', err);
      setError('无法停止执行');
    }
  }, [addLog]);

  /**
   * 清空日志列表
   */
  const clearLogs = useCallback(() => {
    setLogs([]);
    setFiles([]);
    setReport(null);
  }, []);

  return {
    logs,
    files,
    report,
    isConnected,
    error,
    connect,
    disconnect,
    stopExecution,
    clearLogs
  };
}
