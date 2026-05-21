// ═══════════════════════════════════════════════════════════════
//  AI 人才管理平台 - 核心类型定义
// ═══════════════════════════════════════════════════════════════

// ── 版本类型 ───────────────────────────────────────────────────
export type PlatformEdition = 'standard' | 'advanced' | 'flagship';

// ── 用户角色 ───────────────────────────────────────────────────
export type UserRole = 'admin' | 'hr' | 'interviewer' | 'consultant' | 'manager' | 'partner';

// ── 人才池类型 ─────────────────────────────────────────────────
export type TalentPoolType = 'employee' | 'candidate' | 'reserve' | 'blacklist';

// ═══════════════════════════════════════════════════════════════
//  简历相关类型
// ═══════════════════════════════════════════════════════════════

export interface ResumeBasic {
  id: string;
  name: string;
  phone: string;
  email: string;
  age?: number;
  gender?: 'male' | 'female' | 'other';
  location?: string;
  avatar?: string;
}

export interface Education {
  school: string;
  degree: 'high_school' | 'associate' | 'bachelor' | 'master' | 'doctor';
  major: string;
  startDate: string;
  endDate: string;
  isFullTime: boolean;
}

export interface WorkExperience {
  company: string;
  position: string;
  department?: string;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
  description?: string;
  achievements?: string[];
  salary?: number;
  reasonForLeaving?: string;
}

export interface ResumeParsed {
  id: string;
  basic: ResumeBasic;
  educations: Education[];
  workExperiences: WorkExperience[];
  skills: string[];
  expectedSalary?: {
    min: number;
    max: number;
    currency: string;
  };
  currentSalary?: number;
  noticePeriod?: string;
  jobStatus?: 'employed' | 'unemployed' | 'looking';
  source?: string;
  createdAt: string;
  updatedAt: string;
}

// ═══════════════════════════════════════════════════════════════
//  进阶版/旗舰版扩展类型
// ═══════════════════════════════════════════════════════════════

export interface TalentTag {
  id: string;
  name: string;
  category: string;
  color?: string;
}

export interface CommunicationRecord {
  id: string;
  talentId: string;
  date: string;
  method: 'phone' | 'email' | 'wechat' | 'interview' | 'other';
  summary: string;
  nextStep?: string;
  nextStepDate?: string;
  createdBy: string;
}

export interface TalentIntention {
  jobPreference?: string[];
  locationPreference?: string[];
  salaryExpectation?: { min: number; max: number };
  industryPreference?: string[];
  companySizePreference?: string;
  workStylePreference?: 'onsite' | 'remote' | 'hybrid';
}

export interface TalentProfile extends ResumeParsed {
  tags: string[];
  poolType: TalentPoolType;
  intention?: TalentIntention;
  communicationRecords: CommunicationRecord[];
  matchScore?: number;
  riskLevel?: 'low' | 'medium' | 'high';
  lastContactDate?: string;
  nextFollowUpDate?: string;
}

// ═══════════════════════════════════════════════════════════════
//  旗舰版独有：深度人才评估
// ═══════════════════════════════════════════════════════════════

export interface DeepTalentAssessment {
  // 离职真实原因
  realReasonForLeaving?: string;
  // 职场口碑
  workplaceReputation?: string;
  // 上下级风格
  managementStyle?: string;
  // 竞业状态
  nonCompeteStatus?: 'none' | 'active' | 'expired';
  nonCompeteDetails?: string;
  // 劳动纠纷
  laborDispute?: boolean;
  laborDisputeDetails?: string;
  // 过往寻访记录
  previousSearchRecords?: {
    agency: string;
    date: string;
    result: string;
  }[];
  // 拒岗原因
  offerRejectionReasons?: string[];
  // 家庭意向
  familyIntention?: string;
  // 城市偏好
  cityPreference?: string[];
  // 薪资底线
  salaryBottomLine?: number;
  // 跳槽意愿度
  jobHoppingWillingness: 'low' | 'medium' | 'high';
  // 稳定性评估
  stabilityScore: number; // 1-100
  // 稀缺度
  scarcityLevel: 'common' | 'rare' | 'very_rare';
  // 难度系数
  difficultyCoefficient: number; // 1-10
}

