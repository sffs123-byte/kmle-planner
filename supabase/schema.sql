create table if not exists public.planner_states (
  user_id uuid primary key references auth.users(id) on delete cascade,
  state_json jsonb not null,
  state_version text not null default 'kmlePlannerState.v2',
  updated_at timestamptz not null default timezone('utc', now()),
  updated_by text
);

alter table public.planner_states enable row level security;

do $$ begin
  create policy "planner_states_select_own"
    on public.planner_states
    for select
    to authenticated
    using (auth.uid() = user_id);
exception
  when duplicate_object then null;
end $$;

do $$ begin
  create policy "planner_states_insert_own"
    on public.planner_states
    for insert
    to authenticated
    with check (auth.uid() = user_id);
exception
  when duplicate_object then null;
end $$;

do $$ begin
  create policy "planner_states_update_own"
    on public.planner_states
    for update
    to authenticated
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);
exception
  when duplicate_object then null;
end $$;
