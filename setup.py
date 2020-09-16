from setuptools import setup

setup(
    name="nxbt",
    include_package_data=True,
    long_description_content_type="text/markdown",
    install_requires=[
        "dbus-python>=1.2.16",
        "Flask>=1.1.2",
        "Flask-SocketIO>=4.3.0",
        "eventlet>=0.25.2",
        "blessed>=1.17.9",
        "pynput>=1.6.8",
        "psutil>=5.5.1",
    ],
    extra_require={
        "dev": [
            "pytest"
        ]
    }
)
