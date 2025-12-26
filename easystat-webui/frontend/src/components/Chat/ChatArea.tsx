/**
 * 中间聊天/执行区域
 * 
 * 包含：
 * - 顶栏 (标题/状态)
 * - 滚动区域 (LogStream + ReportPanel)
 * - 底部输入框
 */

import { useRef, useEffect } from 'react';
import { LogStream } from '../LogStream';
import { ReportPanel } from '../ReportPanel';
import type { LogEntry } from '../../hooks/useSSE';

interface ChatAreaProps {
  logs: LogEntry[];
  report: string | null;
  query: string;
  setQuery: (q: string) => void;
  isConnected: boolean;
  error: string | null;
  onStart: () => void;
  onStop: () => void;
  onClear: () => void;
}

export function ChatArea({
  logs,
  report,
  query,
  setQuery,
  isConnected,
  error,
  onStart,
  onStop,
  onClear
}: ChatAreaProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // 自动滚动
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, report]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onStart();
    }
  };

  return (
    <div className="chat-area">
      {/* 顶部标题栏 */}
      <header className="chat-header">
        <h2>🤖 EasySTAT Agent</h2>
        <div className="header-actions">
          <button onClick={onClear} disabled={isConnected} className="btn-icon" title="清空">
            🗑️
          </button>
        </div>
      </header>

      {/* 错误提示 */}
      {error && (
        <div className="error-banner">
          ⚠️ {error}
        </div>
      )}

      {/* 滚动内容区域 */}
      <div className="chat-content" ref={scrollRef}>
        <div className="welcome-message">
          <h3>👋 欢迎使用 EasySTAT</h3>
          <p>请输入您的金融分析需求，例如："分析茅台股票" 或 "查询中国GDP"</p>
        </div>
        
        <LogStream logs={logs} />
        <ReportPanel content={report} />
        
        {/* 底部留白，防止内容被输入框遮挡 */}
        <div style={{ height: '80px' }}></div>
      </div>

      {/* 底部输入区域 */}
      <div className="input-area">
        <div className="input-wrapper">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入您的查询..."
            disabled={isConnected}
            className="chat-input"
          />
          <button
            onClick={isConnected ? onStop : onStart}
            className={`btn-send ${isConnected ? 'stop' : ''}`}
          >
            {isConnected ? '⏹' : '➤'}
          </button>
        </div>
      </div>
    </div>
  );
}
