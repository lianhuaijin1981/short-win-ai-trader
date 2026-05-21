import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  Save,
  Trash2,
  Edit3,
  FileText,
  Calendar,
  Tag,
  Smile,
  Frown,
  Meh,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Settings,
  Bold,
  Italic,
  Underline,
  List,
  ListOrdered,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Image,
  Table,
  Mic,
  MicOff,
  X,
  Check,
  Copy,
  FolderPlus,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  useTradeJournals,
  useJournalTemplates,
  useTradeSettings,
} from '@/hooks/useTradeStorage';
import type { TradeJournal, JournalTemplate, JournalSection } from '@/data/tradeData';
import { DEFAULT_JOURNAL_TEMPLATES } from '@/data/tradeData';

// ── 工具函数 ───────────────────────────────────────────────────
const generateId = () => Math.random().toString(36).substring(2, 11);
const formatDate = (date: string) => {
  const d = new Date(date);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
const getToday = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

// ── 情绪图标映射 ───────────────────────────────────────────────
const MOOD_ICONS: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  bullish: { icon: Smile, color: '#22c55e', label: '看多' },
  bearish: { icon: Frown, color: '#ef4444', label: '看空' },
  neutral: { icon: Meh, color: '#94a3b8', label: '中性' },
  cautious: { icon: AlertCircle, color: '#f59e0b', label: '谨慎' },
};