export interface FlagshipTalentProfile extends TalentProfile {
  deepAssessment?: DeepTalentAssessment;
  searchHistory: {
    consultant: string;
    date: string;
    position: string;
    status: string;
  }[];
  confidentialityLevel: 'normal' | 'confidential' | 'top_secret';
  viewPermissionLevel: 'basic' | 'full' | 'partner_only';
}

// ═══════════════════════════════════════════════════════════════
//  员工档案
// ═══════════════════════════════════════════════════════════════

export interface EmployeeProfile {
  id: string;
  employeeNo: string;
  name: string;
  department: string;
  position: string;
  level?: string;
  managerId?: string;
  hireDate: string;
  probationEndDate?: string;
  contractEndDate?: string;
  status: 'probation' | 'regular' | 'resigning' | 'resigned';
  salary?: {
    base: number;
    performance?: number;
    bonus?: number;
  };
  performance?: {
    period: string;
    score: number;
    rating: 'A' | 'B' | 'C' | 'D';
    comments?: string;
  }[];
  attendance?: {
    month: string;
    workDays: number;
    absentDays: number;
    leaveDays: number;
    overtimeHours: number;
  }[];
}

// ═══════════════════════════════════════════════════════════════
//  岗位/职位管理
// ═══════════════════════════════════════════════════════════════

