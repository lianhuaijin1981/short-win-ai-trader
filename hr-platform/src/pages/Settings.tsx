import React from 'react';
import { Card, Row, Col, Select, Switch, Divider, Typography, Tag, Space } from 'antd';
import { useEdition } from '@/contexts/EditionContext';
import type { PlatformEdition } from '@/types';
import { EDITION_FEATURES } from '@/types';

const { Title, Text, Paragraph } = Typography;

const SettingsPage: React.FC = () => {
  const { edition, setEdition, features } = useEdition();

  const editionInfo: Record<PlatformEdition, { name: string; desc: string; color: string }> = {
    standard: { name: '标准版', desc: '中小企业基础人事+招聘', color: 'blue' },
    advanced: { name: '进阶版', desc: '中大型企业AI人力运营', color: 'green' },
    flagship: { name: '旗舰版', desc: '猎头专属AI寻访系统', color: 'purple' },
  };

  return (
    <div>
      <h2>系统设置</h2>
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="版本选择">
            <Text>当前版本: </Text>
            <Tag color={editionInfo[edition].color}>{editionInfo[edition].name}</Tag>
            <Paragraph style={{ marginTop: 8 }}>{editionInfo[edition].desc}</Paragraph>
            <Divider />
            <Text>切换版本: </Text>
            <Select value={edition} onChange={setEdition} style={{ width: 200, marginLeft: 8 }}>
              <Select.Option value="standard">标准版 - 中小企业</Select.Option>
              <Select.Option value="advanced">进阶版 - 中大型企业</Select.Option>
              <Select.Option value="flagship">旗舰版 - 猎头公司</Select.Option>
            </Select>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="功能清单">
            <table style={{ width: '100%' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>功能</th>
                  <th>标准版</th>
                  <th>进阶版</th>
                  <th>旗舰版</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(EDITION_FEATURES.standard).map(([key]) => (
                  <tr key={key}>
                    <td>{key}</td>
                    <td>{EDITION_FEATURES.standard[key as keyof typeof EDITION_FEATURES.standard] ? '✓' : '✗'}</td>
                    <td>{EDITION_FEATURES.advanced[key as keyof typeof EDITION_FEATURES.advanced] ? '✓' : '✗'}</td>
                    <td>{EDITION_FEATURES.flagship[key as keyof typeof EDITION_FEATURES.flagship] ? '✓' : '✗'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={8}>
          <Card title="标准版功能">
            <ul>
              <li>简历自动结构化解析入库</li>
              <li>员工档案统一管理</li>
              <li>基础招聘职位发布管理</li>
              <li>简易人才筛选、关键词搜索</li>
              <li>基础人力数据统计报表</li>
              <li>入职/转正/离职流程线上化</li>
              <li>AI简历解析</li>
              <li>JD生成</li>
              <li>面试话术生成</li>
            </ul>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="进阶版新增功能">
            <ul>
              <li>多渠道简历批量导入+智能去重</li>
              <li>岗位-人才AI智能精准匹配</li>
              <li>组织架构管理、编制管控</li>
              <li>全员绩效数据多维分析</li>
              <li>员工流失风险预警</li>
              <li>人才储备池分类管理</li>
              <li>中高层人才简易盘点</li>
              <li>管理层人力数据驾驶舱</li>
              <li>HR智能问答</li>
              <li>绩效评语分析</li>
            </ul>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="旗舰版新增功能">
            <ul>
              <li>客户企业岗位需求统一建档</li>
              <li>寻访任务派发、跟进流程管控</li>
              <li>面试记录、背调信息、offer进度全流程闭环</li>
              <li>人才库去重合并、黑名单管理</li>
              <li>寻访业绩数据统计、成单率分析</li>
              <li>高端人才保密库独立隔离存储</li>
              <li>深度人才评估（离职原因、竞业、口碑等）</li>
              <li>多层级权限隔离</li>
              <li>人才动态长期跟踪</li>
              <li>海量自定义标签体系</li>
              <li>库内人才智能盘活</li>
            </ul>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default SettingsPage;