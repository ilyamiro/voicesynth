{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python3
    pkgs.python3Packages.setuptools
    pkgs.python3Packages.wheel
    pkgs.python3Packages.twine
  ];

  shellHook = ''
    alias pypi-push='rm -rf dist/ build/ *.egg-info && \
                     python3 setup.py sdist bdist_wheel && \
                     twine upload --config-file .pypirc dist/*'
    
    echo "Run 'pypi-push' to rebuild and upload your project using .pypirc"
  '';
}
