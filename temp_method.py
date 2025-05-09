def search_studies(
        self, 
        keyword: str,
        page_number: int = 0,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        direction: str = "ASC",
        limit: Optional[int] = None
    ) -> Dict:
        """
        Search for cancer studies by keyword in their name or description with pagination support.

        Args:
            keyword: Keyword to search for (e.g., 'melanoma', 'lung cancer').
            page_number: Page number (0-indexed) to retrieve
            page_size: Number of studies per page (default: 50)
            sort_by: Field to sort by. Valid options: "studyId", "name", "description",
                    "publicStudy", "cancerTypeId", "status"
            direction: Sort direction ("ASC" or "DESC")
            limit: Maximum total results to return across all pages
                    Set to None to use pagination, 0 for all results

        Returns:
            A dictionary containing:
            - studies: List of study objects matching the keyword
            - pagination: Dictionary with pagination metadata
              - page: Current page number
              - page_size: Items per page
              - total_found: Total number of studies matching criteria
              - has_more: Boolean indicating if more pages exist
        """
        try:
            # Special case for "all results" request
            if limit == 0:
                page_size = 10000000  # Very large number to get all results

            # Fetch all studies first - the API doesn't have search parameters
            all_studies = self._make_api_request("studies")

            # Filter studies where the keyword appears in the name or description (case-insensitive)
            keyword_lower = keyword.lower()
            matching_studies = [
                study
                for study in all_studies
                if keyword_lower in study.get("name", "").lower()
                or keyword_lower in study.get("description", "").lower()
            ]

            # Sort results if requested
            if sort_by:
                reverse = direction.upper() == "DESC"
                # Handle nested sorting fields safely
                matching_studies.sort(
                    key=lambda s: str(s.get(sort_by, "")), 
                    reverse=reverse
                )

            # Get total count before pagination
            total_count = len(matching_studies)

            # Apply pagination
            start_idx = page_number * page_size
            end_idx = start_idx + page_size
            paginated_studies = matching_studies[start_idx:end_idx]

            # Apply limit if specified (and not 0)
            if limit and limit > 0 and len(paginated_studies) > limit:
                paginated_studies = paginated_studies[:limit]

            # Determine if more results are available
            has_more = end_idx < total_count

            # Return paginated results with metadata
            return {
                "studies": paginated_studies,
                "pagination": {
                    "page": page_number,
                    "page_size": page_size,
                    "total_found": total_count,
                    "has_more": has_more
                }
            }
        except Exception as e:
            # Return an error dictionary if the process fails
            return {"error": f"Failed to search studies for '{keyword}': {str(e)}"}
