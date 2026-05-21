import React from 'react';
import { Card, Row, Col, Table, Statistic, Tag } from 'antd';
import ReactECharts from 'echarts-for-react';
import { mockDepartmentStats, mockRecruitmentFunnel, mockDashboard } from '@/data/mockData';
import { useEdition } from '@/contexts/EditionContext';

const ReportPage: React.FC = () => {
  const { hasFeature } = useEdition();

  const deptColumns = [
    { title: '部门', dataIndex: 'department', key: 'department' },
    { title: '人数', dataIndex: 'headcount', key: 'headcount' },
    { title: '在招职位', dataIndex: 'openPositions', key: 'openPositions' },
    { title: '离职率', dataIndex: 'turnoverRate', key: 'turnoverRate', render: (v: number) => `${v}%` },
    { title: '平均绩效', dataIndex: 'avgPerformance', key: 'avgPerformance' },
    { title: '平均司龄(年)', dataIndex: 'avgTenure', key: 'avgTenure' },
  ];

  const turnoverOption = {
    title: { text: '部门离职率对比', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: mockDepartmentStats.map(d => d.department) },
    yAxis: { type: 'value', name: '离职率(%)' },
    series: [{
      name: '离职率',
      type: 'bar',
      data: mockDepartmentStats.map(d => ({
        value: d.turnoverRate,
        itemStyle: { color: d.turnoverRate > 10 ? '#ff4d4f' : d.turnoverRate > 5 ? '#faad14' : '#52c41a' },
      })),
    }],
  };

  const performanceOption = {
    title: { text: '部门平均绩效对比', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: mockDepartmentStats.map(d => d.department) },
    yAxis: { type: 'value', min: 60, max: 100 },
    series: [{
      name: '平均绩效',
      type: 'bar',
      data: mockDepartmentStats.map(d => d.avgPerformance),
      itemStyle: { color: '#1890ff' },
    }],
  };

  const tenureOption = {
    title: { text: '部门平均司龄', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: mockDepartmentStats.map(d => d.department) },
    yAxis: { type: 'value', name: '年' },
    series: [{
      name: '平均司龄',
      type: 'line',
      data: mockDepartmentStats.map(d => d.avgTenure),
      itemStyle: { color: '#722ed1' },
      smooth: true,
    }],
  };

  return (
    <div>
      <h2>数据报表</h2>
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card>
            <Statistic title="总员工数" value={mockDashboard.totalEmployees} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="平均离职率" value={mockDashboard.turnoverRate} suffix="%" />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="平均绩效" value={82} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="平均司龄" value={2.5} suffix="年" />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="部门离职率对比">
            <ReactECharts option={turnoverOption} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="部门平均绩效对比">
            <ReactECharts option={performanceOption} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="部门平均司龄">
            <ReactECharts option={tenureOption} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="招聘漏斗">
            <ReactECharts option={{
              title: { text: '招聘转化漏斗', left: 'center' },
              series: [{
                type: 'funnel',
                data: mockRecruitmentFunnel.map(item => ({ name: item.stage, value: item.count })),
                label: { show: true, position: 'inside' },
              }],
            }} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>

      <Row style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="部门数据明细">
            <Table columns={deptColumns} dataSource={mockDepartmentStats} rowKey="department" pagination={false} />
          </Card>
        </Col>
      </Row>

      {hasFeature('performanceAnalysis') && (
        <Row style={{ marginTop: 16 }}>
          <Col span={24}>
            <Card title="人力成本分析（进阶版专属）">
              <p>人力成本建模、编制测算、人效分析等功能</p>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default ReportPage;