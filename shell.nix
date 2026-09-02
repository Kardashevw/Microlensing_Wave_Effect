{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    cmake
    gcc
    gnumake
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
    echo "CMake:  $(cmake --version | head -n 1)"
    echo "Make:   $(make --version | head -n 1)"
    echo "uv:     $(uv --version)"
  '';
}
