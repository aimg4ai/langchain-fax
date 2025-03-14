# langchain-fax
A LangChain integration for sending faxes using Alohi's Fax.Plus API.

## LangChain Fax Integration

A LangChain integration for sending faxes using Alohi's Fax.Plus API. This package allows LangChain agents to send faxes and check fax status programmatically.

Step 1:
If you don't have Fax.Plus API, get that first. https://www.fax.plus/#67994

## Installation

Install the package using pip:

```bash
pip install langchain-fax
```

If you want to use the LangGraph integration, you can install the extra dependencies:

```bash
pip install "langchain-fax[graph]"
```

## Prerequisites

1. A Fax.Plus account and ID. Sign up at Fax.Plus (https://www.fax.plus/#67994)
2. API Key from Fax.Plus (Note: An enterprise account is required)
3. A fax number. (Note: You can use your existing fax number or a virtual fax number. The Enterprise account comes with a free virtual fax number so this requirement does not require an extra step.)

## Quick Start

### Basic Usage

```python
import os
from langchain_fax.tools import FaxPlusTool

# Set up credentials
api_key = os.environ.get("FAXPLUS_API_KEY")
account_id = os.environ.get("FAXPLUS_ACCOUNT_ID")

# Initialize the tool
fax_tool = FaxPlusTool(
    api_key=api_key,
    account_id=account_id
)

# Send a fax
result = fax_tool.run(
    """{
        "fax_number": "+14151234567",
        "subject": "Test Fax",
        "file_path": "/path/to/document.pdf",
        "comment": "This is a test fax"
    }"""
)

print(result)
```

### Using with a LangChain Agent

```python
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from langchain_fax.tools import FaxPlusTool, FaxPlusStatusTool

# Set up the tools
fax_tool = FaxPlusTool(
    api_key=os.environ.get("FAXPLUS_API_KEY"),
    account_id=os.environ.get("FAXPLUS_ACCOUNT_ID")
)

fax_status_tool = FaxPlusStatusTool(
    api_key=os.environ.get("FAXPLUS_API_KEY"),
    account_id=os.environ.get("FAXPLUS_ACCOUNT_ID")
)

# Initialize the agent
agent = initialize_agent(
    tools=[fax_tool, fax_status_tool],
    llm=OpenAI(temperature=0),
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True
)

# Use the agent
agent.run("Please send a fax of my report.pdf file to +14151234567 with the subject 'Monthly Report'")
```

## LangGraph Integration

The package also supports LangGraph for creating complex workflows involving faxes:

```python
from langchain_fax.tools import FaxPlusTool
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

# See examples/langgraph_workflow_example.py for a complete example
```

## Configuration

### Environment Variables

You can set the following environment variables:

```bash
export FAXPLUS_API_KEY="your-api-key"
export FAXPLUS_ACCOUNT_ID="your-account-id"
```

## API Reference

### FaxPlusTool

Sends faxes using the Fax.Plus API.

**Parameters:**
- `api_key` (str): Your Fax.Plus API key
- `account_id` (str): Your Fax.Plus account ID

**Input Format:**
JSON object with the following keys:
- `fax_number`: The recipient's fax number in E.164 format (e.g., +14151234567)
- `subject`: Subject of the fax
- `file_path`: Path to the file to be faxed
- `comment` (Optional): Comment for the fax

### FaxPlusStatusTool

Checks the status of a sent fax.

**Parameters:**
- `api_key` (str): Your Fax.Plus API key
- `account_id` (str): Your Fax.Plus account ID

**Input Format:**
JSON object with the following key:
- `fax_id`: The ID of the fax to check

## Examples

For more examples, check the [examples](./examples) directory.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Links and Information

Fax.Plus is a faxing solution that's approprtiate for use with LangChain. Here's a quick overview:

- Send faxes without a fax machine or phone line.
- Receive: You'll get a local fax number from one of 40+ different countries of your choice to receive faxes.
- Faxes in the Fax.Plus archive are automatically encrypted with AES-256 bit encryption.
- Key Features: DDoS protection, encrypted secure storage of messages, ISO 27001, SOC 2, GDPR | CCPA | HIPAA compliance, TLS1.3 transport layer security, high volume faxing, blacklisting unwanted senders, and retry for failed faxes. For more, see: https://www.fax.plus/features
- Note: To use an API, you'll need an Enterprise-level plan which comes bundled with fax numbers.
- Existing Fax Number: If you already have a fax number, you can submit a porting request and transfer your current number to Fax.Plus for continuity purposes.
- Other Sending Options: You can also send and receive faxes outside of LangChain, using the mobile app available on iOS and Android platforms or via the www.fax.plus website.

API documentation

https://apidoc.fax.plus/get-started/introduction#fax-plus-rest-api

QuickStart Guide

https://apidoc.fax.plus/get-started/quickstart/

Python SDK

https://apidoc.fax.plus/backend-sdks/python

Javascript SDK

https://apidoc.fax.plus/backend-sdks/javascript

Support Center

https://help.alohi.com/hc/en-us/requests/new

LangChain Documentation

https://python.langchain.com/docs/get_started/introduction

LangGraph Documentation

https://python.langchain.com/docs/langgraph
