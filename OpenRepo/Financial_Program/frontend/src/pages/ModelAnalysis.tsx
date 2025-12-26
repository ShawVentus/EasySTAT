import React, { useState } from 'react';
import { Card, Input, Button, message, Descriptions, Spin, Statistic, Row, Col } from 'antd';
import axios from 'axios';

const ModelAnalysis: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!query.trim()) {
      message.warning('请输入分析目标，例如：分析贵州茅台的波动率');
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const res = await axios.post('/api/crew/analyze', { query });
      if (res.data.success) {
        setResult(res.data);
        message.success('建模分析完成');
      } else {
        message.error('分析失败: ' + (res.data.error || '未知错误'));
      }
    } catch (e) {
      message.error('请求失败，请检查网络或后端服务');
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '24px', maxWidth: 1200, margin: '0 auto' }}>
      <Card title="风险建模分析" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 16 }}>
          <Input 
            placeholder="请输入股票名称或代码，例如：分析贵州茅台的风险" 
            value={query}
            onChange={e => setQuery(e.target.value)}
            onPressEnter={handleAnalyze}
            style={{ width: 400 }}
          />
          <Button type="primary" onClick={handleAnalyze} loading={loading}>
            开始建模
          </Button>
        </div>
      </Card>

      {loading && (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <Spin size="large" tip="正在进行 GARCH 波动率建模，请稍候..." />
        </div>
      )}

      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* 综合报告 */}
          <Card title="风险评估报告">
            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: 16, lineHeight: 1.6 }}>
              {result.report}
            </pre>
          </Card>

          {/* 波动率模型数据 */}
          {result.data?.volatility_data && Object.keys(result.data.volatility_data).length > 0 && (
            <Card title="GARCH 模型参数与结果">
              <Row gutter={24}>
                <Col span={6}>
                  <Statistic 
                    title="条件波动率 (Conditional Volatility)" 
                    value={result.data.volatility_data.conditional_volatility || '-'} 
                    precision={4} 
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic title="Omega" value={result.data.volatility_data.omega || '-'} precision={6} />
                </Col>
                <Col span={6}>
                  <Statistic title="Alpha" value={result.data.volatility_data.alpha || '-'} precision={6} />
                </Col>
                <Col span={6}>
                  <Statistic title="Beta" value={result.data.volatility_data.beta || '-'} precision={6} />
                </Col>
              </Row>
              <div style={{ marginTop: 24 }}>
                <Descriptions title="模型统计摘要" bordered column={1}>
                  <Descriptions.Item label="Log Likelihood">
                    {result.data.volatility_data.log_likelihood || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="Summary">
                    <pre style={{ fontSize: 12 }}>{result.data.volatility_data.summary || '无摘要数据'}</pre>
                  </Descriptions.Item>
                </Descriptions>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default ModelAnalysis;
