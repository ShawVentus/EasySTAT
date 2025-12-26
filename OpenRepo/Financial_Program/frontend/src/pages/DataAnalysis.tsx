import React, { useState } from 'react';
import { Card, Input, Button, message, Table, Descriptions, Spin, Row, Col, Statistic } from 'antd';
import axios from 'axios';

const DataAnalysis: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!query.trim()) {
      message.warning('请输入分析目标，例如：分析贵州茅台');
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post('/api/crew/analyze', { query });
      if (res.data.success) {
        setResult(res.data);
        message.success('分析完成');
      } else {
        message.error('分析失败: ' + (res.data.error || '未知错误'));
      }
    } catch (e) {
      message.error('请求失败，请检查网络或后端服务');
    }
    setLoading(false);
  };

  // 资金流表格列定义
  const flowColumns = [
    { title: '代码', dataIndex: 'code', key: 'code' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '最新价', dataIndex: 'latest_price', key: 'latest_price' },
    { 
      title: '涨跌幅', 
      dataIndex: 'change_percentage', 
      key: 'change_percentage',
      render: (val: number) => (
        <span style={{ color: val >= 0 ? 'red' : 'green' }}>
          {val}%
        </span>
      )
    },
    { title: '主力净流入', dataIndex: 'main_flow_net_amount', key: 'main_flow_net_amount' },
  ];

  return (
    <div style={{ padding: '24px', maxWidth: 1200, margin: '0 auto' }}>
      <Card title="智能数据分析" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 16 }}>
          <Input 
            placeholder="请输入股票名称或代码，例如：分析贵州茅台" 
            value={query}
            onChange={e => setQuery(e.target.value)}
            onPressEnter={handleAnalyze}
            style={{ width: 400 }}
          />
          <Button type="primary" onClick={handleAnalyze} loading={loading}>
            开始分析
          </Button>
        </div>
      </Card>

      {loading && (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <Spin size="large" tip="多智能体团队正在协作分析中，请稍候..." />
        </div>
      )}

      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* 综合报告 */}
          <Card title="综合分析报告">
            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: 16, lineHeight: 1.6 }}>
              {result.report}
            </pre>
          </Card>

          {/* 技术指标 */}
          {result.data?.technical_indicators && Object.keys(result.data.technical_indicators).length > 0 && (
            <Card title="技术指标详情">
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic title="RSI (相对强弱指标)" value={result.data.technical_indicators.rsi || '-'} precision={2} />
                </Col>
                <Col span={8}>
                  <Statistic title="MACD" value={result.data.technical_indicators.macd || '-'} precision={4} />
                </Col>
                <Col span={8}>
                  <Statistic title="布林带上轨" value={result.data.technical_indicators.bollinger_hband || '-'} precision={2} />
                </Col>
              </Row>
            </Card>
          )}

          {/* 资金流数据 */}
          {result.data?.capital_flow && result.data.capital_flow.length > 0 && (
            <Card title="相关资金流数据">
              <Table 
                dataSource={result.data.capital_flow} 
                columns={flowColumns} 
                rowKey="code"
                pagination={false}
                size="small"
              />
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default DataAnalysis;
