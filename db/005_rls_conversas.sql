alter table public.conversas enable row level security;

create policy "ler as próprias conversas"
  on public.conversas for select to authenticated
  using (user_id = (select auth.uid()));

create policy "criar a própria conversa"
  on public.conversas for insert to authenticated
  with check (user_id = (select auth.uid()));

--using decide quais linhas podem ser alteradas; with check impede trocar o dono
create policy "renomear a própria conversa"
  on public.conversas for update to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));

create policy "apagar a própria conversa"
  on public.conversas for delete to authenticated
  using (user_id = (select auth.uid()));