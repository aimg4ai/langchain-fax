from setuptools import setup, find_packages

# Read the content of README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="langchain-fax",
    version="0.1.0",
    author="Jim Griffin",
    author_email="jim@aimast.org",
    description="A LangChain integration for sending faxes using Alohi's Fax.Plus API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aimg4ai/langchain-fax",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "langchain>=0.1.0",
        "faxplus",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "graph": ["langgraph>=0.0.10"],
        "dev": ["pytest", "black", "isort"],
    }
)
