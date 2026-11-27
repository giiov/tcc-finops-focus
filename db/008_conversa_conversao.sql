-- permite vincular uma conversa a uma conversão do mesmo usuário
alter table public.conversoes
  add constraint conversoes_id_user_id_unique
  unique (id, user_id);

alter table public.conversas
  add column conversao_id uuid;

alter table public.conversas
  add constraint conversas_conversao_usuario_fk
  foreign key (conversao_id, user_id)
  references public.conversoes (id, user_id)
  on delete set null (conversao_id);