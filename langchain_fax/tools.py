"""
Fax.Plus LangChain Tool integration

This module provides LangChain tools for sending faxes via the Fax.Plus API.
"""

import os
import base64
from typing import Dict, List, Optional, Union
import json
from pydantic import BaseModel, Field

import faxplus
from faxplus.api import files_api, outbox_api, accounts_api
from faxplus.models import FaxCategory, FaxDirection, PayloadOutbox, PayloadOutboxFax

from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun


class FaxPlusTool(BaseTool):
    """Tool for sending faxes using the Fax.Plus API."""
    
    name = "faxplus"
    description = """
    Useful for sending faxes to a specified fax number.
    Input should be a JSON object with the following keys:
    - fax_number: The recipient's fax number in E.164 format (e.g., +14155552671)
    - subject: Subject of the fax
    - file_path: Path to the file to be faxed (PDF, TIFF, or other supported format)
    - comment: (Optional) Comment for the fax
    """
    
    api_key: str = Field(..., description="Fax.Plus API key")
    account_id: str = Field(..., description="Fax.Plus account ID")
    
    def _init_client(self) -> None:
        """Initialize the Fax.Plus client."""
        configuration = faxplus.Configuration()
        configuration.api_key['ApiKey'] = self.api_key
        
        # Initialize API clients
        self.files_api = files_api.FilesApi(faxplus.ApiClient(configuration))
        self.outbox_api = outbox_api.OutboxApi(faxplus.ApiClient(configuration))
        self.accounts_api = accounts_api.AccountsApi(faxplus.ApiClient(configuration))
    
    def _run(
        self, 
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Run the tool."""
        try:
            # Parse the input JSON
            input_data = json.loads(query)
            
            # Extract parameters
            fax_number = input_data.get("fax_number")
            subject = input_data.get("subject")
            file_path = input_data.get("file_path")
            comment = input_data.get("comment", "")
            
            # Validate required parameters
            if not fax_number:
                return "Error: Recipient fax number is required"
            if not subject:
                return "Error: Subject is required"
            if not file_path:
                return "Error: File path is required"
            
            # Validate file exists
            if not os.path.exists(file_path):
                return f"Error: File not found at {file_path}"
            
            # Initialize the client if not already done
            if not hasattr(self, 'files_api'):
                self._init_client()
            
            # Upload the file
            with open(file_path, "rb") as file:
                file_content = file.read()
            
            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_name)[1].lower()
            
            # Determine appropriate mime type
            mime_type = self._get_mime_type(file_extension)
            
            # Upload the file
            uploaded_file = self.files_api.upload_file(
                self.account_id,
                file=file_content,
                filename=file_name,
                content_type=mime_type
            )
            
            # Create the fax payload
            fax = PayloadOutboxFax(
                to=fax_number,
                subject=subject,
                comment=comment,
                file_id=uploaded_file.id,
                direction=FaxDirection.OUTBOUND,
                category=FaxCategory.GENERAL
            )
            
            payload = PayloadOutbox(fax=fax)
            
            # Send the fax
            fax_result = self.outbox_api.send_fax(self.account_id, payload=payload)
            
            return f"Fax successfully queued. Fax ID: {fax_result.id}"
            
        except json.JSONDecodeError:
            return "Error: Invalid JSON input. Please provide a valid JSON object."
        except Exception as e:
            return f"Error sending fax: {str(e)}"
    
    def _get_mime_type(self, extension: str) -> str:
        """Get appropriate MIME type based on file extension."""
        mime_types = {
            ".pdf": "application/pdf",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".txt": "text/plain"
        }
        return mime_types.get(extension, "application/octet-stream")


class FaxPlusStatusTool(BaseTool):
    """Tool for checking the status of a sent fax via the Fax.Plus API."""
    
    name = "faxplus_status"
    description = """
    Useful for checking the status of a previously sent fax.
    Input should be a JSON object with the following keys:
    - fax_id: The ID of the fax to check the status of
    """
    
    api_key: str = Field(..., description="Fax.Plus API key")
    account_id: str = Field(..., description="Fax.Plus account ID")
    
    def _init_client(self) -> None:
        """Initialize the Fax.Plus client."""
        configuration = faxplus.Configuration()
        configuration.api_key['ApiKey'] = self.api_key
        
        # Initialize API clients
        self.outbox_api = outbox_api.OutboxApi(faxplus.ApiClient(configuration))
    
    def _run(
        self, 
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Run the tool."""
        try:
            # Parse the input JSON
            input_data = json.loads(query)
            
            # Extract parameters
            fax_id = input_data.get("fax_id")
            
            # Validate required parameters
            if not fax_id:
                return "Error: Fax ID is required"
            
            # Initialize the client if not already done
            if not hasattr(self, 'outbox_api'):
                self._init_client()
            
            # Get fax status
            fax_status = self.outbox_api.get_outbox_fax(self.account_id, fax_id)
            
            # Format response
            status_info = {
                "fax_id": fax_id,
                "status": fax_status.status,
                "completed": fax_status.completed,
                "cost": fax_status.cost,
                "pagecount": fax_status.pagecount,
                "created_at": fax_status.created_at
            }
            
            return json.dumps(status_info, indent=2)
            
        except json.JSONDecodeError:
            return "Error: Invalid JSON input. Please provide a valid JSON object."
        except Exception as e:
            return f"Error checking fax status: {str(e)}"
