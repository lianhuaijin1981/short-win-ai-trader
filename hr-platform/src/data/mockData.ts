// ═══════════════════════════════════════════════════════════════
//  AI 人才管理平台 - 模拟数据
// ═══════════════════════════════════════════════════════════════

import type {
  ResumeParsed,
  TalentProfile,
  FlagshipTalentProfile,
  EmployeeProfile,
  JobPosition,
  Interview,
  ClientCompany,
  SearchAssignment,
  SearchRecord,
  HRDashboard,
  DepartmentStats,
  RecruitmentFunnel,
  AIResumeMatch,
  AIInterviewQuestions,
  AIRiskAssessment,
  AIJDDraft,
  TalentTag,
} from '@/types';

// ── 模拟简历数据 ──────────────────────────────────────────────

export const mockResumes: ResumeParsed[] = [
  {
    id: 'resume_001',
    basic: {
      id: 'resume_001',
      name: '张伟',
      phone: '138****1234',
      email: 'zhang***@email.com',
      age: 28,
      gender: 'male',
      location: '上海',
    },
    educations: [
      {
        school: '上海交通大学',
        degree: 'bachelor',
        major: '计算机科学',
        startDate: '2014-09',
        endDate: '2018-06',
        isFullTime: true,
      },
    ],
    workExperiences: [
      {
        company: '阿里巴巴',
        position: '高级前端工程师',
        department: '技术部',
        startDate: '2020-03',
        endDate: '2024-01',
        isCurrent: false,
        description: '负责核心业务前端开发',
        achievements: ['主导微前端架构改造', '性能优化提升40%'],
        salary: 35000,
        reasonForLeaving: '寻求更大发展空间',
      },
      {
        company: '字节跳动',
        position: '前端技术专家',
        department: '抖音技术部',
        startDate: '2024-02',
        endDate: '',
        isCurrent: true,
        description: '负责抖音前端架构设计',
        achievements: ['搭建前端监控体系'],
        salary: 50000,
      },
    ],
    skills: ['React', 'Vue', 'TypeScript', 'Node.js', '微前端'],
    expectedSalary: { min: 45000, max: 60000, currency: 'CNY' },
    currentSalary: 50000,
    noticePeriod: '1个月',
    jobStatus: 'employed',
    source: 'BOSS直聘',
    createdAt: '2026-05-15T10:00:00Z',
    updatedAt: '2026-05-20T14:30:00Z',
  },
  {
    id: 'resume_002',
    basic: {
      id: 'resume_002',
      name: '李娜',
      phone: '139****5678',
      email: 'li***@email.com',
      age: 32,
      gender: 'female',
      location: '北京',
    },
    educations: [
      {
        school: '北京大学',
        degree: 'master',
        major: '人力资源管理',
        startDate: '2014-09',
        endDate: '2016-06',
        isFullTime: true,
      },
      {
        school: '复旦大学',
        degree: 'bachelor',
        major: '工商管理',
        startDate: '2010-09',
        endDate: '2014-06',
        isFullTime: true,
      },
    ],
    workExperiences: [
      {
        company: '腾讯',
        position: 'HRBP',
        department: '人力资源部',
        startDate: '2019-06',
        endDate: '2023-12',
        isCurrent: false,
        description: '负责技术团队HRBP工作',
        achievements: ['搭建人才梯队', '优化招聘流程'],
        salary: 30000,
        reasonForLeaving: '家庭原因回北京',
      },
    ],
    skills: ['招聘', '绩效管理', '员工关系', '人才发展', 'OD'],
    expectedSalary: { min: 35000, max: 45000, currency: 'CNY' },
    currentSalary: 30000,
    noticePeriod: '2周',
    jobStatus: 'looking',
    source: '猎聘',
    createdAt: '2026-05-10T09:00:00Z',
    updatedAt: '2026-05-18T11:00:00Z',
  },
  {
    id: 'resume_003',
    basic: {
      id: 'resume_003',
      name: '王强',
      phone: '136****9012',
      email: 'wang***@email.com',
      age: 35,
      gender: 'male',
      location: '深圳',
    },
    educations: [
      {
        school: '浙江大学',
        degree: 'master',
        major: '人工智能',
        startDate: '2011-09',
        endDate: '2014-06',
        isFullTime: true,
      },
    ],
    workExperiences: [
      {
        company: '华为',
        position: 'AI算法专家',
        department: '2012实验室',
        startDate: '2018-03',
        endDate: '2022-06',
        isCurrent: false,
        description: '负责NLP算法研究',
        achievements: ['发表顶会论文3篇', '申请专利5项'],
        salary: 60000,
        reasonForLeaving: '创业',
      },
      {
        company: '某AI创业公司',
        position: 'CTO',
        startDate: '2022-07',
        endDate: '2025-12',
        isCurrent: false,
        description: '负责公司技术战略',
        achievements: ['完成A轮融资', '团队从10人扩展到50人'],
        salary: 80000,
        reasonForLeaving: '创业失败',
      },
    ],
    skills: ['NLP', '深度学习', 'Python', 'PyTorch', '技术管理', '架构设计'],
    expectedSalary: { min: 70000, max: 100000, currency: 'CNY' },
    currentSalary: 80000,
    noticePeriod: '1个月',
    jobStatus: 'unemployed',
    source: '内部推荐',
    createdAt: '2026-05-01T08:00:00Z',
    updatedAt: '2026-05-19T16:00:00Z',
  },
];

