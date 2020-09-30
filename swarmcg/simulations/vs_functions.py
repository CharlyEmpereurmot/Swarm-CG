import numpy as np
from ..shared import exceptions

# All these functions for virtual sites definitions are explained
# in the GROMACS manual part 5.5.7 (page 379 in manual version 2020)
# Check also the bonded potentials table best viewed here:
# http://manual.gromacs.org/documentation/2020/reference-manual/topologies/topology-file-formats.html#tab-topfile2

# TODO: test all these functions


# Functions for virtual_sites2

# vs_2 func 1 -> Linear combination using 2 reference points
# weighted COG using a percentage in [0, 1]
# the weight is applied on the bead ID that comes first
def vs2_func_1(ns, traj, vs_def_beads_ids, vs_params, bead_id):

    i, j = vs_def_beads_ids
    a = vs_params  # weight
    if a < 0 or a > 1:
        msg = f"Virtual site ID {bead_id + 1} uses an incorrect weight. Expected weight in [0 , 1]."
        raise exceptions.MissformattedFile(msg)
    weights = np.array([a, 1-a])

    for ts in ns.aa2cg_universe.trajectory:
        traj[ts.frame] = ns.aa2cg_universe.atoms[[i, j]].center(weights)


# vs_2 func 2 -> Linear combination using 2 reference points
# on the vector from i to j, at given distance (nm)
# NOTE: it seems this one exists only since GROMACS 2020
# TODO: check this one with a GMX 2020 installation
def vs2_func_2(ns, traj, vs_def_beads_ids, vs_params, bead_id):

    i, j = vs_def_beads_ids
    a = vs_params  # nm
    a = a * 10  # retrieve amgstrom for MDA
    if a <= 0:
        msg = f"Virtual site ID {bead_id + 1} uses an incorrect distance parameter. Expected d > 0."
        raise exceptions.MissformattedFile(msg)

    for ts in ns.aa2cg_universe.trajectory:
        pos_i = ns.aa2cg_universe.atoms[i].position
        pos_j = ns.aa2cg_universe.atoms[j].position
        traj[ts.frame] = pos_i + a * (pos_i-pos_j) / np.abs(pos_i-pos_j)


# Functions for virtual_sites3

# vs_3 func 1 -> Linear combination using 3 reference points
# in the plane, using sum of vectors from i to j and from k to i
def vs3_func_1(ns, traj, vs_def_beads_ids, vs_params):

    i, j, k = vs_def_beads_ids
    a, b = vs_params  # nm, nm
    a, b = a * 10, b * 10  # retrieve amgstrom for MDA

    for ts in ns.aa2cg_universe.trajectory:
        pos_i = ns.aa2cg_universe.atoms[i].position
        pos_j = ns.aa2cg_universe.atoms[j].position
        pos_k = ns.aa2cg_universe.atoms[k].position
        traj[ts.frame] = pos_i + a * (pos_i-pos_j) / np.abs(pos_i-pos_j) + b * (pos_i-pos_k) / np.abs(pos_i-pos_k)


# vs_3 func 2 -> Linear combination using 3 reference points
# in the plane, using WEIGHTS sum of vectors from j to i and from k to i + fixed distance
# I used their formula (hopefully) so the form differs from the explanation on line above, but it should be identical
def vs3_func_2(ns, traj, vs_def_beads_ids, vs_params, bead_id):

    i, j, k = vs_def_beads_ids
    a, b = vs_params  # weight, nm
    b = b * 10  # retrieve amgstrom for MDA
    if a < 0 or a > 1:
        msg = f"Virtual site ID {bead_id + 1} uses an incorrect weight. Expected weight in [0 , 1]."
        raise exceptions.MissformattedFile(msg)

    for ts in ns.aa2cg_universe.trajectory:
        pos_i = ns.aa2cg_universe.atoms[i].position
        pos_j = ns.aa2cg_universe.atoms[j].position
        pos_k = ns.aa2cg_universe.atoms[k].position
        traj[ts.frame] = pos_i - b * (
            ((1-a) * (pos_i-pos_j) + a * (pos_k-pos_j)) / np.abs((1-a) * (pos_i-pos_j) + a * (pos_k-pos_j))
        )


