import React, { useState } from 'react';
import { Card, Table, Tag, Space, Button, Modal, Descriptions, Tabs, Progress } from 'antd';
import { PlusOutlined, EyeOutlined, WarningOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { mockEmployees, mockRiskAssessments } from '@/data/mockData';
import type { EmployeeProfile } from '@/types';
import { useEdition } from '@/contexts/EditionContext';

const EmployeePage: React.FC = () => {
  const { hasFeature } = useEdition();
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<EmployeeProfile | null>(null);

  const statusMap: Record<string, { color: string; text: string }> = {
    probation: { color: 'orange', text: '试用期' },
    regular: { color: 'green', text: '正式' },
    resigning: { color: 'red', text: '离职中' },
    resigned: { color: 'default', text: '已离职' },
  };

  const ratingMap: Record<string, { color: string }> = {
    A: { color: 'green' },
    B: { color: 'blue' },
    C: { color: 'orange' },
    D: { color: 'red' },
  };

  const columns: ColumnsType<EmployeeProfile> = [
    { title: '工号', dataIndex: 'employeeNo', key: 'employeeNo' },
    { title: '姓名', dataIndex: 'name', key: 'name' },
    { title: '部门', dataIndex: 'department', key: 'department' },
    { title: '职位', dataIndex: 'position', key: 'position' },
    { title: '级别', dataIndex: 'level', key: 'level' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <Tag color={statusMap[status]?.color}>{statusMap[status]?.text}</Tag>,
    },
    { title: '入职日期', dataIndex: 'hireDate', key: 'hireDate' },
    {
      title: '最近绩效',
      key: 'performance',
      render: (_: any, record: EmployeeProfile) => {
        const latest = record.performance?.[record.performance.length - 1];
        return latest ? <Tag color={ratingMap[latest.rating]?.color}>{latest.rating}</Tag> : '-';
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: EmployeeProfile) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />} onClick={() => { setSelectedEmployee(record); setDetailVisible(true); }}>详情</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <h2>员工档案</h2>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button type="primary" icon={<PlusOutlined />}>添加员工</Button>
          {hasFeature('flightRiskPrediction') && (
            <Button type="primary" danger icon={<WarningOutlined />}>流失风险预警</Button>
          )}
        </Space>

        <Table columns={columns} dataSource={mockEmployees} rowKey="id" pagination={{ pageSize: 10 }} />
      </Card>

      <Modal
        title="员工详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={800}
      >
        {selectedEmployee && (
          <Tabs>
            <Tabs.TabPane tab="基本信息" key="basic">
              <Descriptions bordered column={2}>
                <Descriptions.Item label="工号">{selectedEmployee.employeeNo}</Descriptions.Item>
                <Descriptions.Item label="姓名">{selectedEmployee.name}</Descriptions.Item>
                <Descriptions.Item label="部门">{selectedEmployee.department}</Descriptions.Item>
                <Descriptions.Item label="职位">{selectedEmployee.position}</Descriptions.Item>
                <Descriptions.Item label="级别">{selectedEmployee.level}</Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag color={statusMap[selectedEmployee.status]?.color}>{statusMap[selectedEmployee.status]?.text}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="入职日期">{selectedEmployee.hireDate}</Descriptions.Item>
                <Descriptions.Item label="合同到期">
                  {selectedEmployee.contractEndDate || '无固定期限'}
                </Descriptions.Item>
              </Descriptions>
            </Tabs.TabPane>
            <Tabs.TabPane tab="绩效记录" key="performance">
              {selectedEmployee.performance?.map((p, i) => (
                <Card key={i} size="small" style={{ marginBottom: 8 }}>
                  <Space>
                    <strong>{p.period}</strong>
                    <Tag color={ratingMap[p.rating]?.color}>{p.rating}</Tag>
                    <span>得分: {p.score}</span>
                  </Space>
                  {p.comments && <p style={{ marginTop: 8 }}>{p.comments}</p>}
                </Card>
              ))}
            </Tabs.TabPane>
            <Tabs.TabPane tab="考勤记录" key="attendance">
              {selectedEmployee.attendance?.map((a, i) => (
                <Card key={i} size="small" style={{ marginBottom: 8 }}>
                  <Descriptions column={4} size="small">
                    <Descriptions.Item label="月份">{a.month}</Descriptions.Item>
                    <Descriptions.Item label="出勤">{a.workDays}天</Descriptions.Item>
                    <Descriptions.Item label="请假">{a.leaveDays}天</Descriptions.Item>
                    <Descriptions.Item label="加班">{a.overtimeHours}小时</Descriptions.Item>
                  </Descriptions>
                </Card>
              ))}
            </Tabs.TabPane>
            {hasFeature('flightRiskPrediction') && (
              <Tabs.TabPane tab="流失风险" key="risk">
                {mockRiskAssessments.find(r => r.talentId === selectedEmployee.id) ? (
                  (() => {
                    const risk = mockRiskAssessments.find(r => r.talentId === selectedEmployee.id)!;
                    return (
                      <>
                        <Progress
                          type="circle"
                          percent={risk.riskScore}
                          format={() => `${risk.flightRisk === 'high' ? '高风险' : risk.flightRisk === 'medium' ? '中风险' : '低风险'}`}
                          strokeColor={risk.flightRisk === 'high' ? '#ff4d4f' : risk.flightRisk === 'medium' ? '#faad14' : '#52c41a'}
                        />
                        <h4 style={{ marginTop: 16 }}>风险因素</h4>
                        <ul>
                          {risk.riskFactors.map((f, i) => <li key={i}>{f}</li>)}
                        </ul>
                        <h4>建议措施</h4>
                        <ul>
                          {risk.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                        </ul>
                      </>
                    );
                  })()
                ) : (
                  <p>暂无风险评估数据</p>
                )}
              </Tabs.TabPane>
            )}
          </Tabs>
        )}
      </Modal>
    </div>
  );
};

export default EmployeePage;