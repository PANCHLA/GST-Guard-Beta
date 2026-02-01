-- =============================================
-- GST Guard: Supabase Row Level Security Setup
-- =============================================
-- Run this in Supabase SQL Editor (Dashboard > SQL Editor)
-- This ensures users can only access their own data

-- =============================================
-- 1. ENABLE RLS ON TABLES
-- =============================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

-- =============================================
-- 2. USERS TABLE POLICIES
-- =============================================

-- Users can only read their own profile
CREATE POLICY "Users can view own profile"
ON users FOR SELECT
USING (auth.uid()::text = id::text OR auth.jwt() ->> 'phone' = whatsapp_phone_number);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
ON users FOR UPDATE
USING (auth.uid()::text = id::text OR auth.jwt() ->> 'phone' = whatsapp_phone_number);

-- Service role (backend) can insert new users
CREATE POLICY "Service role can insert users"
ON users FOR INSERT
WITH CHECK (true);  -- Backend uses service_role key with elevated privileges

-- =============================================
-- 3. INVOICES TABLE POLICIES
-- =============================================

-- Users can only view their own invoices
CREATE POLICY "Users can view own invoices"
ON invoices FOR SELECT
USING (user_id IN (
    SELECT id FROM users 
    WHERE auth.uid()::text = id::text 
    OR auth.jwt() ->> 'phone' = whatsapp_phone_number
));

-- Users can update their own invoices
CREATE POLICY "Users can update own invoices"
ON invoices FOR UPDATE
USING (user_id IN (
    SELECT id FROM users 
    WHERE auth.uid()::text = id::text 
    OR auth.jwt() ->> 'phone' = whatsapp_phone_number
));

-- Service role (backend) can insert invoices
CREATE POLICY "Service role can insert invoices"
ON invoices FOR INSERT
WITH CHECK (true);  -- Backend uses service_role key

-- =============================================
-- 4. OPTIONAL: Add preferred_language column
-- =============================================

-- If not already added, add the preferred_language column
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_language TEXT DEFAULT 'en';

-- =============================================
-- 5. VERIFICATION QUERIES
-- =============================================

-- Check RLS is enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' AND tablename IN ('users', 'invoices');

-- Check policies
SELECT tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE schemaname = 'public';

-- =============================================
-- IMPORTANT NOTES:
-- =============================================
-- 
-- 1. The backend uses SUPABASE_KEY (service_role key) which bypasses RLS
--    This is correct - the webhook needs full access to create users/invoices
--
-- 2. The dashboard API uses JWT tokens with 'phone' claim
--    RLS policies check this claim to filter data
--
-- 3. For RLS to work with JWT, ensure your auth.py sets the phone claim:
--    payload = {"user_id": user["id"], "phone": phone, ...}
--
-- 4. Test by calling the API with a JWT - you should only see your own data
