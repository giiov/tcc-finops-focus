--ATENÇÃO (desenvolvimento): as mensagens de teste não pertencem a nenhuma conversa e são descartadas
--com dados reais, seria preciso criar uma conversa para cada usuário e mover as mensagens antes
delete from public.mensagens;

alter table public.mensagens
  add column conversa_id uuid not null;

--a mensagem só pode apontar para uma conversa do mesmo dono (user_id igual)
--se a conversa for apagada, as mensagens vão junto
alter table public.mensagens
  add constraint mensagens_conversa_fk
  foreign key (conversa_id, user_id)
  references public.conversas (id, user_id)
  on delete cascade;

--mesmo limite do back (max_length=10000 no main.py)
alter table public.mensagens
  add constraint mensagens_content_max check (char_length(content) <= 10000);

--o histórico agora é lido por conversa, em ordem de id
drop index public.idx_mensagens_user_id;
create index idx_mensagens_conversa on public.mensagens (conversa_id, id);

--a cada mensagem nova, a conversa sobe para o topo da lista lateral
create function public.tocar_conversa()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  update public.conversas
     set atualizado_em = now()
   where id = new.conversa_id;
  return new;
end;
$$;

create trigger mensagens_tocar_conversa
after insert on public.mensagens
for each row execute function public.tocar_conversa();