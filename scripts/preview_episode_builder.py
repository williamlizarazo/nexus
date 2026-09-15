import argparse
import os
from collections import Counter

from dotenv import load_dotenv
from supabase import create_client

from memory_core.adapters.supabase.research_activity_source import (
    SupabaseResearchActivitySource,
)
from memory_core.episode_builder.builder import DeterministicEpisodeBuilder


load_dotenv()

parser = argparse.ArgumentParser()
parser.add_argument("--project-id", default=None)
args = parser.parse_args()

client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)

source = SupabaseResearchActivitySource(client)
project_id = args.project_id

if project_id is None:
    available = source.list_searches(limit=500)

    if not available:
        raise RuntimeError("No hay búsquedas disponibles.")

    counts = Counter(item.project_id for item in available)
    project_id = counts.most_common(1)[0][0]

print("PROJECT:", project_id)

searches = source.list_searches(project_id=project_id, limit=1000)
results = source.list_search_results(project_id=project_id, limit=5000)
annotations = source.list_annotations(project_id=project_id, limit=2000)
activities = source.list_activities(project_id=project_id, limit=5000)

builder = DeterministicEpisodeBuilder()
drafts = builder.build(
    project_id=project_id,
    searches=searches,
    search_results=results,
    annotations=annotations,
    activities=activities,
)

print()
print("SEARCHES:", len(searches))
print("RESULTS:", len(results))
print("ANNOTATIONS:", len(annotations))
print("ACTIVITIES:", len(activities))
print("EPISODES:", len(drafts))
print()

for index, draft in enumerate(drafts, start=1):
    print(f"EPISODE {index}")
    print(" id:", draft.episode.episode_id)
    print(" searches:", len(draft.search_ids))
    print(" items:", len(draft.items))
    print(" edges:", len(draft.edges))
    print(" search_ids:", draft.search_ids)
    print()
