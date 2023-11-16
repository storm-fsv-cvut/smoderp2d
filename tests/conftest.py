def pytest_addoption(parser):
    parser.addoption("--config", action="store", default="quicktest_rill.ini")
    parser.addoption("--reference_dir", action="store", default=None)
