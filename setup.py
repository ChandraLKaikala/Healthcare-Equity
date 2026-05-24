from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="healthcare-equity-bias-detection",
    version="1.0.0",
    author="Healthcare Analytics Team",
    description="Enterprise-grade healthcare equity bias detection and intervention system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/org/equity-bias-detection",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "anthropic>=0.40.0",
        "pandas>=2.1.4",
        "numpy>=1.26.3",
        "duckdb>=0.9.4",
        "pydantic>=2.5.3",
        "scipy>=1.11.4",
        "scikit-learn>=1.3.2",
        "statsmodels>=0.14.1",
        "plotly>=5.18.0",
        "streamlit>=1.29.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "equity-setup-db=scripts.setup_db:main",
            "equity-generate-data=scripts.generate_synthetic_data:main",
            "equity-pipeline=scripts.run_full_pipeline:main",
            "equity-dashboard=dashboard.app:main",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Medical Science Apps",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
