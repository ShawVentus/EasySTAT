/**
 * EasySTAT WebUI - 主布局组件
 * 
 * 采用三栏布局：
 * - 左侧：历史记录 (HistorySidebar)
 * - 中间：聊天/执行流 (ChatArea)
 * - 右侧：工作区/文件 (WorkspaceSidebar)
 */

import type { ReactNode } from 'react';
import './MainLayout.css';

interface MainLayoutProps {
  leftSidebar: ReactNode;
  center: ReactNode;
  rightSidebar: ReactNode;
}

export function MainLayout({ leftSidebar, center, rightSidebar }: MainLayoutProps) {
  return (
    <div className="main-layout">
      <aside className="sidebar left-sidebar">
        {leftSidebar}
      </aside>
      <main className="center-area">
        {center}
      </main>
      <aside className="sidebar right-sidebar">
        {rightSidebar}
      </aside>
    </div>
  );
}
