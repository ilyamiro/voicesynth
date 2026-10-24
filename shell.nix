{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python3
    pkgs.python3Packages.setuptools
    pkgs.python3Packages.build
    pkgs.python3Packages.twine
  ];

  shellHook = ''
    alias pypi-push='rm -rf dist/ build/ *.egg-info && \
                     python3 -m build && \
                     twine upload --config-file .pypirc dist/*'
    
    echo "Run 'pypi-push' to rebuild and upload your project using .pypirc"
  '';
}
