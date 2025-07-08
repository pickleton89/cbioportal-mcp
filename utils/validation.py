"""
Input validation utilities for the cBioPortal MCP server.

This module provides reusable validation functions for common parameters.
"""

from typing import Optional, List


def validate_page_params(
    page_number: int,
    page_size: int,
    limit: Optional[int] = None,
) -> None:
    """
    Validate pagination parameters.
    
    Args:
        page_number: Page number (0-based)
        page_size: Number of items per page
        limit: Optional limit on total results
        
    Raises:
        TypeError: If parameters are not the correct type
        ValueError: If parameters have invalid values
    """
    if not isinstance(page_number, int):
        raise TypeError("page_number must be an integer")
    if page_number < 0:
        raise ValueError("page_number must be non-negative")
        
    if not isinstance(page_size, int):
        raise TypeError("page_size must be an integer")
    if page_size <= 0:
        raise ValueError("page_size must be positive")
        
    if limit is not None:
        if not isinstance(limit, int):
            raise TypeError("limit must be an integer if provided")
        if limit < 0:
            raise ValueError("limit must be non-negative if provided")


def validate_sort_params(
    sort_by: Optional[str],
    direction: str,
) -> None:
    """
    Validate sorting parameters.
    
    Args:
        sort_by: Field to sort by (optional)
        direction: Sort direction (ASC or DESC)
        
    Raises:
        TypeError: If parameters are not the correct type
        ValueError: If direction is not valid
    """
    if sort_by is not None and not isinstance(sort_by, str):
        raise TypeError("sort_by must be a string if provided")
        
    if not isinstance(direction, str) or direction.upper() not in ["ASC", "DESC"]:
        raise ValueError("direction must be 'ASC' or 'DESC'")


def validate_study_id(study_id: str) -> None:
    """
    Validate study ID parameter.
    
    Args:
        study_id: Study identifier
        
    Raises:
        TypeError: If study_id is not a string
        ValueError: If study_id is empty
    """
    if not isinstance(study_id, str):
        raise TypeError("study_id must be a string")
    if not study_id:
        raise ValueError("study_id cannot be empty")


def validate_gene_id(gene_id: str) -> None:
    """
    Validate gene ID parameter.
    
    Args:
        gene_id: Gene identifier
        
    Raises:
        TypeError: If gene_id is not a string
        ValueError: If gene_id is empty
    """
    if not isinstance(gene_id, str):
        raise TypeError("gene_id must be a string")
    if not gene_id:
        raise ValueError("gene_id cannot be empty")


def validate_keyword(keyword: str) -> None:
    """
    Validate keyword parameter for search operations.
    
    Args:
        keyword: Search keyword
        
    Raises:
        TypeError: If keyword is not a string
        ValueError: If keyword is empty
    """
    if not isinstance(keyword, str):
        raise TypeError("keyword must be a string")
    if not keyword:
        raise ValueError("keyword cannot be empty")


def validate_gene_ids_list(gene_ids: List[str]) -> None:
    """
    Validate a list of gene IDs.
    
    Args:
        gene_ids: List of gene identifiers
        
    Raises:
        TypeError: If gene_ids is not a list or contains non-strings
        ValueError: If gene_ids is empty or contains empty strings
    """
    if not isinstance(gene_ids, list):
        raise TypeError("gene_ids must be a list")
    if not gene_ids:
        raise ValueError("gene_ids cannot be empty")
    for gene_id in gene_ids:
        if not isinstance(gene_id, str):
            raise TypeError("All gene_ids must be strings")
        if not gene_id:
            raise ValueError("gene_ids cannot contain empty strings")


def validate_gene_id_type(gene_id_type: str) -> None:
    """
    Validate gene ID type parameter.
    
    Args:
        gene_id_type: Type of gene identifier
        
    Raises:
        ValueError: If gene_id_type is not valid
    """
    valid_types = ["ENTREZ_GENE_ID", "HUGO_GENE_SYMBOL"]
    if gene_id_type not in valid_types:
        raise ValueError(f"gene_id_type must be one of {valid_types}")


def validate_projection(projection: str) -> None:
    """
    Validate projection parameter.
    
    Args:
        projection: Level of detail to return
        
    Raises:
        ValueError: If projection is not valid
    """
    valid_projections = ["ID", "SUMMARY", "DETAILED", "META"]
    if projection.upper() not in valid_projections:
        raise ValueError(f"projection must be one of {valid_projections}")


def validate_clinical_data_type(clinical_data_type: str) -> None:
    """
    Validate clinical data type parameter.
    
    Args:
        clinical_data_type: Type of clinical data
        
    Raises:
        ValueError: If clinical_data_type is not valid
    """
    valid_types = ["PATIENT", "SAMPLE"]
    if clinical_data_type not in valid_types:
        raise ValueError(f"clinical_data_type must be one of {valid_types}")