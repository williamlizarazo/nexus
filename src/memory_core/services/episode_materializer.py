from __future__ import annotations

from memory_core.contracts.episode_repository import EpisodeRepository
from memory_core.episode_builder.models import EpisodeDraft


class EpisodeMaterializer:
    def __init__(self, repository: EpisodeRepository):
        self.repository = repository

    def save(self, drafts: list[EpisodeDraft]) -> None:
        for draft in drafts:
            self.repository.save_episode(draft.episode)

            for item in draft.items:
                self.repository.add_item(item)

            for edge in draft.edges:
                self.repository.add_edge(edge)
