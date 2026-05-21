// ═══════════════════════════════════════════════════════════════
//  数据缓存服务
//  支持内存缓存 + IndexedDB持久化 + 降级策略
// ═══════════════════════════════════════════════════════════════

// ── 缓存配置 ───────────────────────────────────────────────────

interface CacheConfig {
  ttl: number;           // 过期时间（毫秒）
  persist: boolean;      // 是否持久化
  maxItems: number;      // 最大缓存项数
}

const DEFAULT_CACHE_CONFIG: CacheConfig = {
  ttl: 5 * 60 * 1000,    // 默认5分钟
  persist: false,
  maxItems: 1000,
};

// 不同类型数据的缓存配置
const CACHE_CONFIGS: Record<string, CacheConfig> = {
  'realtime': { ttl: 10 * 1000, persist: false, maxItems: 100 },     // 实时数据10秒
  'intraday': { ttl: 30 * 1000, persist: false, maxItems: 200 },     // 分时数据30秒
  'daily': { ttl: 60 * 60 * 1000, persist: true, maxItems: 500 },    // 日线数据1小时
  'basic': { ttl: 24 * 60 * 60 * 1000, persist: true, maxItems: 1000 }, // 基础数据24小时
  'news': { ttl: 30 * 60 * 1000, persist: false, maxItems: 200 },    // 新闻30分钟
  'diagnosis': { ttl: 24 * 60 * 60 * 1000, persist: true, maxItems: 500 }, // 诊断结果24小时
};

// ── 缓存项结构 ─────────────────────────────────────────────────

interface CacheItem<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
  hitCount: number;
}

// ── 内存缓存 ───────────────────────────────────────────────────

class MemoryCache {
  private store: Map<string, CacheItem<any>> = new Map();
  private config: CacheConfig;

  constructor(config: CacheConfig = DEFAULT_CACHE_CONFIG) {
    this.config = config;
  }

  get<T>(key: string): T | null {
    const item = this.store.get(key);
    if (!item) return null;

    // 检查是否过期
    if (Date.now() > item.expiresAt) {
      this.store.delete(key);
      return null;
    }

    item.hitCount++;
    return item.data as T;
  }

  set<T>(key: string, data: T, config?: Partial<CacheConfig>): void {
    // 检查缓存大小
    if (this.store.size >= (config?.maxItems || this.config.maxItems)) {
      this.evictOldest();
    }

    const ttl = config?.ttl || this.config.ttl;
    this.store.set(key, {
      data,
      timestamp: Date.now(),
      expiresAt: Date.now() + ttl,
      hitCount: 0,
    });
  }

  has(key: string): boolean {
    const item = this.store.get(key);
    if (!item) return false;
    if (Date.now() > item.expiresAt) {
      this.store.delete(key);
      return false;
    }
    return true;
  }

  delete(key: string): void {
    this.store.delete(key);
  }

  clear(): void {
    this.store.clear();
  }

  // 清理过期项
  cleanup(): void {
    const now = Date.now();
    for (const [key, item] of this.store.entries()) {
      if (now > item.expiresAt) {
        this.store.delete(key);
      }
    }
  }

  // 淘汰最少使用项
  private evictOldest(): void {
    let oldestKey: string | null = null;
    let oldestTime = Date.now();

    for (const [key, item] of this.store.entries()) {
      if (item.timestamp < oldestTime) {
        oldestTime = item.timestamp;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.store.delete(oldestKey);
    }
  }

  // 获取缓存统计信息
  getStats(): { size: number; hitRate: number } {
    let totalHits = 0;
    for (const item of this.store.values()) {
      totalHits += item.hitCount;
    }
    return {
      size: this.store.size,
      hitRate: this.store.size > 0 ? totalHits / this.store.size : 0,
    };
  }
}

// ── IndexedDB 持久化缓存 ──────────────────────────────────────

class IndexedDBCache {
  private dbName: string;
  private storeName: string;
  private db: IDBDatabase | null = null;
  private initPromise: Promise<void> | null = null;

  constructor(dbName: string = 'trade-cache', storeName: string = 'data') {
    this.dbName = dbName;
    this.storeName = storeName;
  }

  private async init(): Promise<void> {
    if (this.initPromise) return this.initPromise;

    this.initPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          db.createObjectStore(this.storeName, { keyPath: 'key' });
        }
      };
    });

    return this.initPromise;
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      await this.init();
      if (!this.db) return null;

      return new Promise((resolve) => {
        const transaction = this.db!.transaction(this.storeName, 'readonly');
        const store = transaction.objectStore(this.storeName);
        const request = store.get(key);

        request.onsuccess = () => {
          const item = request.result as CacheItem<T> | undefined;
          if (!item) {
            resolve(null);
            return;
          }

          // 检查是否过期
          if (Date.now() > item.expiresAt) {
            this.delete(key);
            resolve(null);
            return;
          }

          resolve(item.data);
        };

        request.onerror = () => resolve(null);
      });
    } catch {
      return null;
    }
  }

  async set<T>(key: string, data: T, config?: Partial<CacheConfig>): Promise<void> {
    try {
      await this.init();
      if (!this.db) return;

      const ttl = config?.ttl || DEFAULT_CACHE_CONFIG.ttl;
      const item: CacheItem<T> = {
        data,
        timestamp: Date.now(),
        expiresAt: Date.now() + ttl,
        hitCount: 0,
      };

      return new Promise((resolve) => {
        const transaction = this.db!.transaction(this.storeName, 'readwrite');
        const store = transaction.objectStore(this.storeName);
        store.put({ key, ...item });
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => resolve();
      });
    } catch {
      // 静默失败
    }
  }

  async delete(key: string): Promise<void> {
    try {
      await this.init();
      if (!this.db) return;

      return new Promise((resolve) => {
        const transaction = this.db!.transaction(this.storeName, 'readwrite');
        const store = transaction.objectStore(this.storeName);
        store.delete(key);
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => resolve();
      });
    } catch {
      // 静默失败
    }
  }

  async clear(): Promise<void> {
    try {
      await this.init();
      if (!this.db) return;

      return new Promise((resolve) => {
        const transaction = this.db!.transaction(this.storeName, 'readwrite');
        const store = transaction.objectStore(this.storeName);
        store.clear();
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => resolve();
      });
    } catch {
      // 静默失败
    }
  }
}

