from setuptools import setup, find_packages

setup(
    name="short-win-ai-trader",
    version="1.0.0",
    description="短线致胜 AI 交易智能体 — A股超短线AI决策系统",
    author="lianhuaijin",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.9.0",
        "asyncio-throttle>=1.0.0",
        "pandas>=2.1.0",
        "numpy>=1.26.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "pyyaml>=6.0.1",
        "structlog>=23.2.0",
        "openpyxl>=3.1.0",
        "python-dateutil>=2.8.2",
        "click>=8.1.0",
        "rich>=13.7.0",
        "tabulate>=0.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "swat=short_win_ai_trader.cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
