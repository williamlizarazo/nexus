import os

from dotenv import load_dotenv
from supabase import create_client

from memory_core.adapters.supabase.episode_repository import (
    SupabaseEpisodeRepository,
)
from memory_core.domain.episode import ResearchEpisode


load_dotenv()

url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_KEY"]

client = create_client(url, key)
repository = SupabaseEpisodeRepository(client)

episode = ResearchEpisode(
    scope_type="project",
    scope_id="test-project-001",
)

repository.save_episode(episode)

loaded = repository.get_episode(episode.episode_id)

print("CREADO:", episode)
print("RECUPERADO:", loaded)

assert loaded is not None
assert loaded.episode_id == episode.episode_id
assert loaded.scope_id == "test-project-001"

print("Persistencia Supabase OK")