from setuptools import setup, find_packages

setup(
    name="gitingest",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "tokencost",
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-asyncio',
        ],
    },
    entry_points={
        "console_scripts": [
            "gitingest=gitingest.cli:main",
        ],
    },
    python_requires=">=3.6",
    author="Romain Courtois",
    author_email="romain@coderamp.io",
    description="A tool to analyze and create text dumps of git repositories",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/cyclotruc/gitingest",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)