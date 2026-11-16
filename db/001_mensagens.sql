create table public.mensagens (
  id bigint generated always as identity primary key,
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  criado_em timestamptz not null default now(),
  role text not null check (role in ('user', 'assistant')),
  content text not null check (CHAR_LENGTH(BTRIM(content)) > 0)
);

create index idx_mensagens_user_id on public.mensagens (user_id, criado_em desc);