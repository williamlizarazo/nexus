import os

from dotenv import load_dotenv
from supabase import create_client

from memory_core.adapters.supabase.episode_repository import (
    SupabaseEpisodeRepository,
)
from memory_core.domain.episode import ResearchEpisode
from memory_core.domain.episode_item import ResearchEpisodeItem
from memory_core.domain.episode_edge import ResearchEpisodeEdge
from memory_core.domain.episode_analysis import ResearchEpisodeAnalysis


load_dotenv()

client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)

repository = SupabaseEpisodeRepository(client)


# 1. Episodio
episode = ResearchEpisode(
    scope_type="project",
    scope_id="test-project-full",
)

repository.save_episode(episode)


# 2. Items
search_item = ResearchEpisodeItem(
    episode_id=episode.episode_id,
    source_type="search",
    source_id="search-test-001",
    role="exploration",
)

annotation_item = ResearchEpisodeItem(
    episode_id=episode.episode_id,
    source_type="annotation",
    source_id="annotation-test-001",
    role="analysis",
)

repository.add_item(search_item)
repository.add_item(annotation_item)


# 3. Edge
edge = ResearchEpisodeEdge(
    episode_id=episode.episode_id,
    source_item_id=search_item.item_id,
    target_item_id=annotation_item.item_id,
    relation_type="annotation_from_search",
    relation_score=1.0,
    evidence={
        "reason": "test_integrated_episode"
    },
)

repository.add_edge(edge)


# 4. Analysis
analysis = ResearchEpisodeAnalysis(
    episode_id=episode.episode_id,
    version=1,
    summary="Episodio integrado de prueba.",
    entities=[
        {
            "name": "FARC",
            "type": "organization",
        }
    ],
    topics=[
        {
            "name": "conflicto armado"
        }
    ],
)

repository.save_analysis(analysis)


# 5. Recuperación
loaded_episode = repository.get_episode(episode.episode_id)
items = repository.list_items(episode.episode_id)
edges = repository.list_edges(episode.episode_id)
analyses = repository.list_analyses(episode.episode_id)


# 6. Validaciones
assert loaded_episode is not None
assert len(items) == 2
assert len(edges) == 1
assert len(analyses) == 1

assert edges[0].relation_type == "annotation_from_search"
assert analyses[0].version == 1


print("EPISODIO:", loaded_episode.episode_id)
print("ITEMS:", len(items))
print("EDGES:", len(edges))
print("ANALYSES:", len(analyses))
print("Persistencia episodica completa OK")