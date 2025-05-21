from supabase import create_client

from core.settings import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
