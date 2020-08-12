import setuptools

setuptools.setup(
    name="nxbt",
    install_requires=[
        "dbus-python>=1.2.16",
        "Flask>=1.1.2",
        "Flask-SocketIO>=4.3.0",
        "eventlet>=0.25.2",
        "blessed>=1.17.9",
        "pynput>=1.6.8",
    ],
    extra_require={
        "dev": [
            "pytest"
        ]
    }
)
