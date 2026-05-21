import React, { useState } from 'react';
import { Card, Table, Tag, Input, Select, Space, Button, Modal, Descriptions, Tabs } from 'antd';
import { SearchOutlined, PlusOutlined, EyeOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { mockTalentProfiles, mockTags } from '@/data/mockData';
import type { TalentProfile } from '@/types';
import { useEdition } from '@/contexts/EditionContext';

const { Search } = Input;

const TalentPoolPage: React.FC = () => {
  const { hasFeature } = useEdition();
  const [selectedTalent, setSelectedTalent] = useState<TalentProfile | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);

  const poolTypeMap: Record<string, { color: string; text: string }> = {
    employee: { color: 'blue', text: '在职员工' },
    candidate: { color: 'green', text: '候选人' },
    reserve: { color: 'orange', text: '储备人才' },
    blacklist: { color: 'red', text: '黑名单' },
  };

  const riskMap: Record<string, { color: string; text: string }> = {
    low: { color: 'green', text: '低风险' },
    medium: { color: 'orange', text: '中风险' },
    high: { color: 'red', text: '高风险' },
  };

  const columns: ColumnsType<TalentProfile> = [
    { title: '姓名', dataIndex: ['basic', 'name'], key: 'name' },
    { title: '年龄', dataIndex: ['basic', 'age'], key: 'age' },
    { title: '地点', dataIndex: ['basic', 'location'], key: 'location' },
    {
      title: '人才池',
      dataIndex: 'poolType',
      key: 'poolType',
      render: (type: string) => (
        <Tag color={poolTypeMap[type]?.color}>{poolTypeMap[type]?.text}</Tag>
      ),
    },
    {
      title: '匹配度',
      dataIndex: 'matchScore',
      key: 'matchScore',
      render: (score?: number) => score ? `${score}%` : '-',
    },
    {
      title: '风险等级',
      dataIndex: 'riskLevel',
      key: 'riskLevel',
      render: (level?: string) => level ? (
        <Tag color={riskMap[level]?.color}>{riskMap[level]?.text}</Tag>
      ) : '-',
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <Space wrap>
          {tags.slice(0, 3).map(tag => (
            <Tag key={tag}>{tag}</Tag>
          ))}
          {tags.length > 3 && <Tag>+{tags.length - 3}</Tag>}
        </Space>
      ),
    },
    {
      title: '最后联系',
      dataIndex: 'lastContactDate',
      key: 'lastContactDate',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => { setSelectedTalent(record); setDetailVisible(true); }}
        >
          详情
        </Button>
      ),
    },
  ];

  return (
    <div>
      <h2>人才库</h2>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Search placeholder="搜索姓名/技能/公司" style={{ width: 300 }} />
          <Select placeholder="人才池类型" style={{ width: 150 }}>
            <Select.Option value="all">全部</Select.Option>
            <Select.Option value="employee">在职员工</Select.Option>
            <Select.Option value="candidate">候选人</Select.Option>
            <Select.Option value="reserve">储备人才</Select.Option>
          </Select>
          <Select placeholder="风险等级" style={{ width: 150 }}>
            <Select.Option value="all">全部</Select.Option>
            <Select.Option value="low">低风险</Select.Option>
            <Select.Option value="medium">中风险</Select.Option>
            <Select.Option value="high">高风险</Select.Option>
          </Select>
          <Button type="primary" icon={<PlusOutlined />}>添加人才</Button>
        </Space>

        <Table
          columns={columns}
          dataSource={mockTalentProfiles}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="人才详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={800}
      >
        {selectedTalent && (
          <Tabs>
            <Tabs.TabPane tab="基本信息" key="basic">
              <Descriptions bordered column={2}>
                <Descriptions.Item label="姓名">{selectedTalent.basic.name}</Descriptions.Item>
                <Descriptions.Item label="年龄">{selectedTalent.basic.age}</Descriptions.Item>
                <Descriptions.Item label="地点">{selectedTalent.basic.location}</Descriptions.Item>
                <Descriptions.Item label="求职状态">{selectedTalent.jobStatus}</Descriptions.Item>
                <Descriptions.Item label="期望薪资">
                  {selectedTalent.expectedSalary ? `${selectedTalent.expectedSalary.min}-${selectedTalent.expectedSalary.max}` : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="到岗时间">{selectedTalent.noticePeriod}</Descriptions.Item>
              </Descriptions>
              <h4 style={{ marginTop: 16 }}>技能</h4>
              <Space wrap>
                {selectedTalent.skills.map(skill => <Tag key={skill}>{skill}</Tag>)}
              </Space>
              <h4 style={{ marginTop: 16 }}>标签</h4>
              <Space wrap>
                {selectedTalent.tags.map(tag => <Tag key={tag} color="blue">{tag}</Tag>)}
              </Space>
            </Tabs.TabPane>
            <Tabs.TabPane tab="工作经历" key="work">
              {selectedTalent.workExperiences.map((exp, index) => (
                <Card key={index} size="small" style={{ marginBottom: 8 }}>
                  <h4>{exp.company} - {exp.position}</h4>
                  <p>{exp.startDate} ~ {exp.isCurrent ? '至今' : exp.endDate}</p>
                  <p>{exp.description}</p>
                </Card>
              ))}
            </Tabs.TabPane>
            <Tabs.TabPane tab="沟通记录" key="communication">
              {selectedTalent.communicationRecords.map(record => (
                <Card key={record.id} size="small" style={{ marginBottom: 8 }}>
                  <p><strong>日期:</strong> {record.date}</p>
                  <p><strong>方式:</strong> {record.method}</p>
                  <p><strong>摘要:</strong> {record.summary}</p>
                  {record.nextStep && <p><strong>下一步:</strong> {record.nextStep}</p>}
                </Card>
              ))}
            </Tabs.TabPane>
            {hasFeature('deepAssessment') && (
              <Tabs.TabPane tab="深度评估" key="assessment">
                <p>旗舰版专属功能 - 深度人才评估</p>
              </Tabs.TabPane>
            )}
          </Tabs>
        )}
      </Modal>
    </div>
  );
};

export default TalentPoolPage;