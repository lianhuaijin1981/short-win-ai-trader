import { useState, useEffect, useCallback } from 'react';
import type {
  TradeJournal,
  JournalTemplate,
  TradeRecord,
  TradeDiagnosis,
} from '@/data/tradeData';

// ── Storage Keys ───────────────────────────────────────────────
const STORAGE_KEYS = {
  JOURNAL_TEMPLATES: 'trade_journal_templates',
  JOURNALS: 'trade_journals',
  TRADE_RECORDS: 'trade_records',
  TRADE_DIAGNOSES: 'trade_diagnoses',
  SETTINGS: 'trade_settings',
} as const;

// ── Helper Functions ───────────────────────────────────────────
function getItem<T>(key: string, defaultValue: T): T {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch {
    return defaultValue;
  }
}

function setItem<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    console.error(`Failed to save to localStorage: ${key}`, e);
  }
}

function _removeItem(_key: string): void {
  try {
    localStorage.removeItem(_key);
  } catch (e) {
    console.error(`Failed to remove from localStorage: ${_key}`, e);
  }
}

// ── useJournalTemplates Hook ───────────────────────────────────
export function useJournalTemplates() {
  const [templates, setTemplates] = useState<JournalTemplate[]>(() =>
    getItem<JournalTemplate[]>(STORAGE_KEYS.JOURNAL_TEMPLATES, [])
  );

  useEffect(() => {
    setItem(STORAGE_KEYS.JOURNAL_TEMPLATES, templates);
  }, [templates]);

  const addTemplate = useCallback((template: JournalTemplate) => {
    setTemplates(prev => [...prev, template]);
  }, []);

  const updateTemplate = useCallback((id: string, updates: Partial<JournalTemplate>) => {
    setTemplates(prev =>
      prev.map(t => t.id === id ? { ...t, ...updates, updatedAt: new Date().toISOString() } : t)
    );
  }, []);

  const deleteTemplate = useCallback((id: string) => {
    setTemplates(prev => prev.filter(t => t.id !== id));
  }, []);

  const getTemplate = useCallback((id: string) => {
    return templates.find(t => t.id === id);
  }, [templates]);

  return {
    templates,
    addTemplate,
    updateTemplate,
    deleteTemplate,
    getTemplate,
  };
}

// ── useTradeJournals Hook ──────────────────────────────────────
export function useTradeJournals() {
  const [journals, setJournals] = useState<TradeJournal[]>(() =>
    getItem<TradeJournal[]>(STORAGE_KEYS.JOURNALS, [])
  );

  useEffect(() => {
    setItem(STORAGE_KEYS.JOURNALS, journals);
  }, [journals]);

  const addJournal = useCallback((journal: TradeJournal) => {
    setJournals(prev => [...prev, journal]);
  }, []);

  const updateJournal = useCallback((id: string, updates: Partial<TradeJournal>) => {
    setJournals(prev =>
      prev.map(j => j.id === id ? { ...j, ...updates, updatedAt: new Date().toISOString() } : j)
    );
  }, []);

  const deleteJournal = useCallback((id: string) => {
    setJournals(prev => prev.filter(j => j.id !== id));
  }, []);

  const getJournal = useCallback((id: string) => {
    return journals.find(j => j.id === id);
  }, [journals]);

  const getJournalByDate = useCallback((date: string) => {
    return journals.find(j => j.date === date);
  }, [journals]);

  const getJournalsByDateRange = useCallback((startDate: string, endDate: string) => {
    return journals.filter(j => j.date >= startDate && j.date <= endDate);
  }, [journals]);

  return {
    journals,
    addJournal,
    updateJournal,
    deleteJournal,
    getJournal,
    getJournalByDate,
    getJournalsByDateRange,
  };
}