export interface JobPosition {
  id: string;
  title: string;
  department: string;
  level?: string;
  headcount: number;
  currentHeadcount: number;
  status: 'open' | 'closed' | 'on_hold';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  description?: string;
  requirements?: string[];
  salaryRange?: { min: number; max: number };
  location?: string;
  jobType: 'full_time' | 'part_time' | 'contract' | 'intern';
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

// ═══════════════════════════════════════════════════════════════
//  面试管理
// ═══════════════════════════════════════════════════════════════

export interface Interview {
  id: string;
  talentId: string;
  jobId: string;
  round: number;
  date: string;
  time: string;
  location?: string;
  interviewers: string[];
  status: 'scheduled' | 'completed' | 'cancelled' | 'no_show';
  result?: 'pass' | 'fail' | 'pending' | 'hold';
  feedback?: string;
  score?: number;
  notes?: string;
  createdAt: string;
}

// ═══════════════════════════════════════════════════════════════
//  猎头专属类型（旗舰版）
// ═══════════════════════════════════════════════════════════════

export interface ClientCompany {
  id: string;
  name: string;
  industry: string;
  size: string;
  contactPerson: string;
  contactPhone: string;
  contactEmail: string;
  address?: string;
  contractStatus: 'active' | 'expired' | 'pending';
  contractEndDate?: string;
  serviceFee?: number;
  notes?: string;
}

export interface SearchAssignment {
  id: string;
  clientId: string;
  jobId: string;
  consultantId: string;
  status: 'assigned' | 'in_progress' | 'completed' | 'cancelled';
  deadline?: string;
  targetCount: number;
  submittedCount: number;
  interviewCount: number;
  offerCount: number;
  placedCount: number;
  createdAt: string;
}

export interface SearchRecord {
  id: string;
  assignmentId: string;
  talentId: string;
  consultantId: string;
  status: 'sourced' | 'contacted' | 'interested' | 'submitted' | 'interviewing' | 'offered' | 'placed' | 'rejected';
  submitDate?: string;
  interviewDate?: string;
  offerDate?: string;
  offerAmount?: number;
  placedDate?: string;
  rejectionReason?: string;
  notes?: string;
}

// ═══════════════════════════════════════════════════════════════
//  数据统计类型
// ═══════════════════════════════════════════════════════════════

export interface HRDashboard {
  totalEmployees: number;
  totalOpenPositions: number;
  totalCandidates: number;
  totalReserveTalents: number;
  thisMonthHires: number;
  thisMonthResignations: number;
  turnoverRate: number;
  avgTimeToFill: number;
  offerAcceptanceRate: number;
}

export interface DepartmentStats {
  department: string;
  headcount: number;
  openPositions: number;
  turnoverRate: number;
  avgPerformance: number;
  avgTenure: number;
}

export interface RecruitmentFunnel {
  stage: string;
  count: number;
  conversionRate: number;
}

// ═══════════════════════════════════════════════════════════════
//  AI 能力类型
// ═══════════════════════════════════════════════════════════════

export interface AIResumeMatch {
  talentId: string;
  jobId: string;
  matchScore: number;
  matchDetails: {
    skills: number;
    experience: number;
    education: number;
    salary: number;
    location: number;
  };
  strengths: string[];
  gaps: string[];
  recommendation: 'strong_match' | 'good_match' | 'possible_match' | 'not_recommended';
}

export interface AIInterviewQuestions {
  general: string[];
  technical: string[];
  behavioral: string[];
  cultureFit: string[];
}

export interface AIRiskAssessment {
  talentId: string;
  flightRisk: 'low' | 'medium' | 'high';
  riskScore: number;
  riskFactors: string[];
  recommendations: string[];
}

export interface AIJDDraft {
  title: string;
  department: string;
  responsibilities: string[];
  requirements: string[];
  niceToHave: string[];
  benefits: string[];
}

// ═══════════════════════════════════════════════════════════════
//  权限控制
// ═══════════════════════════════════════════════════════════════

export interface Permission {
  resource: string;
  actions: ('view' | 'create' | 'edit' | 'delete' | 'export')[];
}

export interface RolePermissions {
  role: UserRole;
  permissions: Permission[];
  dataScope: 'all' | 'department' | 'self' | 'assigned';
  canViewDeepInfo: boolean;
  canExportData: boolean;
  canManageUsers: boolean;
}

// ── 版本功能配置 ───────────────────────────────────────────────

export interface EditionFeatures {
  // 简历解析
  resumeParsing: boolean;
  // JD生成
  jdGeneration: boolean;
  // 面试话术
  interviewQuestions: boolean;
  // AI匹配
  aiMatching: boolean;
  // 绩效分析
  performanceAnalysis: boolean;
  // 流失风险
  flightRiskPrediction: boolean;
  // HR问答
  hrChatbot: boolean;
  // 人才画像建模
  talentProfiling: boolean;
  // 行业人才分析
  industryTalentAnalysis: boolean;
  // 寻访话术生成
  searchScriptGeneration: boolean;
  // 背调
  backgroundCheck: boolean;
  // 深度评估
  deepAssessment: boolean;
  // 权限隔离
  permissionIsolation: boolean;
  // 人才动态跟踪
  talentDynamicTracking: boolean;
  // 数据大屏
  dataDashboard: boolean;
}

export const EDITION_FEATURES: Record<PlatformEdition, EditionFeatures> = {
  standard: {
    resumeParsing: true,
    jdGeneration: true,
    interviewQuestions: true,
    aiMatching: false,
    performanceAnalysis: false,
    flightRiskPrediction: false,
    hrChatbot: false,
    talentProfiling: false,
    industryTalentAnalysis: false,
    searchScriptGeneration: false,
    backgroundCheck: false,
    deepAssessment: false,
    permissionIsolation: false,
    talentDynamicTracking: false,
    dataDashboard: false,
  },
  advanced: {
    resumeParsing: true,
    jdGeneration: true,
    interviewQuestions: true,
    aiMatching: true,
    performanceAnalysis: true,
    flightRiskPrediction: true,
    hrChatbot: true,
    talentProfiling: false,
    industryTalentAnalysis: false,
    searchScriptGeneration: false,
    backgroundCheck: true,
    deepAssessment: false,
    permissionIsolation: false,
    talentDynamicTracking: false,
    dataDashboard: true,
  },
  flagship: {
    resumeParsing: true,
    jdGeneration: true,
    interviewQuestions: true,
    aiMatching: true,
    performanceAnalysis: true,
    flightRiskPrediction: true,
    hrChatbot: true,
    talentProfiling: true,
    industryTalentAnalysis: true,
    searchScriptGeneration: true,
    backgroundCheck: true,
    deepAssessment: true,
    permissionIsolation: true,
    talentDynamicTracking: true,
    dataDashboard: true,
  },
};