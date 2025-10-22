from setuptools import setup, find_packages

setup(
    name="trade-tracker",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "python-dotenv>=1.0.0",
        "pandas>=2.1.0",
        "numpy>=1.26.0",
        "plotly>=5.18.0",
        "dash>=2.14.0",
        "cryptography>=41.0.0",
        "pycryptodome>=3.19.0",
        # "ibapi>=9.81.1",  # Optional - Interactive Brokers API
        "requests>=2.31.0",
        "python-dateutil>=2.8.2",
        "tzdata>=2023.3",
    ],
    python_requires=">=3.10",
)