// ── 模拟人才档案（进阶版） ────────────────────────────────────

export const mockTalentProfiles: TalentProfile[] = [
  {
    ...mockResumes[0],
    tags: ['前端专家', '大厂背景', '微前端', '高潜人才'],
    poolType: 'candidate',
    intention: {
      jobPreference: ['前端技术专家', '前端架构师'],
      locationPreference: ['上海', '杭州'],
      salaryExpectation: { min: 45000, max: 60000 },
      industryPreference: ['互联网', '金融科技'],
      workStylePreference: 'hybrid',
    },
    communicationRecords: [
      {
        id: 'comm_001',
        talentId: 'resume_001',
        date: '2026-05-18',
        method: 'phone',
        summary: '初步沟通，对机会感兴趣',
        nextStep: '安排技术面试',
        nextStepDate: '2026-05-22',
        createdBy: 'HR001',
      },
    ],
    matchScore: 85,
    riskLevel: 'low',
    lastContactDate: '2026-05-18',
    nextFollowUpDate: '2026-05-22',
  },
  {
    ...mockResumes[1],
    tags: ['HRBP', '大厂背景', '技术团队经验', '即战力'],
    poolType: 'candidate',
    intention: {
      jobPreference: ['HRBP', 'HRD'],
      locationPreference: ['北京'],
      salaryExpectation: { min: 35000, max: 45000 },
      industryPreference: ['互联网', '科技'],
      workStylePreference: 'onsite',
    },
    communicationRecords: [
      {
        id: 'comm_002',
        talentId: 'resume_002',
        date: '2026-05-15',
        method: 'wechat',
        summary: '已离职，可随时到岗',
        nextStep: '安排HR面试',
        nextStepDate: '2026-05-21',
        createdBy: 'HR001',
      },
    ],
    matchScore: 92,
    riskLevel: 'low',
    lastContactDate: '2026-05-15',
    nextFollowUpDate: '2026-05-21',
  },
  {
    ...mockResumes[2],
    tags: ['AI专家', 'CTO经验', '创业背景', '高端人才'],
    poolType: 'reserve',
    intention: {
      jobPreference: ['CTO', 'AI技术总监', 'VP Engineering'],
      locationPreference: ['深圳', '广州'],
      salaryExpectation: { min: 70000, max: 100000 },
      industryPreference: ['AI', '科技'],
      workStylePreference: 'hybrid',
    },
    communicationRecords: [
      {
        id: 'comm_003',
        talentId: 'resume_003',
        date: '2026-05-10',
        method: 'interview',
        summary: '深度沟通，创业失败后寻求稳定平台',
        nextStep: '推荐给CTO',
        createdBy: 'HR002',
      },
    ],
    matchScore: 78,
    riskLevel: 'medium',
    lastContactDate: '2026-05-10',
    nextFollowUpDate: '2026-05-25',
  },
];

// ── 模拟员工档案 ──────────────────────────────────────────────

