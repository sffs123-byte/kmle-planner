create extension if not exists pgcrypto;

create table if not exists public.planner_sync_slots (
  sync_code text primary key,
  state_json jsonb not null,
  state_version text not null default 'kmlePlannerState.v2',
  updated_at timestamptz not null default timezone('utc', now()),
  updated_by text,
  created_at timestamptz not null default timezone('utc', now())
);

revoke all on public.planner_sync_slots from anon, authenticated;

create or replace function public.planner_sync_pull(p_sync_code text)
returns table(state_json jsonb, state_version text, updated_at timestamptz, updated_by text)
language sql
security definer
set search_path = public
as $$
  select state_json, state_version, updated_at, updated_by
  from public.planner_sync_slots
  where sync_code = p_sync_code
  limit 1;
$$;

create or replace function public.planner_sync_push(
  p_sync_code text,
  p_state_json jsonb,
  p_state_version text default 'kmlePlannerState.v2',
  p_updated_by text default null,
  p_updated_at timestamptz default timezone('utc', now())
)
returns table(updated_at timestamptz)
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.planner_sync_slots (
    sync_code,
    state_json,
    state_version,
    updated_at,
    updated_by
  )
  values (
    p_sync_code,
    p_state_json,
    coalesce(p_state_version, 'kmlePlannerState.v2'),
    coalesce(p_updated_at, timezone('utc', now())),
    p_updated_by
  )
  on conflict (sync_code)
  do update set
    state_json = excluded.state_json,
    state_version = excluded.state_version,
    updated_at = excluded.updated_at,
    updated_by = excluded.updated_by
  where public.planner_sync_slots.updated_at <= excluded.updated_at;

  return query
  select public.planner_sync_slots.updated_at
  from public.planner_sync_slots
  where public.planner_sync_slots.sync_code = p_sync_code;
end;
$$;

grant execute on function public.planner_sync_pull(text) to anon, authenticated;
grant execute on function public.planner_sync_push(text, jsonb, text, text, timestamptz) to anon, authenticated;

-- ------------------------------------------------------------------
-- DB-first phase 1: per-user planner state (single-user / multi-device)
-- ------------------------------------------------------------------

create table if not exists public.planner_user_state (
  user_id text primary key,
  state_json jsonb not null default '{}'::jsonb,
  state_version text not null default 'planner-user-state.v1',
  updated_at timestamptz not null default timezone('utc', now()),
  updated_by text,
  created_at timestamptz not null default timezone('utc', now())
);

revoke all on public.planner_user_state from anon, authenticated;

create or replace function public.planner_user_state_pull(p_user_id text)
returns table(state_json jsonb, state_version text, updated_at timestamptz, updated_by text)
language sql
security definer
set search_path = public
as $$
  select state_json, state_version, updated_at, updated_by
  from public.planner_user_state
  where user_id = p_user_id
  limit 1;
$$;

create or replace function public.planner_user_state_push(
  p_user_id text,
  p_state_json jsonb,
  p_state_version text default 'planner-user-state.v1',
  p_updated_by text default null,
  p_updated_at timestamptz default timezone('utc', now())
)
returns table(updated_at timestamptz)
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.planner_user_state (
    user_id,
    state_json,
    state_version,
    updated_at,
    updated_by
  )
  values (
    p_user_id,
    coalesce(p_state_json, '{}'::jsonb),
    coalesce(p_state_version, 'planner-user-state.v1'),
    coalesce(p_updated_at, timezone('utc', now())),
    p_updated_by
  )
  on conflict (user_id)
  do update set
    state_json = excluded.state_json,
    state_version = excluded.state_version,
    updated_at = excluded.updated_at,
    updated_by = excluded.updated_by
  where public.planner_user_state.updated_at <= excluded.updated_at;

  return query
  select public.planner_user_state.updated_at
  from public.planner_user_state
  where public.planner_user_state.user_id = p_user_id;
end;
$$;

grant execute on function public.planner_user_state_pull(text) to anon, authenticated;
grant execute on function public.planner_user_state_push(text, jsonb, text, text, timestamptz) to anon, authenticated;
