cmake_minimum_required(VERSION 3.16)
project(MicrolensingWaveEffect LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Threads REQUIRED)

add_executable(microlensing
    app/microlensing.cpp
    src/Micro_field_adaptive.cpp
    src/GetPsi_micro_field.cpp
    src/CosMoCal.cpp
    src/ReproducibleRandom.cpp
)

target_include_directories(microlensing PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Match the historical build flags used by Example.sh.
target_compile_options(microlensing PRIVATE -O3 -g)
target_link_libraries(microlensing PRIVATE Threads::Threads m)
