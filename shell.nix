{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    gcc
    python311
    uv
    zlib
  ];

  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
  ];

  UV_PYTHON = "${pkgs.python311}/bin/python3.11";
  UV_PYTHON_DOWNLOADS = "never";

  shellHook = ''
    echo "Microlensing development environment"
    echo "Python: $(python3.11 --version)"
    echo "G++:    $(g++ --version | head -n 1)"
    echo "uv:     $(uv --version)"
  '';
}