"""Pydantic models for data validation and structure."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class DocumentInsert(BaseModel):
    """Model for inserting a document."""

    data: dict[str, Any] = Field(..., description="Document data to insert")
    table: str = Field(default="default", description="Table name")

    @field_validator("data")
    @classmethod
    def validate_data_not_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure data is not empty."""
        if not v:
            raise ValueError("Document data cannot be empty")
        return v


class DocumentQuery(BaseModel):
    """Model for querying documents."""

    field: str | None = Field(default=None, description="Field name to query")
    value: Any = Field(default=None, description="Value to match")
    table: str = Field(default="default", description="Table name")

    @field_validator("field", "value")
    @classmethod
    def validate_field_value_pair(cls, v: Any) -> Any:
        """Validate that field and value are provided together."""
        return v


class DocumentUpdate(BaseModel):
    """Model for updating documents."""

    field: str = Field(..., description="Field name to match")
    value: Any = Field(..., description="Value to match")
    updates: dict[str, Any] = Field(..., description="Fields to update")
    table: str = Field(default="default", description="Table name")

    @field_validator("updates")
    @classmethod
    def validate_updates_not_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Ensure updates is not empty."""
        if not v:
            raise ValueError("Updates cannot be empty")
        return v


class DocumentDelete(BaseModel):
    """Model for deleting documents."""

    field: str = Field(..., description="Field name to match")
    value: Any = Field(..., description="Value to match")
    table: str = Field(default="default", description="Table name")


class TableStats(BaseModel):
    """Model for table statistics."""

    name: str = Field(..., description="Table name")
    document_count: int = Field(..., description="Number of documents in table")
    sample_fields: list[str] = Field(default_factory=list, description="Sample field names")


class DatabaseStats(BaseModel):
    """Model for database statistics."""

    database_path: str = Field(..., description="Path to database file")
    database_size_bytes: int = Field(..., description="Size of database file in bytes")
    total_tables: int = Field(..., description="Total number of tables")
    tables: dict[str, dict[str, int]] = Field(default_factory=dict, description="Table statistics")


class OperationResult(BaseModel):
    """Model for operation results."""

    success: bool = Field(..., description="Whether operation succeeded")
    message: str = Field(..., description="Result message")
    data: dict[str, Any] | None = Field(default=None, description="Result data")
    error: str | None = Field(default=None, description="Error message if failed")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "message": "Document inserted successfully",
                    "data": {"doc_id": 1},
                    "error": None,
                }
            ]
        }
    }
