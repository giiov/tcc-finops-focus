alter table public.mensagens enable row level security;

create policy "ler o próprio histórico de mensagens"
  on public.mensagens for select to authenticated
  using (user_id = (select auth.uid()));

create policy "criar a própria mensagem"
  on public.mensagens for insert to authenticated
  with check (user_id = (select auth.uid()));