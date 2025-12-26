/**
 * EasySTAT 数据预览组件
 * 
 * 主要功能：
 * - 智能识别 JSON 数据格式
 * - 将金融数据（如资金流、K线）渲染为三线表
 * - 对数值进行格式化（亿/万单位）和颜色编码（红涨绿跌）
 * - 提供原始数据查看的切换功能
 */

import { useState, useMemo } from 'react';

interface DataPreviewProps {
  /** 文件内容字符串 */
  content: string;
  /** 文件标题（文件名） */
  title: string;
}

/**
 * 格式化大额数字
 * @param num 原始数值
 * @returns 格式化后的字符串 (如 1.5亿)
 */
const formatNumber = (num: number): string => {
  if (Math.abs(num) >= 100000000) {
    return (num / 100000000).toFixed(2) + '亿';
  }
  if (Math.abs(num) >= 10000) {
    return (num / 10000).toFixed(2) + '万';
  }
  return num.toFixed(2);
};

/**
 * 获取数值的颜色样式
 * @param value 数值
 * @param isPercentage 是否为百分比字段
 * @returns CSS颜色值 (红色: >0, 绿色: <0, 灰色: 0)
 */
const getValueColor = (value: number): string => {
  if (value > 0) return '#ff3333'; // 红色 (涨/流入)
  if (value < 0) return '#00cc00'; // 绿色 (跌/流出)
  return '#888';
};

export function DataPreview({ content, title }: DataPreviewProps) {
  const [showRaw, setShowRaw] = useState(false);

  // 解析并缓存数据
  const parsedData = useMemo(() => {
    try {
      const data = JSON.parse(content);
      // 必须是数组且长度大于0
      if (Array.isArray(data) && data.length > 0) {
        return data; 
      }
      return null;
    } catch (e) {
      return null;
    }
  }, [content]);

  // 判断是否为支持的金融数据表格式
  const tableConfig = useMemo(() => {
    if (!parsedData) return null;
    
    const firstRow = parsedData[0];
    
    // 策略1: 资金流数据 (包含 main_flow_net_amount)
    if ('main_flow_net_amount' in firstRow) {
      return {
        type: 'flow',
        columns: [
          { key: 'code', label: '代码' },
          { key: 'name', label: '名称' },
          { key: 'latest_price', label: '最新价', format: 'price' },
          { key: 'change_percentage', label: '涨跌幅', format: 'percent' },
          { key: 'main_flow_net_amount', label: '主力净流入', format: 'amount' },
        ]
      };
    }

    // 策略2: K线数据 (包含 Open, Close, High, Low)
    if ('Open' in firstRow && 'Close' in firstRow) {
        return {
          type: 'ohlcv',
          columns: [
            { key: 'Date', label: '日期' },
            { key: 'Open', label: '开盘' },
            { key: 'Close', label: '收盘' },
            { key: 'High', label: '最高' },
            { key: 'Low', label: '最低' },
            { key: 'PriceChange', label: '涨跌额', format: 'diff' },
            { key: 'QuoteChange', label: '涨跌幅', format: 'percent' },
            { key: 'Volume', label: '成交量' },
          ]
        };
      }

    return null; // 无法识别的表格格式
  }, [parsedData]);

  // 如果无法解析为表格，或用户选择看原始代码
  if (!parsedData || !tableConfig || showRaw) {
    return (
      <div className="preview-container">
        {tableConfig && (
          <div className="preview-toolbar">
            <button onClick={() => setShowRaw(false)}>🔙 返回表格视图</button>
          </div>
        )}
        <pre className="raw-content">
            {content}
        </pre>
      </div>
    );
  }

  return (
    <div className="preview-container">
      <div className="preview-toolbar" style={{ marginBottom: '10px', display: 'flex', justifyContent: 'flex-end' }}>
        <button onClick={() => setShowRaw(true)} style={{ fontSize: '0.8em', padding: '4px 8px' }}>
          查看原始 JSON
        </button>
      </div>

      <div className="data-table-wrapper" style={{ overflowX: 'auto' }}>
        <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #444', color: '#ccc', textAlign: 'left' }}>
              {tableConfig.columns.map(col => (
                <th key={col.key} style={{ padding: '8px' }}>{col.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {parsedData.map((row: any, i: number) => (
              <tr key={i} style={{ borderBottom: '1px solid #333' }}>
                {tableConfig.columns.map(col => {
                  const val = row[col.key];
                  let displayVal = val;
                  let color = 'inherit';

                  // 格式化处理
                  if (typeof val === 'number') {
                    if (col.format === 'amount') {
                        displayVal = formatNumber(val);
                        color = getValueColor(val);
                    } else if (col.format === 'percent') {
                        displayVal = val.toFixed(2) + '%';
                        color = getValueColor(val);
                    } else if (col.format === 'diff') {
                        displayVal = val.toFixed(2);
                        color = getValueColor(val);
                    } else if (col.format === 'price') {
                        displayVal = val.toFixed(2);
                        // 价格本身如果是红的，通常取决于涨跌幅，这里简单处理，或者不标色
                    }
                  }

                  return (
                    <td key={col.key} style={{ padding: '8px', color }}>
                      {displayVal}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
