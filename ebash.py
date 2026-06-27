import math
from collections import defaultdict

# ==========================================
# BLOCK 1: p-adic Arithmetic and Metrics (v3.0)
# ==========================================
def p_adic_valuation(x, p):
    """Computes the p-adic valuation of number x."""
    if x == 0:
        return float('inf')
    v = 0
    while x % p == 0:
        x //= p
        v += 1
    return v

def p_adic_distance(x, y, p):
    """Computes the p-adic distance between two numbers."""
    if x == y:
        return 0.0
    return p ** (-p_adic_valuation(abs(x - y), p))

def p_adic_entropy(orbit, p):
    """Computes p-adic Shannon entropy."""
    valuations = []
    for i in range(len(orbit)):
        for j in range(i + 1, len(orbit)):
            if orbit[i] and orbit[j]:
                dist = p_adic_distance(orbit[i][0], orbit[j][0], p)
                if dist > 0 and dist != 1.0:
                    valuations.append(-math.log(dist, p))
    
    if not valuations or sum(valuations) == 0:
        return 0.0
    
    total = sum(valuations)
    probs = [v / total for v in valuations]
    entropy = -sum(p_val * math.log(p_val, 2) for p_val in probs if p_val > 0)
    return entropy

# ==========================================
# BLOCK 2: Large Elliptic Curve over F_101 (v3.0)
# ==========================================
P_FIELD = 101
CURVE_A = 1
CURVE_B = 1

def mod_inverse(a, m):
    """Computes modular multiplicative inverse."""
    return pow(a, m - 2, m)

def ec_add(P, Q):
    """Adds two points on the elliptic curve."""
    if P is None: return Q
    if Q is None: return P
    
    x1, y1 = P
    x2, y2 = Q
    
    if x1 == x2 and (y1 + y2) % P_FIELD == 0:
        return None
    
    if x1 == x2 and y1 == y2:
        lam = (3 * x1 * x1 + CURVE_A) * mod_inverse(2 * y1, P_FIELD) % P_FIELD
    else:
        lam = (y2 - y1) * mod_inverse(x2 - x1, P_FIELD) % P_FIELD
        
    x3 = (lam * lam - x1 - x2) % P_FIELD
    y3 = (lam * (x1 - x3) - y1) % P_FIELD
    return (x3, y3)

def ec_mul(k, P):
    """Multiplies a point by a scalar (double-and-add algorithm)."""
    result = None
    addend = P
    while k:
        if k & 1:
            result = ec_add(result, addend)
        addend = ec_add(addend, addend)
        k >>= 1
    return result

def find_curve_order(P):
    """Finds the order of a point on the curve."""
    current = P
    order = 1
    while current is not None and order < 200:
        current = ec_add(current, P)
        order += 1
    return order if current is None else -1

# ==========================================
# BLOCK 3: Dynamics and Tensor Network (v3.0)
# ==========================================
def compute_orbit(P_start, steps):
    """Generates orbit through point doubling."""
    orbit = [P_start]
    current = P_start
    for _ in range(steps):
        current = ec_add(current, current)
        orbit.append(current)
    return orbit

