from supabase import create_client

from core.settings import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ENV_CONFIG

if ENV_CONFIG == "test":
    supabase = None
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
