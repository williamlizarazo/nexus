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

documents = source.list_documents(limit=5)
pages = source.list_pages(limit=5)
chunks = source.list_chunks(limit=5)

print("DOCUMENTS:", len(documents))
for item in documents:
    print(
        item.doc_id,
        "|",
        item.display_name,
    )

print()

print("PAGES:", len(pages))
for item in pages:
    print(
        item.doc_id,
        "| page:",
        item.page_num,
        "| searchable:",
        item.has_searchable_text,
    )

print()

print("CHUNKS:", len(chunks))
for item in chunks:
    print(
        item.chunk_id,
        "| doc:",
        item.doc_id,
        "| pages:",
        item.page_num_start,
        "-",
        item.page_num_end,
    )

print("Lectura estructural completa OK")