// ── useTradeRecords Hook ───────────────────────────────────────
export function useTradeRecords() {
  const [records, setRecords] = useState<TradeRecord[]>(() =>
    getItem<TradeRecord[]>(STORAGE_KEYS.TRADE_RECORDS, [])
  );

  useEffect(() => {
    setItem(STORAGE_KEYS.TRADE_RECORDS, records);
  }, [records]);

  const addRecord = useCallback((record: TradeRecord) => {
    setRecords(prev => [...prev, record]);
  }, []);

  const addRecords = useCallback((newRecords: TradeRecord[]) => {
    setRecords(prev => [...prev, ...newRecords]);
  }, []);

  const updateRecord = useCallback((id: string, updates: Partial<TradeRecord>) => {
    setRecords(prev =>
      prev.map(r => r.id === id ? { ...r, ...updates, updatedAt: new Date().toISOString() } : r)
    );
  }, []);

  const deleteRecord = useCallback((id: string) => {
    setRecords(prev => prev.filter(r => r.id !== id));
  }, []);

  const getRecord = useCallback((id: string) => {
    return records.find(r => r.id === id);
  }, [records]);

  const getRecordsByDate = useCallback((date: string) => {
    return records.filter(r => r.tradeDate === date);
  }, [records]);

  const getRecordsByDateRange = useCallback((startDate: string, endDate: string) => {
    return records.filter(r => r.tradeDate >= startDate && r.tradeDate <= endDate);
  }, [records]);

  const getRecordsByStock = useCallback((stockCode: string) => {
    return records.filter(r => r.stockCode === stockCode);
  }, [records]);

  const getSortedRecords = useCallback((sortBy: string = 'tradeTime', sortOrder: 'asc' | 'desc' = 'desc') => {
    return [...records].sort((a, b) => {
      const aVal = a[sortBy as keyof TradeRecord];
      const bVal = b[sortBy as keyof TradeRecord];
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
      }
      return 0;
    });
  }, [records]);

  return {
    records,
    addRecord,
    addRecords,
    updateRecord,
    deleteRecord,
    getRecord,
    getRecordsByDate,
    getRecordsByDateRange,
    getRecordsByStock,
    getSortedRecords,
  };
}

// ── useTradeDiagnoses Hook ─────────────────────────────────────
export function useTradeDiagnoses() {
  const [diagnoses, setDiagnoses] = useState<TradeDiagnosis[]>(() =>
    getItem<TradeDiagnosis[]>(STORAGE_KEYS.TRADE_DIAGNOSES, [])
  );

  useEffect(() => {
    setItem(STORAGE_KEYS.TRADE_DIAGNOSES, diagnoses);
  }, [diagnoses]);

  const addDiagnosis = useCallback((diagnosis: TradeDiagnosis) => {
    setDiagnoses(prev => [...prev, diagnosis]);
  }, []);

  const updateDiagnosis = useCallback((tradeId: string, updates: Partial<TradeDiagnosis>) => {
    setDiagnoses(prev =>
      prev.map(d => d.tradeId === tradeId ? { ...d, ...updates } : d)
    );
  }, []);

  const getDiagnosis = useCallback((tradeId: string) => {
    return diagnoses.find(d => d.tradeId === tradeId);
  }, [diagnoses]);

  return {
    diagnoses,
    addDiagnosis,
    updateDiagnosis,
    getDiagnosis,
  };
}

// ── useTradeSettings Hook ──────────────────────────────────────
export interface TradeSettings {
  defaultTemplateId: string;
  autoSaveInterval: number; // 自动保存间隔（秒）
  showAdvancedDiagnosis: boolean;
  theme: 'dark' | 'light';
}

const DEFAULT_SETTINGS: TradeSettings = {
  defaultTemplateId: 'default-daily',
  autoSaveInterval: 60,
  showAdvancedDiagnosis: true,
  theme: 'dark',
};

export function useTradeSettings() {
  const [settings, setSettings] = useState<TradeSettings>(() =>
    getItem<TradeSettings>(STORAGE_KEYS.SETTINGS, DEFAULT_SETTINGS)
  );

  useEffect(() => {
    setItem(STORAGE_KEYS.SETTINGS, settings);
  }, [settings]);

  const updateSettings = useCallback((updates: Partial<TradeSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }));
  }, []);

  return {
    settings,
    updateSettings,
  };
}

// ── IndexedDB Helper (for large files like screenshots) ────────
const DB_NAME = 'TradeDataDB';
const DB_VERSION = 1;
const STORE_NAME = 'files';

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function saveFileToIndexedDB(id: string, data: Blob | ArrayBuffer | string): Promise<void> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      store.put({ id, data, createdAt: new Date().toISOString() });
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (e) {
    console.error('Failed to save file to IndexedDB:', e);
  }
}

export async function getFileFromIndexedDB(id: string): Promise<Blob | ArrayBuffer | string | null> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const request = store.get(id);
      request.onsuccess = () => resolve(request.result?.data || null);
      request.onerror = () => reject(request.error);
    });
  } catch (e) {
    console.error('Failed to get file from IndexedDB:', e);
    return null;
  }
}

export async function deleteFileFromIndexedDB(id: string): Promise<void> {
  try {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      store.delete(id);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (e) {
    console.error('Failed to delete file from IndexedDB:', e);
  }
}