# vs_3 func 3 -> Linear combination using 3 reference points
# angle in the plane defined, at given distance of the 3rd point
def vs3_func_3(ns, traj, vs_def_beads_ids, vs_params):

    i, j, k = vs_def_beads_ids
    ang_deg, d = vs_params  # degrees, nm
    d = d * 10  # retrieve amgstrom for MDA

    for ts in ns.aa2cg_universe.trajectory:
        pos_i = ns.aa2cg_universe.atoms[i].position
        pos_j = ns.aa2cg_universe.atoms[j].position
        pos_k = ns.aa2cg_universe.atoms[k].position
        vec_ij = pos_j - pos_i
        vec_jk = pos_k - pos_j
        ang_rad = np.deg2rad(ang_deg)
        comb_ijk = vec_jk - (vec_ij * (np.dot(vec_ij, vec_jk) / np.dot(vec_ij, vec_ij)))
        traj[ts.frame] = pos_i + d * np.cos(ang_rad) * (vec_ij / np.abs(vec_ij)) + d * np.sin(ang_rad) * (comb_ijk / np.abs(comb_ijk))


# vs_3 func 4 -> Linear combination using 3 reference points
# out of plane
# NOTE: tough to implement correctly, documentation seems incomplete
def vs3_func_4(ns, traj, vs_def_beads_ids, vs_params):

    pass


# Functions for virtual_sites4

# vs_4 func 2 -> Linear combination using 3 reference points -> ?
# NOTE: only function 2 is defined for vs_4 in GROMACS
# NOTE: tough to implement correctly, documentation seems incomplete
def vs4_func_2(ns, traj, vs_def_beads_ids, vs_params):

    pass


# Functions for virtual_sitesn

# vs_n func 1 -> Center of Geometry
def vsn_func_1(ns, traj, vs_def_beads_ids):

    for ts in ns.aa2cg_universe.trajectory:
        traj[ts.frame] = ns.aa2cg_universe.atoms[vs_def_beads_ids].center_of_geometry(pbc=None)


# vs_n func 2 -> Center of Mass
def vsn_func_2(ns, traj, vs_def_beads_ids, bead_id):

    # inform user if this VS definition uses beads (or VS) with mass 0,
    # because this is COM so 0 mass means a bead that was marked for defining the VS is in fact ignored
    zero_mass_beads_ids = []
    for bid in vs_def_beads_ids:
        if bid in ns.cg_itp['virtual_sitesn']:
            if ns.cg_itp['virtual_sitesn'][bid]['mass'] == 0:
                zero_mass_beads_ids.append(bid)
    if len(zero_mass_beads_ids) > 0:
        print('  WARNING: Virtual site ID {} uses function 2 for COM, but its definition contains IDs ' + ' '.join(zero_mass_beads_ids) + 'which have no mass'.format(bead_id + 1))

    for ts in ns.aa2cg_universe.trajectory:
        traj[ts.frame] = ns.aa2cg_universe.atoms[vs_def_beads_ids].center_of_mass(pbc=None)


# vs_n func 3 -> Center of Weights (each atom has a given weight, pairwise formatting: id1 w1 id2 w2 ..)
def vsn_func_3(ns, traj, vs_def_beads_ids, vs_params):

    masses_and_weights = np.array([ns.aa2cg_universe.atoms[vs_def_beads_ids[i]].mass * vs_params[i] for i in range(len(vs_def_beads_ids))])
    for ts in ns.aa2cg_universe.trajectory:
        traj[ts.frame] = ns.aa2cg_universe.atoms[vs_def_beads_ids].center(masses_and_weights)






