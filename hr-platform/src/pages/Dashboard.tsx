import React from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Progress } from 'antd';
import {
  TeamOutlined,
  UserAddOutlined,
  UserDeleteOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { mockDashboard, mockDepartmentStats, mockRecruitmentFunnel } from '@/data/mockData';
import { useEdition } from '@/contexts/EditionContext';

const DashboardPage: React.FC = () => {
  const { hasFeature } = useEdition();

  const statsCards = [
    { title: '在职员工', value: mockDashboard.totalEmployees, icon: <TeamOutlined />, color: '#1890ff' },
    { title: '在招职位', value: mockDashboard.totalOpenPositions, icon: <UserAddOutlined />, color: '#52c41a' },
    { title: '候选人', value: mockDashboard.totalCandidates, icon: <TeamOutlined />, color: '#faad14' },
    { title: '储备人才', value: mockDashboard.totalReserveTalents, icon: <TeamOutlined />, color: '#722ed1' },
    { title: '本月入职', value: mockDashboard.thisMonthHires, icon: <UserAddOutlined />, color: '#13c2c2' },
    { title: '本月离职', value: mockDashboard.thisMonthResignations, icon: <UserDeleteOutlined />, color: '#ff4d4f' },
  ];

  const funnelOption = {
    title: { text: '招聘漏斗', left: 'center' },
    series: [{
      type: 'funnel',
      left: '10%',
      top: 40,
      bottom: 40,
      width: '80%',
      min: 0,
      max: mockRecruitmentFunnel[0].count,
      minSize: '0%',
      maxSize: '100%',
      sort: 'descending',
      gap: 2,
      label: { show: true, position: 'inside' },
      data: mockRecruitmentFunnel.map(item => ({
        name: item.stage,
        value: item.count,
      })),
    }],
  };

  const deptOption = {
    title: { text: '部门人员分布', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: mockDepartmentStats.map(d => d.department) },
    yAxis: { type: 'value' },
    series: [
      { name: '在职人数', type: 'bar', data: mockDepartmentStats.map(d => d.headcount), itemStyle: { color: '#1890ff' } },
      { name: '在招职位', type: 'bar', data: mockDepartmentStats.map(d => d.openPositions), itemStyle: { color: '#52c41a' } },
    ],
  };

  return (
    <div>
      <h2>工作台</h2>
      <Row gutter={[16, 16]}>
        {statsCards.map((stat, index) => (
          <Col span={4} key={index}>
            <Card>
              <Statistic
                title={stat.title}
                value={stat.value}
                prefix={React.cloneElement(stat.icon, { style: { color: stat.color } })}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {hasFeature('dataDashboard') && (
        <>
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col span={12}>
              <Card title="招聘漏斗">
                <ReactECharts option={funnelOption} style={{ height: 400 }} />
              </Card>
            </Col>
            <Col span={12}>
              <Card title="部门人员分布">
                <ReactECharts option={deptOption} style={{ height: 400 }} />
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col span={24}>
              <Card title="核心指标">
                <Row gutter={16}>
                  <Col span={6}>
                    <Statistic title="平均到岗时间" value={mockDashboard.avgTimeToFill} suffix="天" />
                  </Col>
                  <Col span={6}>
                    <Statistic title="Offer接受率" value={mockDashboard.offerAcceptanceRate} suffix="%" />
                  </Col>
                  <Col span={6}>
                    <Statistic title="离职率" value={mockDashboard.turnoverRate} suffix="%" />
                  </Col>
                  <Col span={6}>
                    <div>
                      <p>招聘目标完成度</p>
                      <Progress percent={65} status="active" />
                    </div>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        </>
      )}

      {!hasFeature('dataDashboard') && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Card title="核心指标">
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic title="平均到岗时间" value={mockDashboard.avgTimeToFill} suffix="天" />
                </Col>
                <Col span={8}>
                  <Statistic title="Offer接受率" value={mockDashboard.offerAcceptanceRate} suffix="%" />
                </Col>
                <Col span={8}>
                  <Statistic title="离职率" value={mockDashboard.turnoverRate} suffix="%" />
                </Col>
              </Row>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default DashboardPage;