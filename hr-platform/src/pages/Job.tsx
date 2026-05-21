import React, { useState } from 'react';
import { Card, Table, Tag, Space, Button, Modal, Form, Input, Select, Descriptions } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, RobotOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { mockJobs, mockAIJD, mockAIMatches } from '@/data/mockData';
import type { JobPosition } from '@/types';
import { useEdition } from '@/contexts/EditionContext';

const JobPage: React.FC = () => {
  const { hasFeature } = useEdition();
  const [jobVisible, setJobVisible] = useState(false);
  const [jdVisible, setJdVisible] = useState(false);
  const [selectedJob, setSelectedJob] = useState<JobPosition | null>(null);

  const statusMap: Record<string, { color: string; text: string }> = {
    open: { color: 'green', text: '招聘中' },
    closed: { color: 'default', text: '已关闭' },
    on_hold: { color: 'orange', text: '暂停' },
  };

  const priorityMap: Record<string, { color: string; text: string }> = {
    low: { color: 'default', text: '低' },
    medium: { color: 'blue', text: '中' },
    high: { color: 'orange', text: '高' },
    urgent: { color: 'red', text: '紧急' },
  };

  const columns: ColumnsType<JobPosition> = [
    { title: '职位名称', dataIndex: 'title', key: 'title' },
    { title: '部门', dataIndex: 'department', key: 'department' },
    { title: '地点', dataIndex: 'location', key: 'location' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <Tag color={statusMap[status]?.color}>{statusMap[status]?.text}</Tag>,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => <Tag color={priorityMap[priority]?.color}>{priorityMap[priority]?.text}</Tag>,
    },
    {
      title: '编制',
      key: 'headcount',
      render: (_, record: JobPosition) => `${record.currentHeadcount}/${record.headcount}`,
    },
    {
      title: '薪资范围',
      dataIndex: 'salaryRange',
      key: 'salaryRange',
      render: (range?: { min: number; max: number }) => range ? `${range.min}-${range.max}` : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: JobPosition) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />} onClick={() => { setSelectedJob(record); setJdVisible(true); }}>详情</Button>
          <Button type="link" icon={<EditOutlined />}>编辑</Button>
          <Button type="link" danger icon={<DeleteOutlined />}>关闭</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2>职位管理</h2>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setJobVisible(true)}>发布职位</Button>
          {hasFeature('jdGeneration') && (
            <Button type="primary" icon={<RobotOutlined />}>AI生成JD</Button>
          )}
        </Space>

        <Table columns={columns} dataSource={mockJobs} rowKey="id" pagination={{ pageSize: 10 }} />
      </Card>

      <Modal
        title="发布职位"
        open={jobVisible}
        onCancel={() => setJobVisible(false)}
        onOk={() => setJobVisible(false)}
      >
        <Form layout="vertical">
          <Form.Item label="职位名称" rules={[{ required: true, message: '请输入职位名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="部门">
            <Select>
              <Select.Option value="技术部">技术部</Select.Option>
              <Select.Option value="产品部">产品部</Select.Option>
              <Select.Option value="运营部">运营部</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="人数">
            <Input type="number" />
          </Form.Item>
          <Form.Item label="薪资范围">
            <Input.Group compact>
              <Input style={{ width: '50%' }} placeholder="最低薪资" />
              <Input style={{ width: '50%' }} placeholder="最高薪资" />
            </Input.Group>
          </Form.Item>
          <Form.Item label="职位要求">
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="职位详情"
        open={jdVisible}
        onCancel={() => setJdVisible(false)}
        footer={null}
        width={800}
      >
        {selectedJob && (
          <>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="职位名称">{selectedJob.title}</Descriptions.Item>
              <Descriptions.Item label="部门">{selectedJob.department}</Descriptions.Item>
              <Descriptions.Item label="地点">{selectedJob.location}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusMap[selectedJob.status]?.color}>{statusMap[selectedJob.status]?.text}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="编制">{selectedJob.currentHeadcount}/{selectedJob.headcount}</Descriptions.Item>
              <Descriptions.Item label="薪资范围">
                {selectedJob.salaryRange ? `${selectedJob.salaryRange.min}-${selectedJob.salaryRange.max}` : '-'}
              </Descriptions.Item>
            </Descriptions>
            <h4 style={{ marginTop: 16 }}>职位描述</h4>
            <p>{selectedJob.description}</p>
            <h4>任职要求</h4>
            <ul>
              {selectedJob.requirements?.map((req, i) => <li key={i}>{req}</li>)}
            </ul>

            {hasFeature('aiMatching') && (
              <>
                <h4 style={{ marginTop: 16 }}>AI推荐候选人</h4>
                <Table
                  size="small"
                  columns={[
                    { title: '姓名', dataIndex: ['talentId'], key: 'talentId' },
                    { title: '匹配度', dataIndex: 'matchScore', key: 'matchScore', render: (s: number) => `${s}%` },
                    { title: '推荐等级', dataIndex: 'recommendation', key: 'recommendation' },
                  ]}
                  dataSource={mockAIMatches}
                  rowKey="talentId"
                  pagination={false}
                />
              </>
            )}
          </>
        )}
      </Modal>
    </div>
  );
};

export default JobPage;