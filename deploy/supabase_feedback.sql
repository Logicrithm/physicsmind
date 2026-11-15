-- PhysicsMind feedback table for the online app.
-- Paste all of this into Supabase: SQL Editor -> New query -> Run. Running it again is harmless.
--
-- The app uses the project's publishable (anon) key. The rules below let that key ADD feedback and nothing else:
-- it cannot read, change or delete what testers sent. You read the feedback yourself in Table Editor.

create table if not exists public.response_feedback (
  id                  bigint generated always as identity primary key,
  response_id         text not null check (char_length(response_id) <= 100),
  created_at          timestamptz not null default now(),
  response_type       text not null check (char_length(response_type) <= 50),
  question            text not null check (char_length(question) <= 4000),
  answer              text not null check (char_length(answer) <= 12000),
  model               text check (char_length(model) <= 200),
  rating              text not null check (rating in ('helpful', 'not_helpful')),
  issue_category      text check (char_length(issue_category) <= 100),
  comment             text check (char_length(comment) <= 1000),
  verification_status text check (char_length(verification_status) <= 200),
  app_version         text check (char_length(app_version) <= 100)
);

create index if not exists response_feedback_created_at on public.response_feedback (created_at desc);

alter table public.response_feedback enable row level security;

drop policy if exists "the app may add feedback" on public.response_feedback;
create policy "the app may add feedback" on public.response_feedback
  for insert to anon with check (true);

revoke all on public.response_feedback from anon, authenticated;
grant insert on public.response_feedback to anon;
