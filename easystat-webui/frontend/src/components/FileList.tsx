/**
 * EasySTAT WebUI 前端 - 文件列表组件
 * 
 * 主要功能：
 * - 显示 CrewAI 执行过程中生成的文件列表
 * - 提供可视化的文件图标和布局
 */

/**
 * 组件属性接口
 */
interface FileListProps {
  /** 文件路径列表 */
  files: string[];
}

/**
 * 根据文件扩展名获取图标
 * 
 * @param filename 文件名
 * @returns 对应的 Emoji 图标
 */
function getFileIcon(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || '';
  
  switch (ext) {
    case 'md':
      return '📄';
    case 'html':
      return '🌐';
    case 'json':
      return '📊';
    case 'csv':
      return '📈';
    case 'png':
    case 'jpg':
    case 'jpeg':
      return '🖼️';
    case 'pdf':
      return '📕';
    default:
      return '📄';
  }
}

/**
 * 文件列表组件
 * 
 * 显示本次执行生成的所有文件。
 * 
 * @param props 组件属性
 * @returns React 组件
 */
export function FileList({ files }: FileListProps) {
  if (files.length === 0) {
    return null; // 无文件时不显示
  }

  return (
    <div className="file-list">
      <h3>📁 生成的文件 ({files.length})</h3>
      <ul>
        {files.map((file) => (
          <li key={file} className="file-item">
            <span className="file-icon">{getFileIcon(file)}</span>
            <span className="file-name">{file}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
