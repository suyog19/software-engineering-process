"""Build hook that packages canonical non-Python contracts without duplicating sources."""
from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithPolicy(build_py):
    def run(self):
        super().run()
        target = Path(self.build_lib) / "engineering_process" / "_data"
        for name in ("policy", "schemas", "skills", "templates"):
            shutil.copytree(name, target / name, dirs_exist_ok=True)


setup(cmdclass={"build_py": BuildWithPolicy})