export const mockEmployees: EmployeeProfile[] = [
  {
    id: 'emp_001',
    employeeNo: 'EMP001',
    name: '陈明',
    department: '技术部',
    position: '前端工程师',
    level: 'P6',
    managerId: 'emp_010',
    hireDate: '2023-03-15',
    probationEndDate: '2023-06-15',
    status: 'regular',
    salary: { base: 25000, performance: 5000 },
    performance: [
      { period: '2025-Q4', score: 85, rating: 'B', comments: '表现稳定' },
      { period: '2026-Q1', score: 90, rating: 'A', comments: '有显著提升' },
    ],
    attendance: [
      { month: '2026-04', workDays: 22, absentDays: 0, leaveDays: 1, overtimeHours: 15 },
      { month: '2026-05', workDays: 15, absentDays: 0, leaveDays: 0, overtimeHours: 10 },
    ],
  },
  {
    id: 'emp_002',
    employeeNo: 'EMP002',
    name: '刘芳',
    department: '产品部',
    position: '产品经理',
    level: 'P7',
    managerId: 'emp_011',
    hireDate: '2022-06-01',
    status: 'regular',
    salary: { base: 30000, performance: 8000, bonus: 20000 },
    performance: [
      { period: '2025-Q4', score: 92, rating: 'A', comments: '优秀' },
      { period: '2026-Q1', score: 88, rating: 'A', comments: '持续优秀' },
    ],
  },
  {
    id: 'emp_003',
    employeeNo: 'EMP003',
    name: '赵磊',
    department: '技术部',
    position: '后端工程师',
    level: 'P5',
    hireDate: '2024-09-01',
    probationEndDate: '2024-12-01',
    contractEndDate: '2027-09-01',
    status: 'regular',
    salary: { base: 20000, performance: 4000 },
    performance: [
      { period: '2025-Q4', score: 75, rating: 'B' },
      { period: '2026-Q1', score: 70, rating: 'C', comments: '需要提升' },
    ],
  },
];

// ── 模拟岗位 ──────────────────────────────────────────────────

export const mockJobs: JobPosition[] = [
  {
    id: 'job_001',
    title: '高级前端工程师',
    department: '技术部',
    level: 'P7',
    headcount: 3,
    currentHeadcount: 1,
    status: 'open',
    priority: 'high',
    description: '负责公司核心产品前端开发',
    requirements: ['5年以上前端经验', '精通React/Vue', '有大型项目经验'],
    salaryRange: { min: 35000, max: 50000 },
    location: '上海',
    jobType: 'full_time',
    createdAt: '2026-05-01',
    updatedAt: '2026-05-15',
    createdBy: 'HR001',
  },
  {
    id: 'job_002',
    title: 'HRBP',
    department: '人力资源部',
    level: 'M2',
    headcount: 1,
    currentHeadcount: 0,
    status: 'open',
    priority: 'urgent',
    description: '负责技术团队HRBP工作',
    requirements: ['5年以上HRBP经验', '有技术团队管理经验', '互联网行业背景'],
    salaryRange: { min: 30000, max: 45000 },
    location: '北京',
    jobType: 'full_time',
    createdAt: '2026-05-10',
    updatedAt: '2026-05-18',
    createdBy: 'HR002',
  },
  {
    id: 'job_003',
    title: 'AI算法工程师',
    department: '技术部',
    level: 'P8',
    headcount: 2,
    currentHeadcount: 0,
    status: 'open',
    priority: 'high',
    description: '负责AI算法研发',
    requirements: ['硕士以上学历', 'NLP/CV方向', '有顶会论文优先'],
    salaryRange: { min: 50000, max: 80000 },
    location: '深圳',
    jobType: 'full_time',
    createdAt: '2026-05-05',
    updatedAt: '2026-05-12',
    createdBy: 'HR001',
  },
];

// ── 模拟面试 ──────────────────────────────────────────────────

export const mockInterviews: Interview[] = [
  {
    id: 'interview_001',
    talentId: 'resume_001',
    jobId: 'job_001',
    round: 1,
    date: '2026-05-22',
    time: '14:00',
    location: '会议室A',
    interviewers: ['emp_010', 'emp_011'],
    status: 'scheduled',
    createdAt: '2026-05-18',
  },
  {
    id: 'interview_002',
    talentId: 'resume_002',
    jobId: 'job_002',
    round: 1,
    date: '2026-05-21',
    time: '10:00',
    location: '线上',
    interviewers: ['HR001'],
    status: 'scheduled',
    createdAt: '2026-05-16',
  },
];

// ── 模拟标签 ──────────────────────────────────────────────────

