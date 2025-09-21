import re
from difflib import SequenceMatcher

def derive_shared_canonical_key(entity_dict):
    """
    Derive a canonical key using the shared schema:
    {area or room}_{role}_{signal_type} or fallback to {device_class}_{domain}.
    Strips suffixes like Greek letters (_α, _beta) and slugifies the result.
    """
    def slugify(s):
        return re.sub(r'[^a-zA-Z0-9]+', '_', s.strip().lower()) if s else ''

    # Extract fields
    area = entity_dict.get('area') or entity_dict.get('room')
    role = entity_dict.get('role') or entity_dict.get('semantic_role')
    signal_type = entity_dict.get('signal_type')
    device_class = entity_dict.get('device_class')
    domain = entity_dict.get('type') or entity_dict.get('platform') or entity_dict.get('domain')

    # Build base key
    if area and role and signal_type:
        base = f"{area}_{role}_{signal_type}"
    elif area and role:
        base = f"{area}_{role}"
    elif device_class and domain:
        base = f"{device_class}_{domain}"
    else:
        # Fallback to entity_id or name
        base = entity_dict.get('entity_id') or entity_dict.get('name') or ''

    # Remove Greek letter or beta suffixes
    base = re.sub(r'(_[a-zA-Z]+)?(_[α-ωΑ-Ω]|_alpha|_beta|_gamma|_delta|_epsilon|_zeta|_eta|_theta|_iota|_kappa|_lambda|_mu|_nu|_xi|_omicron|_pi|_rho|_sigma|_tau|_upsilon|_phi|_chi|_psi|_omega)$', '', base)
    return slugify(base)

def normalize_key_for_matching(key):
    """
    Normalize a key for matching: lowercase, strip non-alphanum, remove Greek/beta suffixes.
    """
    key = key.lower()
    key = re.sub(r'(_[α-ωΑ-Ω]|_alpha|_beta|_gamma|_delta|_epsilon|_zeta|_eta|_theta|_iota|_kappa|_lambda|_mu|_nu|_xi|_omicron|_pi|_rho|_sigma|_tau|_upsilon|_phi|_chi|_psi|_omega)$', '', key)
    key = re.sub(r'[^a-z0-9_]+', '', key)
    return key

def compare_keys(a, b):
    """
    Compare two canonical keys and return a similarity score (0-1).
    """
    a_norm = normalize_key_for_matching(a)
    b_norm = normalize_key_for_matching(b)
    return SequenceMatcher(None, a_norm, b_norm).ratio()
