import corsika_primary as cpw
import numpy as np

PAR = cpw.particles.identification.PARTICLES


def test_init():
    zoo = cpw.particles.identification.Zoo()

    # check default media
    assert "water" in zoo.media_cherenkov_threshold_lorentz_factor
    assert "atmosphere_2200m" in zoo.media_cherenkov_threshold_lorentz_factor

    keV = 1e3 / 1e9
    MeV = 1e6 / 1e9
    GeV = 1e9 / 1e9

    assert zoo.has(corsika_id=PAR["gamma"])
    assert zoo.mass_GeV(PAR["gamma"]) == 0.0
    assert zoo.electric_charge(PAR["gamma"]) == 0.0

    assert zoo.has(corsika_id=PAR["proton"])
    assert 0.9 * GeV < zoo.mass_GeV(PAR["proton"]) < 1 * GeV
    assert zoo.electric_charge(PAR["proton"]) == 1

    assert zoo.has(corsika_id=PAR["neutron"])
    assert 0.9 * GeV < zoo.mass_GeV(PAR["neutron"]) < 1 * GeV
    assert zoo.electric_charge(PAR["neutron"]) == 0

    assert zoo.has(corsika_id=PAR["electron"])
    assert 500 * keV < zoo.mass_GeV(PAR["electron"]) < 520 * keV
    assert zoo.electric_charge(PAR["electron"]) == -1

    IRON = 5626
    assert zoo.has(IRON)
    assert 50 * GeV < zoo.mass_GeV(IRON) < 56 * GeV
    assert zoo.electric_charge(IRON) == 26

    # water cherenkov
    threshold_total_energy_GeV = {
        "electron": 0.8 * MeV,
        "muon_minus": 160 * MeV,
        "proton": 1.4 * GeV,
    }
    for pkey in threshold_total_energy_GeV:
        c = 1
        E = threshold_total_energy_GeV[pkey]
        m = zoo.mass_GeV(PAR[pkey])
        p = np.sqrt((E ** 2 / c ** 2) - m ** 2 * c ** 2)
        momentum_GeV = p

        assert zoo.cherenkov_emission(
            PAR[pkey],
            momentum_GeV=[1.1 * momentum_GeV, 0, 0],
            medium_key="water",
        )
        assert not zoo.cherenkov_emission(
            PAR[pkey],
            momentum_GeV=[0.9 * momentum_GeV, 0, 0],
            medium_key="water",
        )
