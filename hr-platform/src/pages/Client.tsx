import React, { useState } from 'react';
import { Card, Table, Tag, Space, Button, Modal, Form, Input, Select, Descriptions } from 'antd';
import { PlusOutlined, EyeOutlined, EditOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { mockClients } from '@/data/mockData';
import type { ClientCompany } from '@/types';
import { useEdition } from '@/contexts/EditionContext';

const ClientPage: React.FC = () => {
  const { hasFeature } = useEdition();
  const [clientVisible, setClientVisible] = useState(false);

  const contractStatusMap: Record<string, { color: string; text: string }> = {
    active: { color: 'green', text: '有效' },
    expired: { color: 'red', text: '已过期' },
    pending: { color: 'orange', text: '待签约' },
  };

  const columns: ColumnsType<ClientCompany> = [
    { title: '企业名称', dataIndex: 'name', key: 'name' },
    { title: '行业', dataIndex: 'industry', key: 'industry' },
    { title: '规模', dataIndex: 'size', key: 'size' },
    { title: '联系人', dataIndex: 'contactPerson', key: 'contactPerson' },
    { title: '联系电话', dataIndex: 'contactPhone', key: 'contactPhone' },
    {
      title: '合同状态',
      dataIndex: 'contractStatus',
      key: 'contractStatus',
      render: (s: string) => <Tag color={contractStatusMap[s]?.color}>{contractStatusMap[s]?.text}</Tag>,
    },
    { title: '服务费', dataIndex: 'serviceFee', key: 'serviceFee', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    {
      title: '操作',
      key: 'action',
      render: (_: any, __: ClientCompany) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />}>详情</Button>
          <Button type="link" icon={<EditOutlined />}>编辑</Button>
        </Space>
      ),
    },
  ];

  if (!hasFeature('searchScriptGeneration')) {
    return (
      <div>
        <h2>客户管理</h2>
        <Card>
          <p>此功能仅在旗舰版中可用</p>
          <p>旗舰版专属功能：客户企业管理、猎头业务全流程管理</p>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <h2>客户管理</h2>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setClientVisible(true)}>添加客户</Button>
        </Space>

        <Table columns={columns} dataSource={mockClients} rowKey="id" pagination={{ pageSize: 10 }} />
      </Card>

      <Modal
        title="添加客户"
        open={clientVisible}
        onCancel={() => setClientVisible(false)}
        onOk={() => setClientVisible(false)}
      >
        <Form layout="vertical">
          <Form.Item label="企业名称">
            <Input />
          </Form.Item>
          <Form.Item label="行业">
            <Input />
          </Form.Item>
          <Form.Item label="规模">
            <Select placeholder="选择规模">
              <Select.Option value="1-50人">1-50人</Select.Option>
              <Select.Option value="50-200人">50-200人</Select.Option>
              <Select.Option value="200-1000人">200-1000人</Select.Option>
              <Select.Option value="1000人以上">1000人以上</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="联系人">
            <Input />
          </Form.Item>
          <Form.Item label="联系电话">
            <Input />
          </Form.Item>
          <Form.Item label="联系邮箱">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ClientPage;