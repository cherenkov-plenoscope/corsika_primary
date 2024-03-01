import corsika_primary


def test_exposes_version():
    assert hasattr(corsika_primary, "__version__")
    assert len(corsika_primary.__version__) > 0
    assert "." in corsika_primary.__version__
