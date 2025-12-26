/**
 * EasySTAT 日志流显示组件
 * 
 * 主要功能：
 * - 实时显示对话和执行日志
 * - 智能解析后端返回的 Python 字典格式字符串
 * - 将工具调用、执行结果渲染为美观的卡片
 * - 提供错误信息的视觉强调
 */

import { useState, useMemo } from 'react';
import type { LogEntry } from '../hooks/useSSE';

interface LogStreamProps {
  logs: LogEntry[];
}

/**
 * 尝试解析 Python 风格的字典字符串
 * 后端 CrewAI 经常返回 {'tool': '...', 'output': '...'} 这样的非标准 JSON 字符串
 */
function parseAgentLog(message: string) {
  // 1. 如果本身就是短文本，直接返回
  if (message.length < 10) return { type: 'text', content: message };

  // 2. 尝试解析标准 JSON
  try {
    const jsonObj = JSON.parse(message);
    if (jsonObj.tool) return { type: 'tool', ...jsonObj };
    if (jsonObj.error) return { type: 'error', ...jsonObj };
  } catch (e) {
    // 忽略 JSON 错误，继续尝试正则
  }

  // 3. 正则匹配 Python repr() 风格的字典
  // 匹配 tool 名称
  const toolMatch = message.match(/'tool':\s*'([^']+)'/);
  
  // 匹配 output 内容 (尝试匹配被引号包裹的内容，这是一个简化的匹配，可能无法处理复杂嵌套)
  // 策略：如果包含 'tool', 且包含 'output', 则认为是一个工具日志
  if (toolMatch || message.includes("'tool':")) {
      const toolName = toolMatch ? toolMatch[1] : 'Unknown Tool';
      
      // 提取 output，这里比较tricky，简单提取显示即可
      let outputContent = message;
      const outputIdx = message.indexOf("'output':");
      if (outputIdx > -1) {
          const start = outputIdx + 9; // len("'output':")
          // 简单截取后续内容作为 output，去掉末尾可能的 }
          outputContent = message.substring(start).trim();
          if (outputContent.startsWith("'") || outputContent.startsWith('"')) outputContent = outputContent.substring(1);
          if (outputContent.endsWith("'}")) outputContent = outputContent.substring(0, outputContent.length - 2);
          if (outputContent.endsWith('"}')) outputContent = outputContent.substring(0, outputContent.length - 2);
      }

      return {
          type: 'tool',
          tool: toolName,
          output: outputContent,
          raw: message
      };
  }

  // 4. 检测错误
  if (message.toLowerCase().includes('error') || message.includes('Traceback')) {
      return { type: 'error', content: message };
  }

  // 5. 默认文本
  return { type: 'text', content: message };
}

/**
 * 单条日志项组件
 */
function LogItem({ log }: { log: LogEntry }) {
  const parsed = useMemo(() => parseAgentLog(log.message), [log.message]);
  const [expanded, setExpanded] = useState(false);

  // 时间戳格式化
  const timeStr = new Date(log.timestamp).toLocaleTimeString();

  if (parsed.type === 'tool') {
    return (
      <div className="log-card tool-card" style={{ 
          border: '1px solid #2d5af6', 
          backgroundColor: 'rgba(45, 90, 246, 0.05)',
          borderRadius: '8px',
          margin: '8px 0',
          padding: '10px',
          fontSize: '14px'
      }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', color: '#2d5af6', fontWeight: 'bold' }}>
          <span>🔧 工具调用: {parsed.tool}</span>
          <span style={{ fontSize: '12px', color: '#888' }}>{timeStr}</span>
        </div>
        
        <div className="card-body" style={{ marginTop: '8px', color: '#ccc' }}>
            <div className="output-preview" style={{ 
                whiteSpace: 'pre-wrap', 
                wordBreak: 'break-all',
                maxHeight: expanded ? 'none' : '100px',
                overflow: 'hidden',
                position: 'relative'
            }}>
                {parsed.output || parsed.raw}
            </div>
            {(parsed.output?.length > 200 || parsed.raw?.length > 200) && (
                <button 
                    onClick={() => setExpanded(!expanded)}
                    style={{ 
                        marginTop: '5px', 
                        background: 'none', 
                        border: 'none', 
                        color: '#2d5af6', 
                        cursor: 'pointer',
                        padding: 0
                    }}
                >
                    {expanded ? '收起' : '展开更多...'}
                </button>
            )}
        </div>
      </div>
    );
  }

  if (parsed.type === 'error' || log.type === 'error') {
    return (
      <div className="log-card error-card" style={{ 
          border: '1px solid #ff4d4f', 
          backgroundColor: 'rgba(255, 77, 79, 0.1)', 
          borderRadius: '8px', 
          margin: '8px 0', 
          padding: '10px',
          color: '#ff4d4f'
      }}>
        <div style={{ fontWeight: 'bold' }}>⚠️ 错误 ({timeStr})</div>
        <div style={{ marginTop: '5px', whiteSpace: 'pre-wrap' }}>{parsed.content || log.message}</div>
      </div>
    );
  }

  // 普通文本消息
  return (
    <div className="log-item" style={{ margin: '4px 0', color: '#e0e0e0', lineHeight: '1.5' }}>
      <span style={{ color: '#666', marginRight: '8px', fontSize: '12px' }}>[{timeStr}]</span>
      <span style={{ whiteSpace: 'pre-wrap' }}>{log.message}</span>
    </div>
  );
}

export function LogStream({ logs }: LogStreamProps) {
  return (
    <div className="log-stream">
      {logs.map((log, index) => (
        <LogItem key={index} log={log} />
      ))}
    </div>
  );
}
