-- Supabase Schema
create extension if not exists vector;
create table products (id uuid primary key default gen_random_uuid(), name text, description text, price numeric, target_sales int, budget_rp int, created_at timestamp default now());
create table campaigns (id uuid primary key default gen_random_uuid(), product_id uuid references products(id), meta_campaign_id text, name text, status text default 'PAUSED', budget_daily_rp int, created_at timestamp default now());
create table leads (id uuid primary key default gen_random_uuid(), campaign_id uuid references campaigns(id), wa_id text, name text, phone text, status text default 'NEW', intent_score int, bant jsonb, created_at timestamp default now());
create table conversations (id uuid primary key default gen_random_uuid(), lead_id uuid references leads(id), role text, content text, created_at timestamp default now());
create table follow_ups (id uuid primary key default gen_random_uuid(), lead_id uuid references leads(id), scheduled_at timestamp, template text, status text default 'PENDING');
