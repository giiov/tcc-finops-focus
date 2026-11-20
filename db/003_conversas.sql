create table public.conversas (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  titulo text not null default 'Nova conversa'
    check (char_length(btrim(titulo)) > 0 and char_length(titulo) <= 100),
  criado_em timestamptz not null default now(),
  atualizado_em timestamptz not null default now(),
  --permite que a tabela mensagens aponte para (id, user_id) e exija o mesmo dono
  unique (id, user_id)
);

--lista lateral: as conversas do usuário, da mais recente para a mais antiga
create index idx_conversas_user_atualizado on public.conversas (user_id, atualizado_em desc);