/**
 * 历史记录侧边栏
 * 
 * 显示历史会话列表，支持新建会话和切换会话。
 * 目前使用 localStorage 存储简单的会话元数据。
 */

import { useState, useEffect } from 'react';

interface Session {
  id: string;
  title: string;
  timestamp: number;
}

interface HistorySidebarProps {
  currentSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
}

export function HistorySidebar({ currentSessionId, onSelectSession, onNewSession }: HistorySidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([]);

  // 加载历史记录 (模拟)
  useEffect(() => {
    // TODO: 从 localStorage 或后端加载
    const mockSessions: Session[] = [
      { id: '1', title: '分析茅台股票', timestamp: Date.now() },
      { id: '2', title: '查询 GDP 数据', timestamp: Date.now() - 86400000 },
    ];
    setTimeout(() => {
      setSessions(mockSessions);
    }, 0);
  }, []);

  return (
    <div className="history-sidebar">
      <div className="sidebar-header">
        <button className="btn-new-chat" onClick={onNewSession}>
          + 新建对话
        </button>
      </div>
      <div className="session-list">
        <div className="list-group-title">今天</div>
        {sessions.map(session => (
          <div 
            key={session.id} 
            className={`session-item ${currentSessionId === session.id ? 'active' : ''}`}
            onClick={() => onSelectSession(session.id)}
          >
            <span className="session-title">{session.title}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
