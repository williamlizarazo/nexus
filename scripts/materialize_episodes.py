import argparse
import os
from collections import Counter

from dotenv import load_dotenv
from supabase import create_client

from memory_core.adapters.supabase.episode_repository import (
    SupabaseEpisodeRepository,
)
from memory_core.adapters.supabase.research_activity_source import (
    SupabaseResearchActivitySource,
)
from memory_core.episode_builder.builder import DeterministicEpisodeBuilder
from memory_core.services.episode_materializer import EpisodeMaterializer


load_dotenv()

parser = argparse.ArgumentParser()

parser.add_argument(
    "--project-id",
    default=None,
)

parser.add_argument(
    "--apply",
    action="store_true",
    help="Persistir episodios en Supabase",
)

args = parser.parse_args()

client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)

source = SupabaseResearchActivitySource(client)
repository = SupabaseEpisodeRepository(client)
materializer = EpisodeMaterializer(repository)

project_id = args.project_id

if project_id is None:
    searches_available = source.list_searches(limit=500)

    if not searches_available:
        raise RuntimeError("No hay búsquedas disponibles.")

    counts = Counter(item.project_id for item in searches_available)
    project_id = counts.most_common(1)[0][0]

searches = source.list_searches(
    project_id=project_id,
    limit=1000,
)

results = source.list_search_results(
    project_id=project_id,
    limit=5000,
)

annotations = source.list_annotations(
    project_id=project_id,
    limit=2000,
)

activities = source.list_activities(
    project_id=project_id,
    limit=5000,
)

builder = DeterministicEpisodeBuilder()

drafts = builder.build(
    project_id=project_id,
    searches=searches,
    search_results=results,
    annotations=annotations,
    activities=activities,
)

print("PROJECT:", project_id)
print("SEARCHES:", len(searches))
print("EPISODES:", len(drafts))

for index, draft in enumerate(drafts, start=1):
    print(
        f"{index}.",
        draft.episode.episode_id,
        "| searches:",
        len(draft.search_ids),
        "| items:",
        len(draft.items),
        "| edges:",
        len(draft.edges),
        "| status:",
        draft.episode.status,
    )

if not args.apply:
    print()
    print("DRY RUN: no se escribio nada.")
    print("Use --apply para persistir.")
else:
    materializer.save(drafts)

    print()
    print("Materializacion completada.")
