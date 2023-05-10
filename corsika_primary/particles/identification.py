import numpy as np

"""
Taken from corsika's SUROUTINE PAMAF
"""


def DATA_MASSES():
    a = [
        0.0e0,
        0.51099893e-3,
        0.51099893e-3,
        0.0e0,
        0.105658372e0,
        0.105658372e0,
        0.1349766e0,
        0.13957018e0,
        0.13957018e0,
        0.497611e0,
        0.493677e0,
        0.493677e0,
        0.93956538e0,
        0.93827205e0,
        0.93827205e0,
        0.497611e0,
        0.547862e0,
        1.115683e0,
        1.18937e0,
        1.192642e0,
        1.197449e0,
        1.31486e0,
        1.32171e0,
        1.67245e0,
        0.93956538e0,
        1.115683e0,
        1.18937e0,
        1.192642e0,
        1.197449e0,
        1.31486e0,
        1.32171e0,
        1.67245e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        1.0e9,
        580.0e0,
        1.0e5,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.95778e0,
        1.019461e0,
        0.78265e0,
        0.7690e0,
        0.7665e0,
        0.7665e0,
        1.2305e0,
        1.2318e0,
        1.2331e0,
        1.2344e0,
        1.2309e0,
        1.2323e0,
        1.2336e0,
        1.2349e0,
        0.89581e0,
        0.89166e0,
        0.89166e0,
        0.89581e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.547862e0,
        0.547862e0,
        0.547862e0,
        0.547862e0,
        0.0e0,
    ]
    return np.array(a)


def DATA_CHARGE():
    """
    Taken from corsika's SUROUTINE PAMAF
    """
    a = [
        0.0e0,
        +1.0e0,
        -1.0e0,
        0.0e0,
        +1.0e0,
        -1.0e0,
        0.0e0,
        +1.0e0,
        -1.0e0,
        0.0e0,
        +1.0e0,
        -1.0e0,
        0.0e0,
        +1.0e0,
        -1.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        +1.0e0,
        0.0e0,
        -1.0e0,
        0.0e0,
        -1.0e0,
        -1.0e0,
        0.0e0,
        0.0e0,
        -1.0e0,
        0.0e0,
        +1.0e0,
        0.0e0,
        +1.0e0,
        +1.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        +1.0e0,
        -1.0e0,
        +2.0e0,
        +1.0e0,
        0.0e0,
        -1.0e0,
        -2.0e0,
        -1.0e0,
        0.0e0,
        +1.0e0,
        0.0e0,
        +1.0e0,
        -1.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
    ]
    return np.array(a)


def DATA_DECTME():
    """
    Taken from corsika's SUROUTINE PAMAF
    """
    a = [
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        2.19698e-6,
        2.19698e-6,
        8.52e-17,
        2.6033e-8,
        2.6033e-8,
        5.116e-8,
        1.2380e-8,
        1.2380e-8,
        880.3e0,
        0.0e0,
        0.0e0,
        0.8954e-10,
        5.02e-19,
        2.632e-10,
        0.8018e-10,
        7.4e-20,
        1.479e-10,
        2.90e-10,
        1.639e-10,
        0.821e-10,
        880.3e0,
        2.632e-10,
        0.8018e-10,
        7.4e-20,
        1.479e-10,
        2.90e-10,
        1.639e-10,
        0.821e-10,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        3.32e-21,
        1.54e-22,
        7.75e-23,
        4.14e-24,
        4.14e-24,
        4.14e-24,
        5.87e-24,
        5.02e-24,
        5.606e-24,
        5.0e-24,
        5.87e-24,
        5.02e-24,
        5.606e-24,
        5.0e-24,
        1.398e-23,
        1.296e-23,
        1.296e-23,
        1.389e-23,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        0.0e0,
        5.02e-19,
        5.02e-19,
        5.02e-19,
        5.02e-19,
        0.0e0,
    ]
    return np.array(a)


PARTICLES = {
    "gamma": 1,
    "positron": 2,
    "electron": 3,
    "muon_plus": 5,
    "muon_minus": 6,
    "pi_zero": 7,
    "pi_plus": 8,
    "pi_minus": 9,
    "kaon_l_zero": 10,
    "kaon_plus": 11,
    "kaon_minus": 12,
    "neutron": 13,
    "proton": 14,
    "anti_proton": 15,
}


