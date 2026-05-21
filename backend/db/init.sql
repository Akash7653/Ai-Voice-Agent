-- PostgreSQL Schema Initialization for Voice Agent

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id VARCHAR NOT NULL,
    doctor_name VARCHAR NOT NULL,
    doctor_id VARCHAR,
    specialty VARCHAR NOT NULL,
    appointment_date VARCHAR NOT NULL,
    appointment_time VARCHAR NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    status VARCHAR DEFAULT 'scheduled',
    notes TEXT,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patient_id ON appointments(patient_id);
CREATE INDEX idx_appointment_date ON appointments(appointment_date);
CREATE INDEX idx_status ON appointments(status);

-- Doctor Schedule table
CREATE TABLE IF NOT EXISTS doctor_schedule (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doctor_id VARCHAR NOT NULL UNIQUE,
    doctor_name VARCHAR NOT NULL,
    specialty VARCHAR NOT NULL,
    available_slots JSONB NOT NULL DEFAULT '{}',
    working_hours_start VARCHAR DEFAULT '09:00',
    working_hours_end VARCHAR DEFAULT '17:00',
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_doctor_id ON doctor_schedule(doctor_id);
CREATE INDEX idx_is_active ON doctor_schedule(is_active);

-- Patient Memory table
CREATE TABLE IF NOT EXISTS patient_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id VARCHAR NOT NULL UNIQUE,
    preferred_language VARCHAR DEFAULT 'en',
    preferred_doctor VARCHAR,
    preferred_specialties JSONB DEFAULT '{}',
    past_appointments JSONB DEFAULT '[]',
    interaction_count INTEGER DEFAULT 0,
    last_interaction TIMESTAMP WITH TIME ZONE,
    conversation_summary TEXT,
    patient_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pm_patient_id ON patient_memory(patient_id);

-- Conversation Log table
CREATE TABLE IF NOT EXISTS conversation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR NOT NULL,
    patient_id VARCHAR NOT NULL,
    language VARCHAR DEFAULT 'en',
    status VARCHAR DEFAULT 'active',
    transcript TEXT,
    extracted_intent VARCHAR,
    tools_used JSONB DEFAULT '[]',
    latency_metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cl_session_id ON conversation_log(session_id);
CREATE INDEX idx_cl_patient_id ON conversation_log(patient_id);
CREATE INDEX idx_cl_created_at ON conversation_log(created_at);

-- Campaign Task table
CREATE TABLE IF NOT EXISTS campaign_task (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id VARCHAR NOT NULL,
    campaign_type VARCHAR NOT NULL,
    appointment_id UUID,
    status VARCHAR DEFAULT 'scheduled',
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_time TIMESTAMP WITH TIME ZONE,
    result VARCHAR,
    transcript TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ct_patient_id ON campaign_task(patient_id);
CREATE INDEX idx_ct_scheduled_time ON campaign_task(scheduled_time);
CREATE INDEX idx_ct_status ON campaign_task(status);

-- Latency Metric table
CREATE TABLE IF NOT EXISTS latency_metric (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR NOT NULL,
    component VARCHAR NOT NULL,
    duration_ms NUMERIC NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lm_session_id ON latency_metric(session_id);
CREATE INDEX idx_lm_component ON latency_metric(component);
CREATE INDEX idx_lm_timestamp ON latency_metric(timestamp);

-- Insert sample doctor data
INSERT INTO doctor_schedule (doctor_id, doctor_name, specialty, available_slots, is_active)
VALUES
    ('doc_001', 'Dr. Rajesh Kumar', 'Cardiologist', '{"2024-12-20": ["09:00", "10:00", "14:00"], "2024-12-21": ["11:00", "15:00"]}'::jsonb, true),
    ('doc_002', 'Dr. Priya Sharma', 'General Practitioner', '{"2024-12-20": ["10:00", "11:00", "16:00"], "2024-12-21": ["09:00", "14:00"]}'::jsonb, true),
    ('doc_003', 'Dr. Amit Patel', 'Dermatologist', '{"2024-12-20": ["13:00", "14:00", "15:00"], "2024-12-21": ["10:00", "16:00"]}'::jsonb, true)
ON CONFLICT (doctor_id) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_appointments_patient_date ON appointments(patient_id, appointment_date);
CREATE INDEX IF NOT EXISTS idx_conversation_log_patient_session ON conversation_log(patient_id, session_id);
CREATE INDEX IF NOT EXISTS idx_latency_metric_session_component ON latency_metric(session_id, component);
CREATE INDEX IF NOT EXISTS idx_campaign_task_patient_status ON campaign_task(patient_id, status);
