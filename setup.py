from setuptools import setup, find_packages

setup(
    name="odoo-liberate",
    version="0.1.0",
    description="A zero-dependency CLI tool to migrate Odoo Enterprise databases to Community Edition by stripping proprietary artifacts.",
    author="tiborrr",
    author_email="tibor@casteleijn.com",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "odoo-liberate=odoo_liberate.cli:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
