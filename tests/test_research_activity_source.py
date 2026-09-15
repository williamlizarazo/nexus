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

searches = source.list_searches(limit=5)
annotations = source.list_annotations(limit=5)

print("SEARCHES:", len(searches))

for search in searches:
    print(
        search.search_id,
        "|",
        search.search_type,
        "|",
        search.original_query,
    )

print()

print("ANNOTATIONS:", len(annotations))

for annotation in annotations:
    print(
        annotation.annotation_id,
        "|",
        annotation.annotation_type,
        "|",
        annotation.doc_id,
    )

print("Lectura real OK")