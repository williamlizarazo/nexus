create table if not exists public.research_episodes (
    episode_id uuid primary key,

    scope_type text not null,
    scope_id text not null,

    actor_id uuid null,

    started_at timestamptz not null,
    ended_at timestamptz null,

    status text not null default 'open',

    grouping_version text not null default 'episodic_v1',
    schema_version integer not null default 1,

    metadata_json jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


create table if not exists public.research_episode_items (
    item_id uuid primary key,

    episode_id uuid not null
        references public.research_episodes(episode_id)
        on delete cascade,

    source_type text not null,
    source_id text not null,

    role text null,
    occurred_at timestamptz null,

    membership_method text not null default 'deterministic',
    membership_reason text null,
    membership_score double precision null,

    schema_version integer not null default 1,
    metadata_json jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now(),

    unique (episode_id, source_type, source_id)
);


create table if not exists public.research_episode_edges (
    edge_id uuid primary key,

    episode_id uuid not null
        references public.research_episodes(episode_id)
        on delete cascade,

    source_item_id uuid not null
        references public.research_episode_items(item_id)
        on delete cascade,

    target_item_id uuid not null
        references public.research_episode_items(item_id)
        on delete cascade,

    relation_type text not null,
    relation_score double precision null,

    evidence_json jsonb not null default '{}'::jsonb,

    rule_version text not null default 'episodic_v1',
    schema_version integer not null default 1,

    metadata_json jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now(),

    check (source_item_id <> target_item_id)
);


create table if not exists public.research_episode_analyses (
    analysis_id uuid primary key,

    episode_id uuid not null
        references public.research_episodes(episode_id)
        on delete cascade,

    version integer not null,

    summary text null,

    entities_json jsonb not null default '[]'::jsonb,
    relations_json jsonb not null default '[]'::jsonb,
    topics_json jsonb not null default '[]'::jsonb,

    open_questions_json jsonb not null default '[]'::jsonb,
    contradictions_json jsonb not null default '[]'::jsonb,

    structure_json jsonb not null default '{}'::jsonb,

    source_fingerprint text null,

    provider text null,
    model text null,
    prompt_version text null,

    schema_version integer not null default 1,
    metadata_json jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now(),

    unique (episode_id, version)
);

create index if not exists idx_research_episodes_scope
on public.research_episodes(scope_type, scope_id);

create index if not exists idx_research_episodes_actor
on public.research_episodes(actor_id);

create index if not exists idx_research_episodes_started
on public.research_episodes(started_at desc);

create index if not exists idx_episode_items_episode
on public.research_episode_items(episode_id);

create index if not exists idx_episode_items_source
on public.research_episode_items(source_type, source_id);

create index if not exists idx_episode_items_occurred
on public.research_episode_items(occurred_at);

create index if not exists idx_episode_edges_episode
on public.research_episode_edges(episode_id);

create index if not exists idx_episode_edges_relation
on public.research_episode_edges(relation_type);

create index if not exists idx_episode_analyses_episode_version
on public.research_episode_analyses(episode_id, version desc);

alter table public.research_episode_items
add constraint uq_episode_items_episode_item
unique (episode_id, item_id);


alter table public.research_episode_edges
drop constraint if exists research_episode_edges_source_item_id_fkey;

alter table public.research_episode_edges
drop constraint if exists research_episode_edges_target_item_id_fkey;


alter table public.research_episode_edges
add constraint fk_episode_edges_source_item
foreign key (episode_id, source_item_id)
references public.research_episode_items (episode_id, item_id)
on delete cascade;


alter table public.research_episode_edges
add constraint fk_episode_edges_target_item
foreign key (episode_id, target_item_id)
references public.research_episode_items (episode_id, item_id)
on delete cascade;