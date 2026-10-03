import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://mfpbiwqesrlcljkumgxc.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_u9d8u7Ag6nv6pjXV30sVjA_8w6e7dVE';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export async function checkSupabaseConnection() {
  try {
    const { data, error } = await supabase.auth.getSession();
    return { connected: !error, url: supabaseUrl };
  } catch (err) {
    return { connected: false, error: err.message };
  }
}
