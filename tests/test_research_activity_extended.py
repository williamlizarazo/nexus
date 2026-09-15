import os

from dotenv import load_dotenv
from supabase import create_client

from memory_core.adapters.supabase.research_activity_source import (
    SupabaseResearchActivitySource,
)

load_dotenv()

client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)

source = SupabaseResearchActivitySource(client)

activities = source.list_activities(limit=5)
results = source.list_search_results(limit=5)

print("ACTIVITIES:", len(activities))

for activity in activities:
    print(
        activity.activity_type,
        "|",
        activity.trace_id,
        "|",
        activity.document_id,
    )

print()

print("SEARCH RESULTS:", len(results))

for result in results:
    print(
        result.trace_id,
        "| doc:",
        result.doc_id,
        "| chunk:",
        result.chunk_id,
        "| rank:",
        result.rank_position,
    )

print("Lectura extendida OK")