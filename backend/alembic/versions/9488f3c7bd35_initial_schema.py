"""initial schema

Revision ID: 9488f3c7bd35
Revises:
Create Date: 2026-08-07
"""
from alembic import op

revision = "9488f3c7bd35"
down_revision = None
branch_labels = None
depends_on = None

UPGRADE_SQL = r"""
-- Reference DDL matching backend/app/models/*.py. The actual schema is created via Alembic
-- migrations (backend/alembic/); this file is a human-readable reference / manual-setup fallback.

CREATE TYPE user_role AS ENUM ('worker', 'supervisor', 'user', 'admin');
CREATE TYPE material_category AS ENUM ('plastic','glass','steel','aluminium','iron','paper','cardboard','organic','textile','ewaste');
CREATE TYPE polymer_type AS ENUM ('PET','HDPE','LDPE','PP','PS','PC','PVC','ABS','PLA');
CREATE TYPE weight_source AS ENUM ('vision','load_cell','manual');
CREATE TYPE scan_status AS ENUM ('pending','classified','disposed','rejected');
CREATE TYPE leaderboard_period AS ENUM ('daily','monthly','alltime');
CREATE TYPE collection_status AS ENUM ('assigned','in_progress','completed','cancelled');

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR UNIQUE NOT NULL,
  phone VARCHAR UNIQUE,
  password_hash VARCHAR NOT NULL,
  full_name VARCHAR NOT NULL,
  role user_role NOT NULL DEFAULT 'user',
  district VARCHAR,
  state VARCHAR,
  language_pref VARCHAR NOT NULL DEFAULT 'en',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE materials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR UNIQUE NOT NULL,
  name VARCHAR NOT NULL,
  category material_category NOT NULL,
  polymer_type polymer_type,
  biodegradable BOOLEAN NOT NULL DEFAULT false,
  recyclable BOOLEAN NOT NULL DEFAULT true,
  reusable BOOLEAN NOT NULL DEFAULT false,
  description TEXT,
  disposal_instructions TEXT,
  recycling_instructions TEXT,
  base_price_per_kg NUMERIC(10,2) NOT NULL DEFAULT 0
);

CREATE TABLE co2_factors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  material_id UUID UNIQUE NOT NULL REFERENCES materials(id),
  co2_saved_recycle_per_kg NUMERIC(10,4) NOT NULL DEFAULT 0,
  co2_saved_reuse_per_kg NUMERIC(10,4) NOT NULL DEFAULT 0,
  energy_saved_per_kg_kwh NUMERIC(10,4) NOT NULL DEFAULT 0,
  landfill_volume_reduced_per_kg_l NUMERIC(10,4) NOT NULL DEFAULT 0,
  tree_equivalent_per_kg NUMERIC(10,6) NOT NULL DEFAULT 0,
  source_note TEXT
);

CREATE TABLE esp32_devices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  device_uid VARCHAR UNIQUE NOT NULL,
  owner_id UUID REFERENCES users(id),
  location VARCHAR,
  last_seen TIMESTAMPTZ,
  firmware_version VARCHAR,
  ip_address VARCHAR
);

CREATE TABLE scans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  material_id UUID REFERENCES materials(id),
  image_url VARCHAR,
  confidence_score NUMERIC(5,4),
  estimated_weight_kg NUMERIC(10,4),
  weight_source weight_source NOT NULL DEFAULT 'vision',
  weight_confidence NUMERIC(5,4),
  co2_saved_kg NUMERIC(10,4),
  earnings_estimate NUMERIC(10,2),
  device_id UUID REFERENCES esp32_devices(id),
  status scan_status NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE market_prices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category VARCHAR NOT NULL,
  price_per_kg NUMERIC(10,2) NOT NULL,
  currency VARCHAR NOT NULL DEFAULT 'INR',
  updated_by UUID REFERENCES users(id),
  updated_at TIMESTAMPTZ DEFAULT now(),
  source VARCHAR NOT NULL DEFAULT 'admin'
);

CREATE TABLE recycling_centers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR NOT NULL,
  address VARCHAR NOT NULL,
  lat NUMERIC(9,6) NOT NULL,
  lng NUMERIC(9,6) NOT NULL,
  phone VARCHAR,
  operating_hours JSONB,
  accepted_materials VARCHAR[] NOT NULL DEFAULT '{}',
  rating NUMERIC(3,2),
  verified BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE leaderboard_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  period leaderboard_period NOT NULL,
  district VARCHAR,
  state VARCHAR,
  total_weight_kg NUMERIC(12,4) NOT NULL DEFAULT 0,
  total_co2_kg NUMERIC(12,4) NOT NULL DEFAULT 0,
  total_earnings NUMERIC(12,2) NOT NULL DEFAULT 0,
  streak_days INTEGER NOT NULL DEFAULT 0,
  rank INTEGER
);

CREATE TABLE achievements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR UNIQUE NOT NULL,
  name VARCHAR NOT NULL,
  description TEXT,
  icon_url VARCHAR
);

CREATE TABLE user_achievements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  achievement_id UUID NOT NULL REFERENCES achievements(id),
  earned_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE collections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  worker_id UUID NOT NULL REFERENCES users(id),
  assigned_by UUID NOT NULL REFERENCES users(id),
  area VARCHAR NOT NULL,
  status collection_status NOT NULL DEFAULT 'assigned',
  scheduled_for TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_scans_user_id ON scans(user_id);
CREATE INDEX idx_scans_created_at ON scans(created_at);
CREATE INDEX idx_leaderboard_period_rank ON leaderboard_entries(period, rank);
CREATE INDEX idx_materials_code ON materials(code);

"""

DOWNGRADE_SQL = r"""
DROP TABLE IF EXISTS collections, user_achievements, achievements, leaderboard_entries,
  recycling_centers, market_prices, scans, esp32_devices, co2_factors, materials, users CASCADE;
DROP TYPE IF EXISTS collection_status, leaderboard_period, scan_status, weight_source,
  polymer_type, material_category, user_role CASCADE;
"""


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto;')  # for gen_random_uuid()
    op.execute(UPGRADE_SQL)


def downgrade() -> None:
    op.execute(DOWNGRADE_SQL)
