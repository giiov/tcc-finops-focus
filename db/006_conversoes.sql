create table public.conversoes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
  nome_arquivo text not null
    check (char_length(btrim(nome_arquivo)) > 0 and char_length(nome_arquivo) <= 255),
  --sem lista fixa de provedores: um provedor novo não exige mexer no banco
  formato text not null
    check (char_length(btrim(formato)) > 0 and char_length(formato) <= 30),
  total_linhas integer not null check (total_linhas >= 0),
  tamanho_bytes bigint not null check (tamanho_bytes >= 0),
  criado_em timestamptz not null default now()
);

--a lista do histórico: as conversões do usuário, da mais recente para a mais antiga
create index idx_conversoes_user_criado on public.conversoes (user_id, criado_em desc);