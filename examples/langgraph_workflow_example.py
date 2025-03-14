"""
Example of using Fax.Plus in a LangGraph workflow

This example demonstrates how to use the Fax.Plus tools within a LangGraph
workflow that processes documents, decides whether to fax them, and monitors
the status of sent faxes. It demonstrates a workflow that:

- Analyzes a document to determine if it should be faxed
- Generates a subject line for the fax
- Sends the fax
- Error handling for missing credentials
- Checks the status of the sent fax
- Provides an output to recap the end-to-end process

The workflow makes use of the following LangGraph concepts:

- Using conditional edges to make decisions based on document analysis
- Transforming data between nodes with edge functions
- Integrating tool nodes (for Fax.Plus operations) with regular processing nodes
- Maintaining state throughout the workflow
- Handling multi-step processes with dependencies

You can customize the document analysis criteria and also the subject-line 
generation to match your own business rules. 

This example can be extended for more complex document processing 
and faxing workflows.

"""

import os
import json
from typing import Dict, Any, TypedDict, List, Annotated

from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Import LangGraph components
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.graph.nodes.tool_nodes import ToolInvocation

# Import our custom tool
from langchain_fax import FaxPlusTool, FaxPlusStatusTool


# Define our state type
class State(TypedDict):
    """State for the document processing workflow."""
    messages: List[Any]
    document_path: str
    document_type: str
    recipient_fax: str
    should_fax: bool
    fax_id: str
    subject: str


def create_fax_workflow(api_key: str, account_id: str):
    """
    Creates a LangGraph workflow for processing documents and faxing them.
    
    Args:
        api_key: Fax.Plus API key
        account_id: Fax.Plus account ID
        
    Returns:
        A compiled LangGraph workflow
    """
    # Set up the LLM
    llm = ChatOpenAI(temperature=0)

    # Set up the tools
    fax_tool = FaxPlusTool(
        api_key=api_key,
        account_id=account_id
    )

    fax_status_tool = FaxPlusStatusTool(
        api_key=api_key,
        account_id=account_id
    )

    # Create tool nodes
    fax_node = ToolNode(fax_tool)
    status_node = ToolNode(fax_status_tool)

    # Document analyzer prompt
    analyzer_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are an assistant that analyzes documents and determines if they should be faxed.
        If the document is of type 'invoice', 'contract', 'legal_document', or 'medical_record', it should be faxed.
        Other document types are evaluated case by case."""),
        HumanMessage(content="""I have a document at path: {document_path}
        The document type is: {document_type}
        The recipient's fax number is: {recipient_fax}
        
        Should this document be faxed? Answer with YES or NO and provide a brief explanation.""")
    ])

    # Subject generator prompt
    subject_prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""You are an assistant that creates appropriate subject lines for faxes.
        The subject should be professional, concise, and clearly indicate the document type."""),
        HumanMessage(content="""Create a subject line for a fax containing a {document_type} document.""")
    ])

    def analyze_document(state: State) -> State:
        """Analyze the document and determine if it should be faxed."""
        # Generate prompt with document details
        response = llm.invoke(
            analyzer_prompt.format_messages(
                document_path=state["document_path"],
                document_type=state["document_type"],
                recipient_fax=state["recipient_fax"]
            )
        )
        
        # Determine if document should be faxed
        should_fax = "YES" in response.content.upper()
        
        # Add to messages
        messages = state["messages"] + [response]
        
        # Return updated state
        return {
            **state,
            "messages": messages,
            "should_fax": should_fax
        }

    def generate_subject(state: State) -> State:
        """Generate an appropriate subject line for the fax."""
        # Generate subject line
        response = llm.invoke(
            subject_prompt.format_messages(
                document_type=state["document_type"]
            )
        )
        
        # Extract subject from response
        subject = response.content.strip()
        if ":" in subject:
            # If response format is "Subject: XXX", extract just the XXX part
            subject = subject.split(":", 1)[1].strip()
        
        # Add to messages
        messages = state["messages"] + [
            AIMessage(content=f"Generated subject: {subject}")
        ]
        
        # Return updated state
        return {
            **state,
            "messages": messages,
            "subject": subject
        }

    def prepare_fax_data(state: State) -> ToolInvocation:
        """Prepare the fax data for sending."""
        fax_data = {
            "fax_number": state["recipient_fax"],
            "subject": state["subject"],
            "file_path": state["document_path"],
            "comment": f"Automated fax of {state['document_type']} document"
        }
        
        return ToolInvocation(
            tool="faxplus",
            tool_input=json.dumps(fax_data)
        )

    def process_fax_result(state: State, result: str) -> State:
        """Process the result of the fax sending operation."""
        # Extract fax ID from result
        fax_id = ""
        if "Fax ID:" in result:
            fax_id = result.split("Fax ID:")[1].strip()
        
        # Add to messages
        messages = state["messages"] + [
            AIMessage(content=result)
        ]
        
        # Return updated state
        return {
            **state,
            "messages": messages,
            "fax_id": fax_id
        }

    def prepare_status_check(state: State) -> ToolInvocation:
        """Prepare the data for checking fax status."""
        status_data = {
            "fax_id": state["fax_id"]
        }
        
        return ToolInvocation(
            tool="faxplus_status",
            tool_input=json.dumps(status_data)
        )

    def process_status_result(state: State, result: str) -> State:
        """Process the result of the status check operation."""
        # Add to messages
        messages = state["messages"] + [
            AIMessage(content=f"Current fax status: {result}")
        ]
        
        # Return updated state
        return {
            **state,
            "messages": messages,
        }

    def should_send_fax(state: State) -> str:
        """Determine if we should send a fax based on the analysis."""
        if state["should_fax"]:
            return "send_fax"
        else:
            return "end"

    def has_fax_id(state: State) -> str:
        """Check if we have a fax ID to check status."""
        if state.get("fax_id", ""):
            return "check_status"
        else:
            return "end"

    # Create the graph
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("analyze_document", analyze_document)
    workflow.add_node("generate_subject", generate_subject)
    workflow.add_node("send_fax", fax_node)
    workflow.add_node("process_fax_result", process_fax_result)
    workflow.add_node("check_status", status_node)
    workflow.add_node("process_status_result", process_status_result)

    # Connect analyze_document to conditional path
    workflow.add_conditional_edges(
        "analyze_document",
        should_send_fax,
        {
            "send_fax": "generate_subject",
            "end": END
        }
    )
    
    # Connect generate_subject to send_fax
    workflow.add_edge("generate_subject", "send_fax", prepare_fax_data)
    
    # Connect send_fax to process_fax_result
    workflow.add_edge("send_fax", "process_fax_result")
    
    # Connect process_fax_result to conditional path
    workflow.add_conditional_edges(
        "process_fax_result",
        has_fax_id,
        {
            "check_status": "check_status",
            "end": END
        }
    )
    
    # Connect check_status to process_status_result
    workflow.add_edge("check_status", "process_status_result")
    
    # Set entry point
    workflow.set_entry_point("analyze_document")

    # Compile the graph
    return workflow.compile()