export const mockTags: TalentTag[] = [
  { id: 'tag_001', name: '大厂背景', category: '背景', color: '#1890ff' },
  { id: 'tag_002', name: '前端专家', category: '技能', color: '#52c41a' },
  { id: 'tag_003', name: 'HRBP', category: '职能', color: '#faad14' },
  { id: 'tag_004', name: 'AI专家', category: '技能', color: '#722ed1' },
  { id: 'tag_005', name: '高潜人才', category: '评估', color: '#eb2f96' },
  { id: 'tag_006', name: '即战力', category: '评估', color: '#13c2c2' },
  { id: 'tag_007', name: '创业背景', category: '背景', color: '#fa8c16' },
  { id: 'tag_008', name: '管理潜力', category: '评估', color: '#a0d911' },
];

// ── 模拟仪表盘数据 ────────────────────────────────────────────

export const mockDashboard: HRDashboard = {
  totalEmployees: 156,
  totalOpenPositions: 12,
  totalCandidates: 45,
  totalReserveTalents: 128,
  thisMonthHires: 5,
  thisMonthResignations: 2,
  turnoverRate: 8.5,
  avgTimeToFill: 28,
  offerAcceptanceRate: 75,
};

export const mockDepartmentStats: DepartmentStats[] = [
  { department: '技术部', headcount: 68, openPositions: 5, turnoverRate: 6.2, avgPerformance: 82, avgTenure: 2.5 },
  { department: '产品部', headcount: 25, openPositions: 2, turnoverRate: 8.0, avgPerformance: 85, avgTenure: 2.1 },
  { department: '运营部', headcount: 32, openPositions: 3, turnoverRate: 12.5, avgPerformance: 78, avgTenure: 1.8 },
  { department: '销售部', headcount: 18, openPositions: 2, turnoverRate: 15.0, avgPerformance: 75, avgTenure: 1.5 },
  { department: '人力资源部', headcount: 8, openPositions: 1, turnoverRate: 5.0, avgPerformance: 88, avgTenure: 3.2 },
  { department: '财务部', headcount: 5, openPositions: 0, turnoverRate: 0, avgPerformance: 90, avgTenure: 4.0 },
];

export const mockRecruitmentFunnel: RecruitmentFunnel[] = [
  { stage: '简历筛选', count: 450, conversionRate: 100 },
  { stage: '电话沟通', count: 180, conversionRate: 40 },
  { stage: '初试', count: 85, conversionRate: 19 },
  { stage: '复试', count: 42, conversionRate: 9 },
  { stage: '终试', count: 25, conversionRate: 6 },
  { stage: 'Offer', count: 15, conversionRate: 3 },
  { stage: '入职', count: 10, conversionRate: 2 },
];

// ── 模拟AI匹配结果 ────────────────────────────────────────────

export const mockAIMatches: AIResumeMatch[] = [
  {
    talentId: 'resume_001',
    jobId: 'job_001',
    matchScore: 88,
    matchDetails: {
      skills: 95,
      experience: 90,
      education: 85,
      salary: 80,
      location: 100,
    },
    strengths: ['技术栈高度匹配', '大厂经验', '微前端架构经验'],
    gaps: ['管理经验不足', '薪资期望略高'],
    recommendation: 'strong_match',
  },
  {
    talentId: 'resume_002',
    jobId: 'job_002',
    matchScore: 92,
    matchDetails: {
      skills: 95,
      experience: 90,
      education: 90,
      salary: 95,
      location: 100,
    },
    strengths: ['HRBP经验丰富', '技术团队背景', '大厂经验', '可随时到岗'],
    gaps: ['需要适应新行业'],
    recommendation: 'strong_match',
  },
  {
    talentId: 'resume_003',
    jobId: 'job_003',
    matchScore: 85,
    matchDetails: {
      skills: 95,
      experience: 85,
      education: 90,
      salary: 70,
      location: 100,
    },
    strengths: ['AI算法专家', 'NLP方向', 'CTO经验', '技术视野广'],
    gaps: ['薪资期望较高', '创业经历可能不稳定'],
    recommendation: 'good_match',
  },
];

// ── 模拟AI面试问题 ────────────────────────────────────────────

export const mockAIQuestions: AIInterviewQuestions = {
  general: [
    '请简单介绍一下你自己和你的工作经历',
    '你为什么考虑看新的机会？',
    '你对我们公司有什么了解？',
  ],
  technical: [
    '请描述你主导过的最复杂的前端架构项目',
    '微前端架构的优缺点是什么？你在实践中遇到过哪些坑？',
    '如何进行前端性能优化？请分享具体案例',
  ],
  behavioral: [
    '请分享一个你与团队意见不合的案例，你是如何处理的？',
    '描述一次你在压力下完成项目的经历',
    '你如何平衡技术债务和业务需求？',
  ],
  cultureFit: [
    '你理想中的团队是什么样的？',
    '你如何看待加班？',
    '你未来3年的职业规划是什么？',
  ],
};

