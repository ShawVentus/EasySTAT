/**
 * EasySTAT WebUI 前端 - 工作区侧边栏
 * 
 * 主要功能：
 * - 实时显示生成的文件列表（结果、日志、中间数据）
 * - 支持文件预览（Markdown/文本），并对 Markdown 进行简单渲染优化
 * - 支持文件下载到本地
 */

import { useState, useEffect } from 'react';
import { DataPreview } from '../DataPreview';

// 后端 API 基础地址（使用相对路径，通过 Vite 代理转发）
const API_BASE_URL = '';

interface FileInfo {
  name: string;
  path: string;
  type: string;
  category: string;
  size: number;
  mtime: number;
  extension: string;
}

interface WorkspaceSidebarProps {
  /** SSE 传来的新生成文件名列表（用于触发刷新） */
  files: string[];
}

export function WorkspaceSidebar({ files: newFiles }: WorkspaceSidebarProps) {
  const [fileList, setFileList] = useState<FileInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewContent, setPreviewContent] = useState<string | null>(null);
  const [previewTitle, setPreviewTitle] = useState('');

  /**
   * 从后端获取完整文件列表
   */
  const fetchFiles = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/files`);
      const data = await response.json();
      setFileList(data);
    } catch (error) {
      console.error('获取文件列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 当组件加载或 SSE 提示有新文件生成时，刷新列表
  useEffect(() => {
    fetchFiles();
  }, [newFiles]);

  /**
   * 处理文件预览
   */
  const handlePreview = async (file: FileInfo) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/files/content?path=${encodeURIComponent(file.path)}`);
      const data = await response.json();
      if (data.content) {
        setPreviewContent(data.content);
        setPreviewTitle(file.name);
      } else {
        alert(data.error || '无法预览该文件');
      }
    } catch (error) {
      alert('预览失败');
    }
  };

  /**
   * 处理文件下载
   */
  const handleDownload = (file: FileInfo) => {
    window.open(`${API_BASE_URL}/api/files/download?path=${encodeURIComponent(file.path)}`, '_blank');
  };

  /**
   * 格式化文件大小
   */
  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="workspace-sidebar">
      <div className="sidebar-header">
        <div className="header-title-group">
          <h3>📂 工作区 <small style={{ fontSize: '0.7em', color: '#888', fontWeight: 'normal' }}>(数据总线)</small></h3>
        </div>
        <button className="refresh-btn" onClick={fetchFiles} disabled={loading}>
          {loading ? '...' : '🔄'}
        </button>
      </div>

      <div className="file-tree">
        {fileList.length === 0 ? (
          <div className="empty-state">暂无生成文件</div>
        ) : (
          <div className="file-list-container">
            {fileList
              .filter(file => file.type !== 'log' && !file.name.endsWith('.log')) // 过滤掉日志文件
              .map((file) => (
              <div key={file.path} className="file-card">
                <div className="file-info">
                  <span className="file-icon">
                    {file.type === 'data' ? '📊' : file.extension === '.md' ? '📄' : file.extension === '.log' ? '📝' : '📄'}
                  </span>
                  <div className="file-details">
                    <div className="file-name" title={file.name}>{file.name}</div>
                    <div className="file-meta">
                      {file.category} · {formatSize(file.size)}
                    </div>
                  </div>
                </div>
                <div className="file-actions">
                  <button onClick={() => handlePreview(file)} title="预览">👁️</button>
                  <button onClick={() => handleDownload(file)} title="下载">💾</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 预览模态框 */}
      {previewContent !== null && (
        <div className="preview-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h4>预览: {previewTitle}</h4>
              <button onClick={() => setPreviewContent(null)}>❌</button>
            </div>
            <div className="modal-body">
              {previewTitle.endsWith('.md') ? (
                <div className="markdown-preview">
                  {previewContent.split('\n').map((line, i) => {
                    // 1. 处理标题
                    if (line.startsWith('# ')) return <h1 key={i}>{line.substring(2)}</h1>;
                    if (line.startsWith('## ')) return <h2 key={i}>{line.substring(3)}</h2>;
                    if (line.startsWith('### ')) return <h3 key={i}>{line.substring(4)}</h3>;
                    
                    // 2. 处理列表
                    if (line.startsWith('- ')) return <li key={i}>{line.substring(2)}</li>;
                    
                    // 3. 处理分隔线
                    if (line.trim() === '---' || line.trim() === '***') return <hr key={i} />;
                    
                    // 4. 处理空行
                    if (line.trim() === '') return <br key={i} />;
                    
                    // 5. 处理加粗 (简单正则替换)
                    const parts = line.split(/(\*\*.*?\*\*)/g);
                    return (
                      <p key={i}>
                        {parts.map((part, j) => {
                          if (part.startsWith('**') && part.endsWith('**')) {
                            return <strong key={j}>{part.slice(2, -2)}</strong>;
                          }
                          return part;
                        })}
                      </p>
                    );
                  })}
                </div>
              ) : (
                <DataPreview content={previewContent} title={previewTitle} />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
