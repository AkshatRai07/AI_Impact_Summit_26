from pydantic import BaseModel
from typing import List, Optional

class ApplyPolicy(BaseModel):
    max_applications_per_day: int = 50
    min_match_threshold: float = 0.3  # Minimum skill overlap
    blocked_companies: List[str] = []
    blocked_role_types: List[str] = []
    location_constraints: List[str] = []  # Empty = no constraint
    remote_only: bool = False
    enabled: bool = True  # Kill switch
