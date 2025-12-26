/**
 * EasySTAT WebUI 前端 - Markdown 报告渲染组件
 * 
 * 主要功能：
 * - 渲染 CrewAI 执行完成后的 Markdown 格式报告
 * - 支持代码高亮、表格、列表等 Markdown 语法
 */

import ReactMarkdown from 'react-markdown';

/**
 * 组件属性接口
 */
interface ReportPanelProps {
  /** Markdown 格式的报告内容 */
  content: string | null;
}

/**
 * 报告面板组件
 * 
 * 渲染 CrewAI 生成的最终报告。
 * 
 * @param props 组件属性
 * @returns React 组件
 */
export function ReportPanel({ content }: ReportPanelProps) {
  if (!content) {
    return null; // 无内容时不显示
  }

  return (
    <div className="report-panel">
      <h3>📝 执行报告</h3>
      <div className="report-content">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    </div>
  );
}
