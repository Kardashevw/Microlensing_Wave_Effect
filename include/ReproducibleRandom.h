#pragma once

#include <cstdint>
#include <string>

void SetSimulationSeed(std::uint32_t seed);
std::uint32_t GetSimulationSeed();

double* SampleResultSeeded(
    int NStarStellar,
    int NStarRemnant,
    std::string IMFType
);

double* CreatMicroLensSeeded(
    double SkyLimitX,
    double SkyLimitY,
    int NStar
);
