import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Layout, Menu, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import {
  DashboardOutlined,
  TeamOutlined,
  FileTextOutlined,
  SolutionOutlined,
  CalendarOutlined,
  BarChartOutlined,
  SettingOutlined,
  BriefcaseOutlined,
  ContactsOutlined,
  SearchOutlined,
  BuildingOutlined,
} from '@ant-design/icons';
import { EditionProvider } from './contexts/EditionContext';
import DashboardPage from './pages/Dashboard';
import TalentPoolPage from './pages/TalentPool';
import ResumePage from './pages/Resume';
import JobPage from './pages/Job';
import InterviewPage from './pages/Interview';
import EmployeePage from './pages/Employee';
import ReportPage from './pages/Report';
import SearchPage from './pages/Search';
import ClientPage from './pages/Client';
import SettingsPage from './pages/Settings';

const { Sider, Content } = Layout;

const App: React.FC = () => {
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  const menuItems = [
    { key: '/dashboard', icon: <DashboardOutlined />, label: '工作台' },
    { key: '/talent-pool', icon: <TeamOutlined />, label: '人才库' },
    { key: '/resumes', icon: <FileTextOutlined />, label: '简历管理' },
    { key: '/jobs', icon: <BriefcaseOutlined />, label: '职位管理' },
    { key: '/interviews', icon: <CalendarOutlined />, label: '面试管理' },
    { key: '/employees', icon: <ContactsOutlined />, label: '员工档案' },
    { key: '/reports', icon: <BarChartOutlined />, label: '数据报表' },
    { key: '/search', icon: <SearchOutlined />, label: '人才寻访' },
    { key: '/clients', icon: <BuildingOutlined />, label: '客户管理' },
    { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
  ];

  return (
    <ConfigProvider locale={zhCN}>
      <EditionProvider>
        <BrowserRouter>
          <Layout style={{ minHeight: '100vh' }}>
            <Sider theme="dark" collapsible defaultCollapsed={false}>
              <div style={{ padding: '16px', textAlign: 'center' }}>
                <h2 style={{ color: 'white', margin: 0 }}>AI 人才管理平台</h2>
              </div>
              <Menu theme="dark" mode="inline" defaultSelectedKeys={['/dashboard']} items={menuItems} />
            </Sider>
            <Layout>
              <Content style={{ margin: '16px' }}>
                <div style={{ padding: 24, minHeight: 360, background: colorBgContainer, borderRadius: 8 }}>
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<DashboardPage />} />
                    <Route path="/talent-pool" element={<TalentPoolPage />} />
                    <Route path="/resumes" element={<ResumePage />} />
                    <Route path="/jobs" element={<JobPage />} />
                    <Route path="/interviews" element={<InterviewPage />} />
                    <Route path="/employees" element={<EmployeePage />} />
                    <Route path="/reports" element={<ReportPage />} />
                    <Route path="/search" element={<SearchPage />} />
                    <Route path="/clients" element={<ClientPage />} />
                    <Route path="/settings" element={<SettingsPage />} />
                  </Routes>
                </div>
              </Content>
            </Layout>
          </Layout>
        </BrowserRouter>
      </EditionProvider>
    </ConfigProvider>
  );
};

export default App;