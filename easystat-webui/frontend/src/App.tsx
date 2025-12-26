/**
 * EasySTAT WebUI 前端 - 主应用组件
 * 
 * 架构说明：
 *   App.tsx (入口)
 *   └── MainLayout (三栏布局)
 *       ├── Left: HistorySidebar
 *       ├── Center: ChatArea
 *       └── Right: WorkspaceSidebar
 */

import { useState } from 'react';
import { useSSE } from './hooks/useSSE';
import { MainLayout } from './components/Layout/MainLayout';
import { HistorySidebar } from './components/Sidebar/HistorySidebar';
import { WorkspaceSidebar } from './components/Sidebar/WorkspaceSidebar';
import { ChatArea } from './components/Chat/ChatArea';
import './App.css';

// 后端 API 地址
const API_BASE_URL = 'http://localhost:8000';

function App() {
  // 用户输入查询
  const [query, setQuery] = useState('分析茅台股票');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>('1');
  
  // SSE 连接和日志状态
  const { logs, files, report, isConnected, error, connect, disconnect, stopExecution, clearLogs } = useSSE();

  /**
   * 处理开始执行
   */
  const handleStart = () => {
    if (isConnected) {
      handleStop();
    } else {
      const encodedQuery = encodeURIComponent(query);
      connect(`${API_BASE_URL}/api/stream?query=${encodedQuery}`);
    }
  };

  /**
   * 处理停止执行
   */
  const handleStop = async () => {
    await stopExecution();
    // 延迟断开 SSE，给后端一点时间发送最后的停止事件
    setTimeout(() => {
      disconnect();
    }, 1000);
  };

  /**
   * 处理清空/新建
   */
  const handleClear = () => {
    clearLogs();
  };

  return (
    <MainLayout
      leftSidebar={
        <HistorySidebar 
          currentSessionId={currentSessionId}
          onSelectSession={setCurrentSessionId}
          onNewSession={handleClear}
        />
      }
      center={
        <ChatArea
          logs={logs}
          report={report}
          query={query}
          setQuery={setQuery}
          isConnected={isConnected}
          error={error}
          onStart={handleStart}
          onStop={handleStop}
          onClear={handleClear}
        />
      }
      rightSidebar={
        <WorkspaceSidebar files={files} />
      }
    />
  );
}

export default App;
