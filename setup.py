from setuptools import setup, find_packages

setup(
    name="widget-automation-tool",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for automating mouse interactions in minigames.",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pyautogui",
        "opencv-python",
        "pytesseract",
        "Pillow",
        "numpy",
        "pygetwindow",
        "pyperclip",
        "psutil",
    ],
    entry_points={
        "console_scripts": [
            "widget-automation-tool=main:main",
        ],
    },
)
