from setuptools import setup

setup(
    name="nxbt",
    include_package_data=True,
    long_description_content_type="text/markdown",
    install_requires=[
        "dbus-python==1.2.16",
        "Flask~=2.0.0",
        "Flask-SocketIO~=5.1.0",
        "eventlet~=0.33.0",
        "blessed==1.17.10",
        "pynput==1.7.1",
        "psutil==5.6.6",
        "cryptography==3.3.2",
    ],
    extra_require={
        "dev": [
            "pytest"
        ]
    }
)
