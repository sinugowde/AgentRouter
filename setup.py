from setuptools import setup, find_packages

setup(
    name="agentrouter",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    extras_require={
        "langchain": ["langchain-core>=0.2.0"],
        "anthropic": ["anthropic>=0.20.0"],
    },
    entry_points={
        "console_scripts": [
            "agentrouter=agentrouter.cli:main",
        ],
    },
    python_requires=">=3.8",
)
