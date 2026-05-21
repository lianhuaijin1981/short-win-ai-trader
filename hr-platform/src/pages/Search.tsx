import React, { useState } from 'react';
import { Card, Table, Tag, Space, Button, Modal, Form, Input, Select, Descriptions, Steps } from 'antd';
import { PlusOutlined, SearchOutlined, EyeOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { mockSearchAssignments, mockSearchRecords, mockClients } from '@/data/mockData';
import type { SearchAssignment, SearchRecord } from '@/types';
import { useEdition } from '@/contexts/EditionContext';

const SearchPage: React.FC = () => {
  const { hasFeature } = useEdition();
  const [assignmentVisible, setAssignmentVisible] = useState(false);

  const statusMap: Record<string, { color: string; text: string }> = {
    assigned: { color: 'blue', text: '已分配' },
    in_progress: { color: 'orange', text: '进行中' },
    completed: { color: 'green', text: '已完成' },
    cancelled: { color: 'default', text: '已取消' },
  };

  const recordStatusMap: Record<string, { color: string; text: string }> = {
    sourced: { color: 'default', text: '已寻访' },
    contacted: { color: 'blue', text: '已联系' },
    interested: { color: 'cyan', text: '有意向' },
    submitted: { color: 'orange', text: '已推荐' },
    interviewing: { color: 'purple', text: '面试中' },
    offered: { color: 'green', text: '已发Offer' },
    placed: { color: 'success', text: '已入职' },
    rejected: { color: 'red', text: '已拒绝' },
  };

  const assignmentColumns: ColumnsType<SearchAssignment> = [
    { title: '客户', dataIndex: 'clientId', key: 'clientId', render: (id: string) => mockClients.find(c => c.id === id)?.name || id },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={statusMap[s]?.color}>{statusMap[s]?.text}</Tag> },
    { title: '目标人数', dataIndex: 'targetCount', key: 'targetCount' },
    { title: '已推荐', dataIndex: 'submittedCount', key: 'submittedCount' },
    { title: '面试中', dataIndex: 'interviewCount', key: 'interviewCount' },
    { title: '已入职', dataIndex: 'placedCount', key: 'placedCount' },
    { title: '截止日期', dataIndex: 'deadline', key: 'deadline' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: SearchAssignment) => (
        <Button type="link" icon={<EyeOutlined />}>详情</Button>
      ),
    },
  ];

  const recordColumns: ColumnsType<SearchRecord> = [
    { title: '候选人', dataIndex: 'talentId', key: 'talentId' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (s: string) => <Tag color={recordStatusMap[s]?.color}>{recordStatusMap[s]?.text}</Tag>,
    },
    { title: '推荐日期', dataIndex: 'submitDate', key: 'submitDate' },
    { title: '备注', dataIndex: 'notes', key: 'notes' },
  ];

  if (!hasFeature('searchScriptGeneration')) {
    return (
      <div>
        <h2>人才寻访</h2>
        <Card>
          <p>此功能仅在旗舰版中可用</p>
          <p>旗舰版专属功能：人才寻访、客户管理、猎头业务全流程管理</p>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <h2>人才寻访</h2>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setAssignmentVisible(true)}>创建寻访任务</Button>
          <Button icon={<SearchOutlined />}>人才搜索</Button>
        </Space>

        <h3>寻访任务</h3>
        <Table columns={assignmentColumns} dataSource={mockSearchAssignments} rowKey="id" pagination={false} style={{ marginBottom: 16 }} />

        <h3>候选人跟进</h3>
        <Table columns={recordColumns} dataSource={mockSearchRecords} rowKey="id" pagination={false} />
      </Card>

      <Modal
        title="创建寻访任务"
        open={assignmentVisible}
        onCancel={() => setAssignmentVisible(false)}
        onOk={() => setAssignmentVisible(false)}
      >
        <Form layout="vertical">
          <Form.Item label="客户企业">
            <Select placeholder="选择客户">
              {mockClients.map(c => <Select.Option key={c.id} value={c.id}>{c.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item label="目标人数">
            <Input type="number" />
          </Form.Item>
          <Form.Item label="截止日期">
            <Input type="date" />
          </Form.Item>
          <Form.Item label="寻访顾问">
            <Select placeholder="选择顾问">
              <Select.Option value="consultant_001">顾问A</Select.Option>
              <Select.Option value="consultant_002">顾问B</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SearchPage;