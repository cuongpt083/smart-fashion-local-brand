from .rfm_analyzer import (
    calculate_rfm,
    segment_summary,
    calculate_rfm_kpis,
    get_segment_recommendation,
    classify_rfm_segment
)

# Alias for backward compatibility
segment_customers = calculate_rfm

__all__ = [
    "calculate_rfm",
    "segment_customers",
    "segment_summary",
    "calculate_rfm_kpis",
    "get_segment_recommendation",
    "classify_rfm_segment"
]