def main():
    """Run the example workflow."""
    # Get API credentials from environment
    api_key = os.environ.get("FAXPLUS_API_KEY")
    account_id = os.environ.get("FAXPLUS_ACCOUNT_ID")
    
    if not api_key or not account_id:
        print("ERROR: Please set FAXPLUS_API_KEY and FAXPLUS_ACCOUNT_ID environment variables.")
        return
    
    # Create the workflow
    workflow = create_fax_workflow(api_key, account_id)
    
    # Example document details - you would get these from user input or your application
    document_details = {
        "messages": [],
        "document_path": "/path/to/example/invoice.pdf",
        "document_type": "invoice",
        "recipient_fax": "+14155552671",
        "should_fax": False,  # This will be determined by the workflow
        "fax_id": "",         # This will be filled in if a fax is sent
        "subject": ""         # This will be generated by the workflow
    }
    
    # Run the workflow
    print("Starting document workflow...")
    result = workflow.invoke(document_details)
    
    # Print final messages
    print("\nWorkflow completed")
    print("==================")
    for message in result["messages"]:
        if hasattr(message, "content"):
            print(f"{message.type}: {message.content}")
    
    # Print fax result if applicable
    if result.get("fax_id"):
        print(f"\nDocument was faxed successfully. Fax ID: {result['fax_id']}")
    else:
        print("\nDocument was not faxed.")


if __name__ == "__main__":
    # Handle a name error that might occur with END
    from langgraph.graph.graph import END
    main()