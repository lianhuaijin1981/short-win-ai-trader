import React, { useState } from 'react';
import { Card, Table, Tag, Space, Button, Upload, message, Modal, Form, Input, Select } from 'antd';
import { UploadOutlined, FileTextOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { mockResumes } from '@/data/mockData';
import type { ResumeParsed } from '@/types';
import { useEdition } from '@/contexts/EditionContext';

const { TextArea } = Input;

const ResumePage: React.FC = () => {
  const { hasFeature } = useEdition();
  const [uploadVisible, setUploadVisible] = useState(false);

  const jobStatusMap: Record<string, { color: string; text: string }> = {
    employed: { color: 'blue', text: '在职' },
    unemployed: { color: 'orange', text: '离职' },
    looking: { color: 'green', text: '求职中' },
  };

  const columns: ColumnsType<ResumeParsed> = [
    { title: '姓名', dataIndex: ['basic', 'name'], key: 'name' },
    { title: '年龄', dataIndex: ['basic', 'age'], key: 'age' },
    { title: '地点', dataIndex: ['basic', 'location'], key: 'location' },
    {
      title: '求职状态',
      dataIndex: 'jobStatus',
      key: 'jobStatus',
      render: (status?: string) => status ? (
        <Tag color={jobStatusMap[status]?.color}>{jobStatusMap[status]?.text}</Tag>
      ) : '-',
    },
    {
      title: '期望薪资',
      dataIndex: 'expectedSalary',
      key: 'expectedSalary',
      render: (salary?: { min: number; max: number }) => salary ? `${salary.min}-${salary.max}` : '-',
    },
    {
      title: '技能',
      dataIndex: 'skills',
      key: 'skills',
      render: (skills: string[]) => (
        <Space wrap>
          {skills.slice(0, 3).map(skill => <Tag key={skill}>{skill}</Tag>)}
          {skills.length > 3 && <Tag>+{skills.length - 3}</Tag>}
        </Space>
      ),
    },
    { title: '来源', dataIndex: 'source', key: 'source' },
    { title: '更新时间', dataIndex: 'updatedAt', key: 'updatedAt' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ResumeParsed) => (
        <Space>
          <Button type="link" icon={<FileTextOutlined />}>查看</Button>
          <Button type="link" icon={<EditOutlined />}>编辑</Button>
          <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
        </Space>
      ),
    },
  ];

  const handleUpload = () => {
    message.success('简历解析成功');
    setUploadVisible(false);
  };

  return (
    <div>
      <h2>简历管理</h2>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Upload
            accept=".pdf,.doc,.docx"
            showUploadList={false}
            beforeUpload={() => {
              setUploadVisible(true);
              return false;
            }}
          >
            <Button type="primary" icon={<UploadOutlined />}>上传简历</Button>
          </Upload>
          {hasFeature('aiMatching') && (
            <Button>AI智能解析</Button>
          )}
        </Space>

        <Table
          columns={columns}
          dataSource={mockResumes}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="上传简历"
        open={uploadVisible}
        onCancel={() => setUploadVisible(false)}
        onOk={handleUpload}
      >
        <Form layout="vertical">
          <Form.Item label="选择简历文件">
            <Upload.Dragger accept=".pdf,.doc,.docx">
              <p>点击或拖拽文件到此区域</p>
              <p>支持 PDF、Word 格式</p>
            </Upload.Dragger>
          </Form.Item>
          <Form.Item label="来源渠道">
            <Select placeholder="选择来源">
              <Select.Option value="boss">BOSS直聘</Select.Option>
              <Select.Option value="liepin">猎聘</Select.Option>
              <Select.Option value="referral">内部推荐</Select.Option>
              <Select.Option value="other">其他</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ResumePage;