def init_particle_table():
    m = DATA_MASSES()
    c = DATA_CHARGE()
    t = DATA_DECTME()
    tab = {}
    for name in PARTICLES:
        corsika_id = PARTICLES[name]
        idx = corsika_id - 1
        tab[corsika_id] = {
            "mass_GeV": m[idx],
            "decay_time_s": t[idx],
            "electric_charge": c[idx],
        }
    return tab


SPEED_OF_LIGHT_M_PER_S = 299792458
REFRACTIVE_INDEX_WATER = 1.33


def refractive_index_atmosphere(altitude_asl_m):
    DENSITY_LENGTH_AIR = 8435.0  # m
    # Rise in altitude by which atmospheric density is reduced by 1/e.
    REFRACTION_AIR_0CELSIUS_1ATM = 1.00027357  # 1

    # refractive index of atmosphere vs. altitude
    return 1.0 + (REFRACTION_AIR_0CELSIUS_1ATM - 1.0) * np.exp(
        -altitude_asl_m / DENSITY_LENGTH_AIR
    )


def decompose_nucleus_a_z(corsika_id):
    """
    a: mass-number
    z: electric charge-number
    """
    corsika_id = int(corsika_id)
    a = corsika_id // 100
    z = corsika_id - (a * 100)
    assert 2 <= a <= 56
    assert z <= 56
    return a, z


def is_nucleus(corsika_id):
    return 201 <= corsika_id <= 5656


def cherenkov_threshold_beta_factor(refractive_index):
    assert refractive_index >= 1.0
    return 1 / refractive_index


def cherenkov_threshold_lorentz_factor(refractive_index):
    beta = cherenkov_threshold_beta_factor(refractive_index)
    # b = sq( 1 - ( 1/g^2) )
    # b^2 = 1 - 1/g^2
    # 1/g^2 = 1 - b^2
    # 1 = (1 - b^2) g^2
    # 1 / (1 - b^2) = g^2
    # g = sq(1 / (1 - b^2))
    return np.sqrt(1 / (1 - beta ** 2))


class Zoo:
    def __init__(self, media_refractive_indices=None):
        if media_refractive_indices == None:
            self.media_refractive_indices = {
                "water": REFRACTIVE_INDEX_WATER,
                "atmosphere_2200m": refractive_index_atmosphere(2200),
            }
        else:
            self.media_refractive_indices = media_refractive_indices
        self.table = init_particle_table()

        self.media_cherenkov_threshold_lorentz_factor = {}
        for medium_key in self.media_refractive_indices:
            lorentz = cherenkov_threshold_lorentz_factor(
                refractive_index=self.media_refractive_indices[medium_key]
            )
            self.media_cherenkov_threshold_lorentz_factor[medium_key] = lorentz

    def has(self, corsika_id):
        if corsika_id in self.table:
            return True
        elif is_nucleus(corsika_id=corsika_id):
            return True
        return False

    def mass_GeV(self, corsika_id):
        assert self.has(corsika_id)

        if is_nucleus(corsika_id=corsika_id):
            a, z = decompose_nucleus_a_z(corsika_id)
            mp = self.table[PARTICLES["proton"]]["mass_GeV"]
            mn = self.table[PARTICLES["neutron"]]["mass_GeV"]
            return a * (1 / 2) * (mn + mp)
        else:
            return self.table[corsika_id]["mass_GeV"]

    def electric_charge(self, corsika_id):
        assert self.has(corsika_id=corsika_id)

        if is_nucleus(corsika_id=corsika_id):
            _, z = decompose_nucleus_a_z(corsika_id)
            return z
        else:
            return self.table[corsika_id]["electric_charge"]

    def cherenkov_emission(self, corsika_id, momentum_GeV, medium_key):
        assert self.has(corsika_id=corsika_id)

        if self.electric_charge(corsika_id) == 0:
            return False

        p2 = momentum_GeV[0] ** 2 + momentum_GeV[1] ** 2 + momentum_GeV[2] ** 2
        m = self.mass_GeV(corsika_id)
        m2 = m ** 2

        c = 1.0
        c2 = c ** 2

        lorentz = np.sqrt(m2 * c2 + p2) / (m * c)

        return (
            lorentz
            >= self.media_cherenkov_threshold_lorentz_factor[medium_key]
        )
