from setuptools import setup

setup(
    name="nxbt",
    include_package_data=True,
    long_description_content_type="text/markdown",
    install_requires=[
        "dbus-python==1.2.16",
        "Flask==2.1.3",
        "Flask-SocketIO==5.3.4",
        "eventlet==0.33.3",
        "blessed==1.17.10",
        "pynput==1.7.1",
        "psutil==5.6.6",
        "cryptography==3.3.2",
        "jinja2==3.0.3",
        "itsdangerous==2.0.1",
        "Werkzeug==2.0.3",
    ],
    extra_require={
        "dev": [
            "pytest"
        ]
    }
)