// ── 模拟AI风险评估 ───────────────────────────────────────────

export const mockRiskAssessments: AIRiskAssessment[] = [
  {
    talentId: 'emp_003',
    flightRisk: 'high',
    riskScore: 78,
    riskFactors: ['绩效下滑', '近期无晋升', '市场薪资涨幅较大'],
    recommendations: ['安排1v1沟通', '制定成长计划', '考虑调薪'],
  },
  {
    talentId: 'emp_001',
    flightRisk: 'low',
    riskScore: 25,
    riskFactors: ['绩效提升', '近期有晋升'],
    recommendations: ['保持关注', '给予更多挑战'],
  },
];

// ── 模拟AI JD生成 ─────────────────────────────────────────────

export const mockAIJD: AIJDDraft = {
  title: '高级前端工程师',
  department: '技术部',
  responsibilities: [
    '负责公司核心产品的前端架构设计与开发',
    '主导前端技术选型和最佳实践落地',
    '优化前端性能和用户体验',
    '指导和培养初级前端工程师',
    '与产品、设计、后端团队紧密协作',
  ],
  requirements: [
    '本科及以上学历，计算机相关专业',
    '5年以上前端开发经验',
    '精通React/Vue等主流前端框架',
    '熟悉TypeScript，有大型项目经验',
    '了解前端工程化、性能优化',
    '具备良好的沟通能力和团队协作精神',
  ],
  niceToHave: [
    '有微前端架构经验',
    '有Node.js后端开发经验',
    '有开源项目贡献',
    '有大厂工作背景',
  ],
  benefits: [
    '有竞争力的薪资和期权',
    '弹性工作制',
    '年度体检',
    '学习发展基金',
    '舒适的办公环境',
  ],
};

// ── 猎头专属数据（旗舰版） ────────────────────────────────────

export const mockClients: ClientCompany[] = [
  {
    id: 'client_001',
    name: '某知名互联网公司',
    industry: '互联网',
    size: '1000-5000人',
    contactPerson: '张总',
    contactPhone: '138****0001',
    contactEmail: 'zhang***@company.com',
    address: '北京朝阳区',
    contractStatus: 'active',
    contractEndDate: '2027-06-30',
    serviceFee: 500000,
    notes: '年框合作，优先服务',
  },
  {
    id: 'client_002',
    name: '某AI独角兽',
    industry: '人工智能',
    size: '100-500人',
    contactPerson: '李总',
    contactPhone: '139****0002',
    contactEmail: 'li***@aicompany.com',
    contractStatus: 'active',
    contractEndDate: '2026-12-31',
    serviceFee: 300000,
  },
];

export const mockSearchAssignments: SearchAssignment[] = [
  {
    id: 'assignment_001',
    clientId: 'client_001',
    jobId: 'job_001',
    consultantId: 'consultant_001',
    status: 'in_progress',
    deadline: '2026-06-30',
    targetCount: 3,
    submittedCount: 2,
    interviewCount: 1,
    offerCount: 0,
    placedCount: 0,
    createdAt: '2026-05-01',
  },
];

export const mockSearchRecords: SearchRecord[] = [
  {
    id: 'search_001',
    assignmentId: 'assignment_001',
    talentId: 'resume_001',
    consultantId: 'consultant_001',
    status: 'submitted',
    submitDate: '2026-05-15',
    notes: '候选人背景优秀，推荐',
  },
];

// ── 导出所有数据 ──────────────────────────────────────────────

export const mockHRData = {
  resumes: mockResumes,
  talentProfiles: mockTalentProfiles,
  employees: mockEmployees,
  jobs: mockJobs,
  interviews: mockInterviews,
  tags: mockTags,
  dashboard: mockDashboard,
  departmentStats: mockDepartmentStats,
  recruitmentFunnel: mockRecruitmentFunnel,
  aiMatches: mockAIMatches,
  aiQuestions: mockAIQuestions,
  riskAssessments: mockRiskAssessments,
  aiJD: mockAIJD,
  clients: mockClients,
  searchAssignments: mockSearchAssignments,
  searchRecords: mockSearchRecords,
};