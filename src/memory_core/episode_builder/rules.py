from __future__ import annotations

from itertools import combinations

from memory_core.episode_builder.models import BranchRelation, SearchBranch


def _document_ids(branch: SearchBranch) -> set[str]:
    return {item.doc_id for item in branch.results if item.doc_id}


def _chunk_ids(branch: SearchBranch) -> set[str]:
    return {item.chunk_id for item in branch.results if item.chunk_id}


def _page_keys(branch: SearchBranch) -> set[tuple[str, int]]:
    keys: set[tuple[str, int]] = set()

    for item in branch.results:
        if not item.doc_id:
            continue

        start = item.page_idx_start
        end = item.page_idx_end

        if start is None:
            continue

        if end is None:
            end = start

        # Evitar expandir rangos anómalamente grandes.
        if end - start > 20:
            end = start

        for page_idx in range(start, end + 1):
            keys.add((item.doc_id, page_idx))

    return keys


def compare_branches(
    left: SearchBranch,
    right: SearchBranch,
) -> list[BranchRelation]:
    relations: list[BranchRelation] = []

    left_id = left.search.search_id
    right_id = right.search.search_id

    if (
        left.search.trace_id
        and right.search.trace_id
        and left.search.trace_id == right.search.trace_id
    ):
        relations.append(
            BranchRelation(
                source_search_id=left_id,
                target_search_id=right_id,
                relation_type="same_trace",
                merge_episode=True,
                score=1.0,
                evidence={"trace_id": left.search.trace_id},
            )
        )

    shared_chunks = _chunk_ids(left) & _chunk_ids(right)

    if shared_chunks:
        relations.append(
            BranchRelation(
                source_search_id=left_id,
                target_search_id=right_id,
                relation_type="shared_chunk",
                merge_episode=True,
                score=1.0,
                evidence={"chunk_ids": sorted(shared_chunks)},
            )
        )

    shared_pages = _page_keys(left) & _page_keys(right)

    if shared_pages:
        relations.append(
            BranchRelation(
                source_search_id=left_id,
                target_search_id=right_id,
                relation_type="shared_page",
                merge_episode=True,
                score=0.95,
                evidence={
                    "pages": [
                        {"doc_id": doc_id, "page_idx": page_idx}
                        for doc_id, page_idx in sorted(shared_pages)
                    ]
                },
            )
        )

    left_docs = _document_ids(left)
    right_docs = _document_ids(right)

    shared_docs = left_docs & right_docs
    union_docs = left_docs | right_docs

    if shared_docs:
        jaccard = len(shared_docs) / len(union_docs) if union_docs else 0.0

        strong_document_overlap = len(shared_docs) >= 2 and jaccard >= 0.30

        relations.append(
            BranchRelation(
                source_search_id=left_id,
                target_search_id=right_id,
                relation_type=(
                    "shared_documents"
                    if strong_document_overlap
                    else "shared_document"
                ),
                merge_episode=strong_document_overlap,
                score=0.80 if strong_document_overlap else 0.50,
                evidence={
                    "document_ids": sorted(shared_docs),
                    "shared_count": len(shared_docs),
                    "jaccard": round(jaccard, 4),
                },
            )
        )

    return relations


def build_branch_relations(
    branches: list[SearchBranch],
) -> list[BranchRelation]:
    relations: list[BranchRelation] = []

    for left, right in combinations(branches, 2):
        relations.extend(compare_branches(left, right))

    return relations
