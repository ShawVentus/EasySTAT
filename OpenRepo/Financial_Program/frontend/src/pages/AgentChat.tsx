/**
 * AgentChat - CrewAI 多智能体对话界面
 * 
 * 三栏布局：
 * - 左侧：历史对话记录
 * - 中间：当前对话区域（支持 Markdown 渲染）
 * - 右侧：处理流程步骤
 */
import React, { useState, useEffect, useRef } from 'react';
import { Card, Input, Button, List, message, Spin, Steps, Typography, Empty } from 'antd';
import { SendOutlined, DeleteOutlined, RobotOutlined, UserOutlined, CheckCircleOutlined, LoadingOutlined, ClockCircleOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';

const { Text, Title } = Typography;

// 历史对话存储 Key
const HISTORY_KEY = 'agent_chat_history';

// 事件类型定义
interface ChatEvent {
  type: 'start' | 'agent_start' | 'task_start' | 'tool_call' | 'task_complete' | 'thinking' | 'final_answer' | 'report' | 'error' | 'done' | 'heartbeat';
  message?: string;
  agent?: string;
  task?: string;
  tool?: string;
  content?: string;
  data?: any;
}

// 对话消息
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

// 历史会话
interface ChatSession {
  id: string;
  query: string;
  timestamp: string;
  messages: ChatMessage[];
}

// 处理步骤
interface ProcessStep {
  title: string;
  description?: string;
  status: 'wait' | 'process' | 'finish' | 'error';
}

const AgentChat: React.FC = () => {
  // 状态
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [steps, setSteps] = useState<ProcessStep[]>([]);
  const [loading, setLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [history, setHistory] = useState<ChatSession[]>(() => {
    const saved = localStorage.getItem(HISTORY_KEY);
    return saved ? JSON.parse(saved) : [];
  });
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  // 保存历史
  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  }, [history]);

  // 发送消息
  const handleSend = async () => {
    if (!input.trim()) {
      message.warning('请输入分析内容');
      return;
    }

    const query = input.trim();
    setInput('');
    setLoading(true);
    setStreamingContent('');
    
    // 添加用户消息
    const userMessage: ChatMessage = {
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleString('zh-CN')
    };
    setMessages(prev => [...prev, userMessage]);

    // 初始化步骤
    setSteps([
      { title: '开始分析', status: 'process' }
    ]);

    try {
      // 调用 SSE 流式 API
      const response = await fetch('/api/crew/analyze/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });

      if (!response.ok) {
        throw new Error('请求失败');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let finalReport = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') continue;

              try {
                const event: ChatEvent = JSON.parse(data);
                handleEvent(event);

                // 收集最终报告
                if (event.type === 'report' && event.content) {
                  finalReport = event.content;
                  setStreamingContent(finalReport);
                }
              } catch {
                // 忽略解析错误
              }
            }
          }
        }
      }

      // 完成后添加助手消息
      if (finalReport) {
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: finalReport,
          timestamp: new Date().toLocaleString('zh-CN')
        };
        
        // 使用函数式更新解决闭包问题
        setMessages(prev => {
          const newMessages = [...prev, assistantMessage];
          
          // 保存到历史
          const sessionId = Date.now().toString();
          const session: ChatSession = {
            id: sessionId,
            query: query,
            timestamp: new Date().toLocaleString('zh-CN'),
            messages: newMessages
          };
          setHistory(prevHistory => [session, ...prevHistory.slice(0, 19)]); // 最多保留20条
          setCurrentSessionId(sessionId);
          
          return newMessages;
        });
        setStreamingContent('');
      }

    } catch (e: any) {
      message.error(`分析失败: ${e.message}`);
      setSteps(prev => [
        ...prev,
        { title: '分析失败', description: e.message, status: 'error' }
      ]);
    }

    setLoading(false);
  };

  // 处理 SSE 事件
  const handleEvent = (event: ChatEvent) => {
    switch (event.type) {
      case 'start':
        setSteps([{ title: '开始分析', description: event.message, status: 'finish' }]);
        break;

      case 'agent_start':
        setSteps(prev => [
          ...prev.map(s => ({ ...s, status: 'finish' as const })),
          { title: `Agent: ${event.agent}`, status: 'process' }
        ]);
        break;

      case 'task_start':
        setSteps(prev => [
          ...prev.map(s => ({ ...s, status: 'finish' as const })),
          { title: event.task || '执行任务', status: 'process' }
        ]);
        break;

      case 'tool_call':
        setSteps(prev => [
          ...prev,
          { title: `使用工具: ${event.tool}`, status: 'process' }
        ]);
        break;

      case 'task_complete':
        setSteps(prev => prev.map((s, i) => 
          i === prev.length - 1 ? { ...s, status: 'finish' } : s
        ));
        break;

      case 'thinking':
        // 更新最后一个步骤的描述
        setSteps(prev => prev.map((s, i) => 
          i === prev.length - 1 ? { ...s, description: '思考中...' } : s
        ));
        break;

      case 'report':
        setSteps(prev => [
          ...prev.map(s => ({ ...s, status: 'finish' as const })),
          { title: '报告生成完成', status: 'finish' }
        ]);
        break;

      case 'error':
        setSteps(prev => [
          ...prev,
          { title: '错误', description: event.message, status: 'error' }
        ]);
        break;

      case 'done':
        setSteps(prev => prev.map(s => ({ ...s, status: 'finish' as const })));
        break;
    }
  };

  // 加载历史会话
  const loadSession = (session: ChatSession) => {
    setMessages(session.messages);
    setCurrentSessionId(session.id);
    setSteps([]);
  };

  // 清空历史
  const clearHistory = () => {
    setHistory([]);
    setMessages([]);
    setSteps([]);
    setCurrentSessionId(null);
    localStorage.removeItem(HISTORY_KEY);
    message.success('历史已清空');
  };

  // 新建对话
  const newChat = () => {
    setMessages([]);
    setSteps([]);
    setStreamingContent('');
    setCurrentSessionId(null);
  };

  // 渲染步骤图标
  const getStepIcon = (status: string) => {
    switch (status) {
      case 'finish': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'process': return <LoadingOutlined style={{ color: '#1890ff' }} />;
      case 'error': return <ClockCircleOutlined style={{ color: '#ff4d4f' }} />;
      default: return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 64px)', background: '#f5f5f5' }}>
      {/* 左侧：历史记录 */}
      <div style={{ 
        width: 240, 
        background: '#fff', 
        borderRight: '1px solid #e8e8e8',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{ padding: 16, borderBottom: '1px solid #e8e8e8' }}>
          <Button type="primary" block onClick={newChat}>
            新建对话
          </Button>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: 8 }}>
          {history.length === 0 ? (
            <Empty description="暂无历史" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <List
              size="small"
              dataSource={history}
              renderItem={item => (
                <List.Item
                  style={{ 
                    cursor: 'pointer', 
                    padding: '8px 12px',
                    borderRadius: 6,
                    marginBottom: 4,
                    background: currentSessionId === item.id ? '#e6f7ff' : 'transparent'
                  }}
                  onClick={() => loadSession(item)}
                >
                  <div style={{ width: '100%' }}>
                    <Text ellipsis style={{ display: 'block', fontWeight: 500 }}>
                      {item.query}
                    </Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.timestamp}
                    </Text>
                  </div>
                </List.Item>
              )}
            />
          )}
        </div>
        <div style={{ padding: 16, borderTop: '1px solid #e8e8e8' }}>
          <Button danger block icon={<DeleteOutlined />} onClick={clearHistory}>
            清空历史
          </Button>
        </div>
      </div>

      {/* 中间：对话区域 */}
      <div style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column',
        background: '#fff'
      }}>
        <div style={{ 
          padding: 16, 
          borderBottom: '1px solid #e8e8e8',
          background: '#fafafa'
        }}>
          <Title level={4} style={{ margin: 0 }}>
            <RobotOutlined style={{ marginRight: 8 }} />
            多智能体金融分析
          </Title>
        </div>

        {/* 消息列表 */}
        <div style={{ 
          flex: 1, 
          overflow: 'auto', 
          padding: 16 
        }}>
          {messages.length === 0 && !streamingContent ? (
            <div style={{ 
              height: '100%', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              flexDirection: 'column'
            }}>
              <RobotOutlined style={{ fontSize: 64, color: '#d9d9d9', marginBottom: 16 }} />
              <Text type="secondary">输入自然语言开始分析，如："分析工业富联的资金流情况"</Text>
            </div>
          ) : (
            <>
              {messages.map((msg, index) => (
                <div 
                  key={index}
                  style={{ 
                    marginBottom: 16,
                    display: 'flex',
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                  }}
                >
                  <Card
                    size="small"
                    style={{ 
                      maxWidth: '80%',
                      background: msg.role === 'user' ? '#1890ff' : '#f5f5f5',
                      color: msg.role === 'user' ? '#fff' : '#000'
                    }}
                    bodyStyle={{ padding: '12px 16px' }}
                  >
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      marginBottom: 8 
                    }}>
                      {msg.role === 'user' ? (
                        <UserOutlined style={{ marginRight: 8 }} />
                      ) : (
                        <RobotOutlined style={{ marginRight: 8 }} />
                      )}
                      <Text 
                        type="secondary" 
                        style={{ 
                          fontSize: 12,
                          color: msg.role === 'user' ? 'rgba(255,255,255,0.8)' : undefined
                        }}
                      >
                        {msg.role === 'user' ? '你' : 'AI'} · {msg.timestamp}
                      </Text>
                    </div>
                    {msg.role === 'assistant' ? (
                      <div className="markdown-body" style={{ color: '#000' }}>
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <Text style={{ color: '#fff' }}>{msg.content}</Text>
                    )}
                  </Card>
                </div>
              ))}

              {/* 流式输出中 */}
              {streamingContent && (
                <div style={{ marginBottom: 16 }}>
                  <Card
                    size="small"
                    style={{ maxWidth: '80%', background: '#f5f5f5' }}
                    bodyStyle={{ padding: '12px 16px' }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                      <RobotOutlined style={{ marginRight: 8 }} />
                      <Text type="secondary" style={{ fontSize: 12 }}>AI · 正在生成...</Text>
                      <Spin size="small" style={{ marginLeft: 8 }} />
                    </div>
                    <div className="markdown-body">
                      <ReactMarkdown>{streamingContent}</ReactMarkdown>
                    </div>
                  </Card>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* 输入框 */}
        <div style={{ 
          padding: 16, 
          borderTop: '1px solid #e8e8e8',
          background: '#fafafa'
        }}>
          <Input.Search
            value={input}
            onChange={e => setInput(e.target.value)}
            onSearch={handleSend}
            enterButton={
              <Button type="primary" icon={<SendOutlined />} loading={loading}>
                发送
              </Button>
            }
            placeholder="输入分析内容，如：分析贵州茅台的资金流情况"
            size="large"
            disabled={loading}
          />
        </div>
      </div>

      {/* 右侧：处理流程 */}
      <div style={{ 
        width: 300, 
        background: '#fff', 
        borderLeft: '1px solid #e8e8e8',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{ 
          padding: 16, 
          borderBottom: '1px solid #e8e8e8',
          background: '#fafafa'
        }}>
          <Title level={5} style={{ margin: 0 }}>处理流程</Title>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
          {steps.length === 0 ? (
            <Empty description="等待分析" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <Steps
              direction="vertical"
              size="small"
              current={steps.findIndex(s => s.status === 'process')}
              items={steps.map(step => ({
                title: step.title,
                description: step.description,
                icon: getStepIcon(step.status),
                status: step.status
              }))}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentChat;