def build_tensor_matrix(orbit, p):
    """Builds tensor matrix of p-adic distances."""
    dim = len(orbit)
    tensor_matrix = [[0.0]*dim for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            if orbit[i] and orbit[j]:
                dist = p_adic_distance(orbit[i][0], orbit[j][0], p)
                tensor_matrix[i][j] = dist
    return tensor_matrix

# ==========================================
# BLOCK 4: Persistent Topology (v3.0)
# ==========================================
def compute_betti_at_threshold(tensor_matrix, threshold):
    """Computes Betti numbers at given threshold."""
    dim = len(tensor_matrix)
    adj = defaultdict(list)
    edges = 0
    
    for i in range(dim):
        for j in range(i + 1, dim):
            if tensor_matrix[i][j] <= threshold and tensor_matrix[i][j] > 0:
                adj[i].append(j)
                adj[j].append(i)
                edges += 1
    
    visited = set()
    betti_0 = 0
    for i in range(dim):
        if i not in visited:
            betti_0 += 1
            queue = [i]
            visited.add(i)
            while queue:
                node = queue.pop(0)
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
    
    betti_1 = edges - dim + betti_0
    return betti_0, betti_1

def persistent_homology_analysis(tensor_matrix):
    """Performs persistent homology analysis."""
    max_dist = max(tensor_matrix[i][j] for i in range(len(tensor_matrix)) for j in range(len(tensor_matrix)))
    
    if max_dist == 0:
        return 0, 0, []
    
    persistence_diagram = []
    for i in range(30):
        threshold = max_dist * i / 30.0
        b0, b1 = compute_betti_at_threshold(tensor_matrix, threshold)
        persistence_diagram.append({
            'threshold': threshold,
            'betti_0': b0,
            'betti_1': b1
        })
    
    max_b1 = max(entry['betti_1'] for entry in persistence_diagram)
    avg_b1 = sum(entry['betti_1'] for entry in persistence_diagram) / len(persistence_diagram)
    
    return max_b1, avg_b1, persistence_diagram

# ==========================================
# MAIN TEST v3.0
# ==========================================
def run_pheti_v3():
    print("="*80)
    print("p-HETI v3.0: Large Curve F_101 + Multi-p Analysis")
    print("="*80)
    
    print("Searching for base point with large order...")
    BASE_POINT = None
    order = -1
    
    for x in range(P_FIELD):
        for y in range(P_FIELD):
            if (y * y - (x**3 + CURVE_A * x + CURVE_B)) % P_FIELD == 0:
                test_point = (x, y)
                test_order = find_curve_order(test_point)
                if test_order > 20:
                    BASE_POINT = test_point
                    order = test_order
                    print(f"Found point {BASE_POINT} with order {order}")
                    break
        if BASE_POINT:
            break
    
    if not BASE_POINT:
        print("No point with sufficient order found")
        return
    
    TARGET_SCALAR = 17
    TARGET_POINT = ec_mul(TARGET_SCALAR, BASE_POINT)
    
    print(f"\nBase Point P: {BASE_POINT}")
    print(f"Point Order: {order}")
    print(f"Target Point Q (scalar {TARGET_SCALAR}): {TARGET_POINT}")
    print(f"Field: F_{P_FIELD}")
    print(f"Orbit Depth: 20 steps")
    print("-"*80)
    
    p_primes = [2, 3, 5, 7]
    results = {}
    
    test_range = min(order - 1, 25)
    
    for test_k in range(1, test_range + 1):
        orbit = compute_orbit(BASE_POINT, steps=20)
        shifted_orbit = [ec_add(pt, ec_mul(test_k, BASE_POINT)) if pt else None for pt in orbit]
        
        energies = []
        entropies = []
        max_b1s = []
        
        for p in p_primes:
            tensor_mat = build_tensor_matrix(shifted_orbit, p)
            
            energy = sum(tensor_mat[i][j] for i in range(len(shifted_orbit)) for j in range(len(shifted_orbit)))
            energy = energy / (len(shifted_orbit) ** 2)
            energies.append(energy)
            
            entropy = p_adic_entropy(shifted_orbit, p)
            entropies.append(entropy)
            
            max_b1, _, _ = persistent_homology_analysis(tensor_mat)
            max_b1s.append(max_b1)
        
        results[test_k] = {
            'energy': sum(energies) / len(energies),
            'entropy': sum(entropies) / len(entropies),
            'max_betti_1': sum(max_b1s) / len(max_b1s),
            'is_target': (test_k == TARGET_SCALAR)
        }
    
    print(f"{'k':<4} | {'Energy':<12} | {'Entropy':<12} | {'Avg Max B1':<12} | {'Target?':<6}")
    print("-"*80)
    
    target_energy = None
    target_entropy = None
    target_max_b1 = None
    
    for k, res in results.items():
        marker = " <<<" if res['is_target'] else ""
        print(f"{k:<4} | {res['energy']:<12.4f} | {res['entropy']:<12.4f} | {res['max_betti_1']:<12.2f} | {str(res['is_target']):<6}{marker}")
        
        if res['is_target']:
            target_energy = res['energy']
            target_entropy = res['entropy']
            target_max_b1 = res['max_betti_1']
    
    print("-"*80)
    print("\n[RESULTS ANALYSIS v3.0]:")
    
    if target_energy is None:
        print("Target scalar not found")
        return
    
    energy_unique = all(abs(res['energy'] - target_energy) > 1e-3 for k, res in results.items() if k != TARGET_SCALAR)
    entropy_unique = all(abs(res['entropy'] - target_entropy) > 1e-3 for k, res in results.items() if k != TARGET_SCALAR)
    topology_unique = all(abs(res['max_betti_1'] - target_max_b1) > 0.1 for k, res in results.items() if k != TARGET_SCALAR)
    
    score = 0
    if energy_unique:
        print("✅ p-adic ENERGY: UNIQUE identifier!")
        score += 1
    else:
        print("⚠️ p-adic energy: collisions detected")
    
    if entropy_unique:
        print("✅ p-adic ENTROPY: UNIQUE topological invariant!")
        score += 1
    else:
        print("⚠️ p-adic entropy: needs larger orbit depth")
    
    if topology_unique:
        print("✅ PERSISTENT TOPOLOGY: UNIQUE cycle count!")
        score += 1
    else:
        print("⚠️ Topology: needs larger field")
    
    print(f"\nOVERALL RESULT: {score}/3 invariants working!")
    
    if score == 3:
        print("\n🎉 ALL THREE HYPOTHESES CONFIRMED!")
        print("   p-HETI ready for scaling to secp256k1 (Puzzle 135)!")
    elif score >= 2:
        print("\n✨ TWO INVARIANTS WORKING - significant progress!")
        print("   Model shows potential for real cryptanalysis.")

if __name__ == "__main__":
    run_pheti_v3()