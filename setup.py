from setuptools import setup

setup(
    name="LogsOdysseys",
    options={
        "build_apps": {
            # Files to include in the distribution
            "include_patterns": [
                "**/*.png",
                "**/*.jpg",
                "**/*.egg",
                "**/*.wav",
                "**/*.vert",
                "**/*.frag",
                
                "README.md",
                "LICENSE",
            ],
            "exclude_patterns": [
                "**/*.pyc",
                "**/__pycache__/**",
                "**/.git/**",
                "**/.github/**",
            ],
            # GUI applications
            "gui_apps": {
                "LogsOdysseys": "main.py",
            },
            
            # Platforms to build for
            "platforms": [
                "win_amd64",
                "macosx_10_13_x86_64",
                "linux_x86_64",
            ],
            # Add plugins for specific functionality
            "plugins": [
                "pandagl",
                "p3openal_audio",
            ],
            # Dependencies
            "requirements_path": "./requirements.txt",
        }
    },
    # Application metadata
    version="0.1.0",
    description="A log-floating game with semi-realistic water simulation",
    author="omn14",
    author_email="sirole@gmail.com",
    # Python dependencies
    install_requires=[
        "panda3d>=1.10",
        "numpy>=1.21",
    ],
)
