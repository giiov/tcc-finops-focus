alter table public.conversoes enable row level security;

create policy "ler o próprio histórico de conversões"
  on public.conversoes for select to authenticated
  using (user_id = (select auth.uid()));

create policy "registrar a própria conversão"
  on public.conversoes for insert to authenticated
  with check (user_id = (select auth.uid()));

create policy "apagar a própria conversão"
  on public.conversoes for delete to authenticated
  using (user_id = (select auth.uid()));