import React, { useState } from 'react';
import { Card, Table, Tag, Space, Button, Modal, Form, Input, DatePicker, TimePicker, Select, Descriptions } from 'antd';
import { PlusOutlined, CalendarOutlined, EditOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { mockInterviews, mockAIQuestions } from '@/data/mockData';
import type { Interview } from '@/types';
import { useEdition } from '@/contexts/EditionContext';
import dayjs from 'dayjs';

const InterviewPage: React.FC = () => {
  const { hasFeature } = useEdition();
  const [interviewVisible, setInterviewVisible] = useState(false);
  const [questionsVisible, setQuestionsVisible] = useState(false);

  const statusMap: Record<string, { color: string; text: string }> = {
    scheduled: { color: 'blue', text: '待面试' },
    completed: { color: 'green', text: '已完成' },
    cancelled: { color: 'default', text: '已取消' },
    no_show: { color: 'red', text: '未到' },
  };

  const columns: ColumnsType<Interview> = [
    { title: '候选人', dataIndex: 'talentId', key: 'talentId' },
    { title: '面试轮次', dataIndex: 'round', key: 'round', render: (r: number) => `第${r}轮` },
    { title: '日期', dataIndex: 'date', key: 'date' },
    { title: '时间', dataIndex: 'time', key: 'time' },
    { title: '地点', dataIndex: 'location', key: 'location' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <Tag color={statusMap[status]?.color}>{statusMap[status]?.text}</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Interview) => (
        <Space>
          <Button type="link" icon={<EditOutlined />}>反馈</Button>
          {hasFeature('interviewQuestions') && (
            <Button type="link" icon={<CalendarOutlined />} onClick={() => setQuestionsVisible(true)}>AI面经</Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2>面试管理</h2>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setInterviewVisible(true)}>安排面试</Button>
        </Space>

        <Table columns={columns} dataSource={mockInterviews} rowKey="id" pagination={{ pageSize: 10 }} />
      </Card>

      <Modal
        title="安排面试"
        open={interviewVisible}
        onCancel={() => setInterviewVisible(false)}
        onOk={() => setInterviewVisible(false)}
      >
        <Form layout="vertical">
          <Form.Item label="候选人">
            <Select placeholder="选择候选人">
              <Select.Option value="resume_001">张伟</Select.Option>
              <Select.Option value="resume_002">李娜</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="面试轮次">
            <Select>
              <Select.Option value={1}>初试</Select.Option>
              <Select.Option value={2}>复试</Select.Option>
              <Select.Option value={3}>终试</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="面试日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="面试时间">
            <TimePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="面试地点">
            <Input />
          </Form.Item>
          <Form.Item label="面试官">
            <Select mode="multiple" placeholder="选择面试官">
              <Select.Option value="emp_010">面试官A</Select.Option>
              <Select.Option value="emp_011">面试官B</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="AI面试问题推荐"
        open={questionsVisible}
        onCancel={() => setQuestionsVisible(false)}
        footer={null}
        width={700}
      >
        <Descriptions title="岗位: 高级前端工程师" style={{ marginBottom: 16 }} />
        <h4>通用问题</h4>
        <ul>
          {mockAIQuestions.general.map((q, i) => <li key={i}>{q}</li>)}
        </ul>
        <h4>技术问题</h4>
        <ul>
          {mockAIQuestions.technical.map((q, i) => <li key={i}>{q}</li>)}
        </ul>
        <h4>行为问题</h4>
        <ul>
          {mockAIQuestions.behavioral.map((q, i) => <li key={i}>{q}</li>)}
        </ul>
        <h4>文化匹配</h4>
        <ul>
          {mockAIQuestions.cultureFit.map((q, i) => <li key={i}>{q}</li>)}
        </ul>
      </Modal>
    </div>
  );
};

export default InterviewPage;