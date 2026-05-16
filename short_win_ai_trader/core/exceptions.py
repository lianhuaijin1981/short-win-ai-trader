"""自定义异常定义"""


class SWATException(Exception):
    """基础异常"""
    pass


class ConfigError(SWATException):
    """配置错误"""
    pass


class DataSourceError(SWATException):
    """数据源错误"""
    pass


class iFindAPIError(DataSourceError):
    """iFind API 调用错误"""
    pass


class CacheError(SWATException):
    """缓存错误"""
    pass


class ModuleError(SWATException):
    """模块错误"""
    pass


class ValidationError(SWATException):
    """数据验证错误"""
    pass


class RiskTriggerError(SWATException):
    """风险触发错误"""
    pass