// ── 主组件 ─────────────────────────────────────────────────────
export default function TradeJournal() {
  const { journals, addJournal, updateJournal, deleteJournal, getJournalByDate } = useTradeJournals();
  const { templates, addTemplate, updateTemplate, deleteTemplate, getTemplate } = useJournalTemplates();
  const { settings, updateSettings } = useTradeSettings();

  const [selectedDate, setSelectedDate] = useState(getToday());
  const [currentJournal, setCurrentJournal] = useState<TradeJournal | null>(null);
  const [activeTemplateId, setActiveTemplateId] = useState(settings.defaultTemplateId);
  const [showTemplateManager, setShowTemplateManager] = useState(false);
  const [showJournalList, setShowJournalList] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');
  const [mood, setMood] = useState<TradeJournal['mood']>('neutral');
  const [showSaveIndicator, setShowSaveIndicator] = useState(false);

  // 初始化模板
  useEffect(() => {
    if (templates.length === 0) {
      DEFAULT_JOURNAL_TEMPLATES.forEach(t => addTemplate(t));
    }
  }, []);

  // 加载当日日志
  useEffect(() => {
    const existing = getJournalByDate(selectedDate);
    if (existing) {
      setCurrentJournal(existing);
      setTags(existing.tags);
      setMood(existing.mood);
    } else {
      // 创建新日志
      const template = getTemplate(activeTemplateId) || templates[0];
      if (template) {
        const newJournal: TradeJournal = {
          id: generateId(),
          date: selectedDate,
          templateId: template.id,
          sections: template.sections.map(s => ({ ...s, content: '' })),
          tags: [],
          mood: 'neutral',
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        setCurrentJournal(newJournal);
        setTags([]);
        setMood('neutral');
      }
    }
  }, [selectedDate, activeTemplateId]);

  // 自动保存
  useEffect(() => {
    if (!currentJournal) return;
    const timer = setTimeout(() => {
      saveJournal();
    }, settings.autoSaveInterval * 1000);
    return () => clearTimeout(timer);
  }, [currentJournal, settings.autoSaveInterval]);

  const saveJournal = useCallback(() => {
    if (!currentJournal) return;
    const journalToSave = {
      ...currentJournal,
      tags,
      mood,
      updatedAt: new Date().toISOString(),
    };
    const existing = getJournalByDate(selectedDate);
    if (existing) {
      updateJournal(existing.id, journalToSave);
    } else {
      addJournal(journalToSave);
    }
    setShowSaveIndicator(true);
    setTimeout(() => setShowSaveIndicator(false), 2000);
  }, [currentJournal, tags, mood, selectedDate]);

  const updateSectionContent = (sectionId: string, content: string) => {
    if (!currentJournal) return;
    setCurrentJournal({
      ...currentJournal,
      sections: currentJournal.sections.map(s =>
        s.id === sectionId ? { ...s, content } : s
      ),
    });
  };

  const toggleSectionVisibility = (sectionId: string) => {
    if (!currentJournal) return;
    setCurrentJournal({
      ...currentJournal,
      sections: currentJournal.sections.map(s =>
        s.id === sectionId ? { ...s, isVisible: !s.isVisible } : s
      ),
    });
  };

  const addTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter(t => t !== tag));
  };

  // 语音输入
  const startVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('您的浏览器不支持语音输入');
      return;
    }
    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => setIsRecording(true);
    recognition.onresult = (event: any) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      if (activeSectionId) {
        const section = currentJournal?.sections.find(s => s.id === activeSectionId);
        if (section) {
          updateSectionContent(activeSectionId, section.content + transcript);
        }
      }
    };
    recognition.onerror = () => setIsRecording(false);
    recognition.onend = () => setIsRecording(false);
    recognition.start();
  };

  return (
    <div className="h-full flex flex-col bg-[#0d1526] text-[#e2e8f0]">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(148,163,184,0.1)] bg-[#111827]">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-bold text-[#c9a84c]">交易日志</h1>
          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-[#94a3b8]" />
            <input
              type="date"
              value={selectedDate}
              onChange={e => setSelectedDate(e.target.value)}
              className="bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-2 py-1 text-sm text-[#e2e8f0]"
            />
          </div>
          <select
            value={activeTemplateId}
            onChange={e => setActiveTemplateId(e.target.value)}
            className="bg-[#1e293b] border border-[rgba(148,163,184,0.2)] rounded px-2 py-1 text-sm text-[#e2e8f0]"
          >
            {templates.map(t => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowJournalList(!showJournalList)}
            className="flex items-center gap-1 px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] rounded text-sm transition-colors"
          >
            <FileText size={14} />
            历史日志
          </button>
          <button
            onClick={() => setShowTemplateManager(!showTemplateManager)}
            className="flex items-center gap-1 px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] rounded text-sm transition-colors"
          >
            <Settings size={14} />
            模板管理
          </button>
          <button
            onClick={saveJournal}
            className="flex items-center gap-1 px-4 py-1.5 bg-[#c9a84c] hover:bg-[#b8943f] text-[#0d1526] rounded text-sm font-medium transition-colors"
          >
            <Save size={14} />
            保存
          </button>
        </div>
      </div>

      {/* 保存指示器 */}
      <AnimatePresence>
        {showSaveIndicator && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-20 right-4 z-50 flex items-center gap-2 px-4 py-2 bg-[#22c55e] text-white rounded-lg shadow-lg"
          >
            <Check size={16} />
            已保存
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex-1 flex overflow-hidden">
        {/* 左侧：历史日志列表 */}
        <AnimatePresence>
          {showJournalList && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 280, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="border-r border-[rgba(148,163,184,0.1)] bg-[#111827] overflow-y-auto"
            >
              <div className="p-3">
                <h3 className="text-sm font-medium text-[#94a3b8] mb-3">历史日志</h3>
                <div className="space-y-1">
                  {journals
                    .sort((a, b) => b.date.localeCompare(a.date))
                    .map(j => (
                      <button
                        key={j.id}
                        onClick={() => {
                          setSelectedDate(j.date);
                          setShowJournalList(false);
                        }}
                        className={cn(
                          'w-full text-left px-3 py-2 rounded text-sm transition-colors',
                          j.date === selectedDate
                            ? 'bg-[#1e293b] text-[#c9a84c]'
                            : 'hover:bg-[#1e293b] text-[#94a3b8]'
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <span>{j.date}</span>
                          <span className={cn(
                            'w-2 h-2 rounded-full',
                            j.mood === 'bullish' ? 'bg-[#22c55e]' :
                            j.mood === 'bearish' ? 'bg-[#ef4444]' :
                            j.mood === 'cautious' ? 'bg-[#f59e0b]' : 'bg-[#94a3b8]'
                          )} />
                        </div>
                        <div className="text-xs text-[#64748b] mt-1">
                          {j.tags.slice(0, 3).join(' ')}
                        </div>
                      </button>
                    ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 中间：日志编辑区 */}
        <div className="flex-1 overflow-y-auto">
          {/* 情绪和标签栏 */}
          <div className="flex items-center gap-4 px-4 py-2 border-b border-[rgba(148,163,184,0.1)] bg-[#0f172a]">
            <div className="flex items-center gap-2">
              <span className="text-xs text-[#64748b]">情绪:</span>
              {Object.entries(MOOD_ICONS).map(([key, { icon: Icon, color, label }]) => (
                <button
                  key={key}
                  onClick={() => setMood(key as TradeJournal['mood'])}
                  className={cn(
                    'p-1.5 rounded transition-colors',
                    mood === key ? 'bg-[#1e293b]' : 'hover:bg-[#1e293b]'
                  )}
                  title={label}
                >
                  <Icon size={18} style={{ color }} />
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2 flex-1">
              <Tag size={14} className="text-[#64748b]" />
              <div className="flex items-center gap-1 flex-wrap">
                {tags.map(tag => (
                  <span
                    key={tag}
                    className="flex items-center gap-1 px-2 py-0.5 bg-[#1e293b] text-[#94a3b8] rounded text-xs"
                  >
                    {tag}
                    <button onClick={() => removeTag(tag)} className="hover:text-[#ef4444]">
                      <X size={10} />
                    </button>
                  </span>
                ))}
              </div>
              <input
                type="text"
                value={newTag}
                onChange={e => setNewTag(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && addTag()}
                placeholder="添加标签..."
                className="bg-transparent text-xs text-[#94a3b8] outline-none w-24"
              />
            </div>
          </div>

          {/* 日志内容区 */}
          <div className="p-4 space-y-4">
            {currentJournal?.sections.filter(s => s.isVisible).map((section, index) => (
              <JournalSectionEditor
                key={section.id}
                section={section}
                isActive={activeSectionId === section.id}
                onActivate={() => setActiveSectionId(section.id)}
                onUpdateContent={(content) => updateSectionContent(section.id, content)}
                onToggleVisibility={() => toggleSectionVisibility(section.id)}
                isRecording={isRecording && activeSectionId === section.id}
                onStartVoiceInput={() => {
                  setActiveSectionId(section.id);
                  startVoiceInput();
                }}
              />
            ))}
          </div>
        </div>

        {/* 右侧：模板管理 */}
        <AnimatePresence>
          {showTemplateManager && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="border-l border-[rgba(148,163,184,0.1)] bg-[#111827] overflow-y-auto"
            >
              <TemplateManager
                templates={templates}
                onUpdateTemplate={updateTemplate}
                onDeleteTemplate={deleteTemplate}
                onAddTemplate={addTemplate}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

// ── 日志段落编辑器 ─────────────────────────────────────────────
interface JournalSectionEditorProps {
  section: JournalSection;
  isActive: boolean;
  onActivate: () => void;
  onUpdateContent: (content: string) => void;
  onToggleVisibility: () => void;
  isRecording: boolean;
  onStartVoiceInput: () => void;
}

function JournalSectionEditor({
  section,
  isActive,
  onActivate,
  onUpdateContent,
  onToggleVisibility,
  isRecording,
  onStartVoiceInput,
}: JournalSectionEditorProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [textareaEl, setTextareaEl] = useState<HTMLTextAreaElement | null>(null);

  const insertFormat = (format: string) => {
    if (!textareaEl) return;
    const start = textareaEl.selectionStart;
    const end = textareaEl.selectionEnd;
    const selectedText = section.content.substring(start, end);
    let replacement = '';
    switch (format) {
      case 'bold':
        replacement = `**${selectedText || '粗体文字'}**`;
        break;
      case 'italic':
        replacement = `*${selectedText || '斜体文字'}*`;
        break;
      case 'underline':
        replacement = `__${selectedText || '下划线文字'}__`;
        break;
      case 'list':
        replacement = `\n- ${selectedText || '列表项'}`;
        break;
      case 'ordered-list':
        replacement = `\n1. ${selectedText || '列表项'}`;
        break;
      case 'table':
        replacement = `\n| 列1 | 列2 | 列3 |\n| --- | --- | --- |\n| 内容 | 内容 | 内容 |`;
        break;
    }
    const newContent = section.content.substring(0, start) + replacement + section.content.substring(end);
    onUpdateContent(newContent);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'rounded-lg border transition-colors',
        isActive
          ? 'border-[#c9a84c] bg-[#111827]'
          : 'border-[rgba(148,163,184,0.1)] bg-[#0f172a] hover:border-[rgba(148,163,184,0.2)]'
      )}
      onClick={onActivate}
    >
      {/* 段落标题栏 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(148,163,184,0.1)]">
        <div className="flex items-center gap-3">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsCollapsed(!isCollapsed);
            }}
            className="text-[#64748b] hover:text-[#94a3b8] transition-colors"
          >
            {isCollapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
          </button>
          <h3 className="text-sm font-medium text-[#e2e8f0]">{section.title}</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onStartVoiceInput();
            }}
            className={cn(
              'p-1.5 rounded transition-colors',
              isRecording
                ? 'bg-[#ef4444] text-white animate-pulse'
                : 'text-[#64748b] hover:text-[#94a3b8] hover:bg-[#1e293b]'
            )}
            title={isRecording ? '停止录音' : '语音输入'}
          >
            {isRecording ? <MicOff size={14} /> : <Mic size={14} />}
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleVisibility();
            }}
            className="text-[#64748b] hover:text-[#94a3b8] hover:bg-[#1e293b] p-1.5 rounded transition-colors"
            title="隐藏此段落"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* 工具栏 */}
      {!isCollapsed && (
        <div className="flex items-center gap-1 px-4 py-2 border-b border-[rgba(148,163,184,0.05)]">
          <ToolbarButton icon={<Bold size={14} />} onClick={() => insertFormat('bold')} title="粗体" />
          <ToolbarButton icon={<Italic size={14} />} onClick={() => insertFormat('italic')} title="斜体" />
          <ToolbarButton icon={<Underline size={14} />} onClick={() => insertFormat('underline')} title="下划线" />
          <div className="w-px h-5 bg-[rgba(148,163,184,0.2)] mx-1" />
          <ToolbarButton icon={<List size={14} />} onClick={() => insertFormat('list')} title="无序列表" />
          <ToolbarButton icon={<ListOrdered size={14} />} onClick={() => insertFormat('ordered-list')} title="有序列表" />
          <ToolbarButton icon={<Table size={14} />} onClick={() => insertFormat('table')} title="插入表格" />
          <div className="w-px h-5 bg-[rgba(148,163,184,0.2)] mx-1" />
          <ToolbarButton icon={<AlignLeft size={14} />} title="左对齐" />
          <ToolbarButton icon={<AlignCenter size={14} />} title="居中对齐" />
          <ToolbarButton icon={<AlignRight size={14} />} title="右对齐" />
          <div className="w-px h-5 bg-[rgba(148,163,184,0.2)] mx-1" />
          <ToolbarButton icon={<Image size={14} />} title="插入图片" />
          <ToolbarButton icon={<Copy size={14} />} title="复制" />
        </div>
      )}

      {/* 编辑区 */}
      {!isCollapsed && (
        <div className="p-4">
          <textarea
            ref={setTextareaEl}
            value={section.content}
            onChange={e => onUpdateContent(e.target.value)}
            placeholder={`在此输入${section.title}内容...`}
            className="w-full min-h-[150px] bg-transparent text-[#e2e8f0] text-sm outline-none resize-y placeholder:text-[#475569] leading-relaxed"
            style={{ fontFamily: "'JetBrains Mono', 'Fira Code', monospace" }}
          />
        </div>
      )}
    </motion.div>
  );
}

// ── 工具栏按钮 ─────────────────────────────────────────────────
interface ToolbarButtonProps {
  icon: React.ReactNode;
  onClick?: () => void;
  title?: string;
}

function ToolbarButton({ icon, onClick, title }: ToolbarButtonProps) {
  return (
    <button
      onClick={onClick}
      className="p-1.5 text-[#64748b] hover:text-[#c9a84c] hover:bg-[#1e293b] rounded transition-colors"
      title={title}
    >
      {icon}
    </button>
  );
}

// ── 模板管理器 ─────────────────────────────────────────────────
interface TemplateManagerProps {
  templates: JournalTemplate[];
  onUpdateTemplate: (id: string, updates: Partial<JournalTemplate>) => void;
  onDeleteTemplate: (id: string) => void;
  onAddTemplate: (template: JournalTemplate) => void;
}

function TemplateManager({
  templates,
  onUpdateTemplate,
  onDeleteTemplate,
  onAddTemplate,
}: TemplateManagerProps) {
  const [editingTemplate, setEditingTemplate] = useState<JournalTemplate | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTemplateName, setNewTemplateName] = useState('');

  const handleAddTemplate = () => {
    if (!newTemplateName.trim()) return;
    const newTemplate: JournalTemplate = {
      id: generateId(),
      name: newTemplateName.trim(),
      sections: [
        { id: generateId(), title: '新段落', content: '', order: 1, isVisible: true },
      ],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isDefault: false,
    };
    onAddTemplate(newTemplate);
    setNewTemplateName('');
    setShowAddForm(false);
  };

  const addSectionToTemplate = () => {
    if (!editingTemplate) return;
    const newSection: JournalSection = {
      id: generateId(),
      title: '新段落',
      content: '',
      order: editingTemplate.sections.length + 1,
      isVisible: true,
    };
    onUpdateTemplate(editingTemplate.id, {
      sections: [...editingTemplate.sections, newSection],
    });
    setEditingTemplate({ ...editingTemplate, sections: [...editingTemplate.sections, newSection] });
  };

  const removeSectionFromTemplate = (sectionId: string) => {
    if (!editingTemplate) return;
    const newSections = editingTemplate.sections.filter(s => s.id !== sectionId);
    onUpdateTemplate(editingTemplate.id, { sections: newSections });
    setEditingTemplate({ ...editingTemplate, sections: newSections });
  };

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-[#94a3b8]">模板管理</h3>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center gap-1 px-2 py-1 bg-[#1e293b] hover:bg-[#334155] rounded text-xs transition-colors"
        >
          <FolderPlus size={12} />
          新建模板
        </button>
      </div>

      {/* 新建模板表单 */}
      {showAddForm && (
        <div className="mb-4 p-3 bg-[#1e293b] rounded-lg">
          <input
            type="text"
            value={newTemplateName}
            onChange={e => setNewTemplateName(e.target.value)}
            placeholder="模板名称"
            className="w-full bg-[#0f172a] border border-[rgba(148,163,184,0.2)] rounded px-2 py-1.5 text-sm text-[#e2e8f0] mb-2"
          />
          <div className="flex gap-2">
            <button
              onClick={handleAddTemplate}
              className="px-3 py-1 bg-[#c9a84c] text-[#0d1526] rounded text-xs font-medium"
            >
              创建
            </button>
            <button
              onClick={() => setShowAddForm(false)}
              className="px-3 py-1 bg-[#334155] rounded text-xs"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {/* 模板列表 */}
      <div className="space-y-2">
        {templates.map(template => (
          <div
            key={template.id}
            className="p-3 bg-[#1e293b] rounded-lg"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-[#e2e8f0]">{template.name}</span>
                {template.isDefault && (
                  <span className="px-1.5 py-0.5 bg-[#c9a84c] text-[#0d1526] text-[10px] rounded">
                    默认
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setEditingTemplate(template)}
                  className="p-1 text-[#64748b] hover:text-[#c9a84c]"
                >
                  <Edit3 size={12} />
                </button>
                {!template.isDefault && (
                  <button
                    onClick={() => onDeleteTemplate(template.id)}
                    className="p-1 text-[#64748b] hover:text-[#ef4444]"
                  >
                    <Trash2 size={12} />
                  </button>
                )}
              </div>
            </div>
            <div className="text-xs text-[#64748b]">
              {template.sections.length} 个段落
            </div>
          </div>
        ))}
      </div>

      {/* 编辑模板弹窗 */}
      {editingTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-[500px] max-h-[80vh] bg-[#111827] rounded-lg border border-[rgba(148,163,184,0.2)] overflow-hidden"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(148,163,184,0.1)]">
              <h3 className="text-sm font-medium text-[#e2e8f0]">编辑模板: {editingTemplate.name}</h3>
              <button
                onClick={() => setEditingTemplate(null)}
                className="text-[#64748b] hover:text-[#e2e8f0]"
              >
                <X size={16} />
              </button>
            </div>
            <div className="p-4 overflow-y-auto max-h-[60vh]">
              <div className="space-y-2">
                {editingTemplate.sections.map((section, index) => (
                  <div
                    key={section.id}
                    className="flex items-center gap-2 p-2 bg-[#1e293b] rounded"
                  >
                    <span className="text-xs text-[#64748b] w-6">{index + 1}</span>
                    <input
                      type="text"
                      value={section.title}
                      onChange={e => {
                        const newSections = [...editingTemplate.sections];
                        newSections[index] = { ...section, title: e.target.value };
                        setEditingTemplate({ ...editingTemplate, sections: newSections });
                      }}
                      className="flex-1 bg-[#0f172a] border border-[rgba(148,163,184,0.2)] rounded px-2 py-1 text-sm text-[#e2e8f0]"
                    />
                    <button
                      onClick={() => removeSectionFromTemplate(section.id)}
                      className="p-1 text-[#64748b] hover:text-[#ef4444]"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
              </div>
              <button
                onClick={addSectionToTemplate}
                className="mt-3 flex items-center gap-1 px-3 py-1.5 bg-[#1e293b] hover:bg-[#334155] rounded text-sm text-[#94a3b8] transition-colors"
              >
                <Plus size={14} />
                添加段落
              </button>
            </div>
            <div className="flex justify-end gap-2 px-4 py-3 border-t border-[rgba(148,163,184,0.1)]">
              <button
                onClick={() => setEditingTemplate(null)}
                className="px-4 py-1.5 bg-[#334155] rounded text-sm"
              >
                取消
              </button>
              <button
                onClick={() => {
                  onUpdateTemplate(editingTemplate.id, editingTemplate);
                  setEditingTemplate(null);
                }}
                className="px-4 py-1.5 bg-[#c9a84c] text-[#0d1526] rounded text-sm font-medium"
              >
                保存
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}