// ── 统一缓存服务 ───────────────────────────────────────────────

class DataCache {
  private memoryCache: MemoryCache;
  private dbCache: IndexedDBCache;

  constructor() {
    this.memoryCache = new MemoryCache();
    this.dbCache = new IndexedDBCache();

    // 定期清理过期缓存
    setInterval(() => this.memoryCache.cleanup(), 60 * 1000);
  }

  // 获取缓存（优先内存，其次IndexedDB）
  async get<T>(key: string, type: string = 'daily'): Promise<T | null> {
    // 1. 先查内存缓存
    const memoryData = this.memoryCache.get<T>(key);
    if (memoryData !== null) {
      return memoryData;
    }

    // 2. 查持久化缓存
    const config = CACHE_CONFIGS[type] || DEFAULT_CACHE_CONFIG;
    if (config.persist) {
      const dbData = await this.dbCache.get<T>(key);
      if (dbData !== null) {
        // 加载到内存缓存
        this.memoryCache.set(key, dbData, config);
        return dbData;
      }
    }

    return null;
  }

  // 设置缓存（同时写入内存和IndexedDB）
  async set<T>(key: string, data: T, type: string = 'daily'): Promise<void> {
    const config = CACHE_CONFIGS[type] || DEFAULT_CACHE_CONFIG;

    // 写入内存缓存
    this.memoryCache.set(key, data, config);

    // 如果需要持久化，写入IndexedDB
    if (config.persist) {
      await this.dbCache.set(key, data, config);
    }
  }

  // 删除缓存
  async delete(key: string): Promise<void> {
    this.memoryCache.delete(key);
    await this.dbCache.delete(key);
  }

  // 清除所有缓存
  async clear(): Promise<void> {
    this.memoryCache.clear();
    await this.dbCache.clear();
  }

  // 获取缓存统计
  getStats() {
    return {
      memory: this.memoryCache.getStats(),
    };
  }
}

// ── 带降级的数据请求封装 ───────────────────────────────────────

interface DataRequestOptions<T> {
  key: string;
  type?: string;
  fetcher: () => Promise<T>;
  fallback?: T;
  forceRefresh?: boolean;
  timeout?: number;
}

class DataFetcher {
  private cache: DataCache;

  constructor() {
    this.cache = new DataCache();
  }

  async fetch<T>(options: DataRequestOptions<T>): Promise<T> {
    const {
      key,
      type = 'daily',
      fetcher,
      fallback,
      forceRefresh = false,
      timeout = 10000,
    } = options;

    // 1. 尝试从缓存获取
    if (!forceRefresh) {
      const cached = await this.cache.get<T>(key, type);
      if (cached !== null) {
        return cached;
      }
    }

    // 2. 发起网络请求（带超时）
    try {
      const data = await this.withTimeout(fetcher(), timeout);

      // 3. 缓存结果
      await this.cache.set(key, data, type);

      return data;
    } catch (error) {
      console.warn(`数据请求失败 [${key}]:`, error);

      // 4. 降级：返回缓存中的旧数据
      const cached = await this.cache.get<T>(key, type);
      if (cached !== null) {
        console.log(`使用缓存旧数据 [${key}]`);
        return cached;
      }

      // 5. 降级：返回fallback数据
      if (fallback !== undefined) {
        console.log(`使用fallback数据 [${key}]`);
        return fallback;
      }

      // 6. 抛出错误
      throw error;
    }
  }

  // 超时控制
  private withTimeout<T>(promise: Promise<T>, timeout: number): Promise<T> {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error('请求超时'));
      }, timeout);

      promise
        .then((result) => {
          clearTimeout(timer);
          resolve(result);
        })
        .catch((error) => {
          clearTimeout(timer);
          reject(error);
        });
    });
  }

  // 强制刷新
  async refresh<T>(options: Omit<DataRequestOptions<T>, 'forceRefresh'>): Promise<T> {
    return this.fetch({ ...options, forceRefresh: true });
  }

  // 清除指定缓存
  async invalidate(key: string): Promise<void> {
    await this.cache.delete(key);
  }

  // 清除所有缓存
  async clearCache(): Promise<void> {
    await this.cache.clear();
  }
}

// ── 导出单例 ───────────────────────────────────────────────────

export const dataCache = new DataCache();
export const dataFetcher = new DataFetcher();

// ── 便捷函数 ───────────────────────────────────────────────────

export async function getCachedData<T>(key: string, type?: string): Promise<T | null> {
  return dataCache.get<T>(key, type);
}

export async function setCachedData<T>(key: string, data: T, type?: string): Promise<void> {
  return dataCache.set(key, data, type);
}

export async function fetchWithCache<T>(
  key: string,
  fetcher: () => Promise<T>,
  type?: string,
  fallback?: T
): Promise<T> {
  return dataFetcher.fetch({ key, fetcher, type, fallback });
}

// ── 导出类型 ───────────────────────────────────────────────────

export type { CacheConfig, CacheItem, DataRequestOptions };