from fastapi import Query


class PaginationParams:
    """Reusable pagination query params for list endpoints"""

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(0, ge=0, le=1000, description="Max items to return (0 = no limit)"),
    ):
        self.skip = skip
        self.limit = limit
