#include "./ReproducibleRandom.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <vector>

#include "./spline.h"

namespace {

std::uint32_t simulation_seed = 12345;

constexpr double kStellarMassMin = 0.08;
constexpr double kStellarMassMax = 1.5;


double normalization_chabrier(double stellar_mass_min, double stellar_mass_max)
{
    const double step = 0.001;
    const int step_num = static_cast<int>((stellar_mass_max - stellar_mass_min) / step);
    double pdf = 0.0;
    double mass = stellar_mass_min;

    for (int i = 0; i < step_num; ++i)
    {
        if (mass < 1.0)
            pdf += 0.158 / mass * std::exp(-0.5 * std::pow((std::log10(mass) - std::log10(0.079)) / 0.69, 2));
        else
            pdf += 0.0443 * std::pow(mass, -2.3);

        mass += step;
    }

    return pdf * step;
}


double chabrier_imf(double mass, double normalization)
{
    if (mass < 1.0)
        return 0.158 / mass * std::exp(-0.5 * std::pow((std::log10(mass) - std::log10(0.079)) / 0.69, 2)) / normalization;

    return 0.0443 * std::pow(mass, -2.3) / normalization;
}


double salpeter_imf(double mass)
{
    const double exponent = -1.35;
    const double normalization =
        (std::pow(kStellarMassMax, exponent) - std::pow(kStellarMassMin, exponent)) / exponent;

    return std::pow(mass, -2.35) / normalization;
}


void load_remnant_mass_function(
    std::vector<double>& masses,
    std::vector<double>& pdf
)
{
    std::ifstream file("SampleMethod/Remnant_MF.csv");
    if (!file.is_open())
    {
        std::cerr << "Failed to open SampleMethod/Remnant_MF.csv" << std::endl;
        std::exit(EXIT_FAILURE);
    }

    std::string line;
    int row = 0;
    while (std::getline(file, line))
    {
        std::istringstream input(line);
        std::string value;

        while (std::getline(input, value, ','))
        {
            if (value.empty())
                continue;

            if (row % 2 == 0)
                masses.push_back(std::stod(value));
            else
                pdf.push_back(std::stod(value));
        }

        ++row;
    }

    if (masses.size() <= 2 || pdf.size() <= 2 || masses.size() != pdf.size())
    {
        std::cerr << "Invalid remnant mass function data:" << std::endl;
        std::cerr << "  masses: " << masses.size() << std::endl;
        std::cerr << "  PDFs:   " << pdf.size() << std::endl;
        std::exit(EXIT_FAILURE);
    }
}

}  // namespace


void SetSimulationSeed(std::uint32_t seed)
{
    simulation_seed = seed;
}


std::uint32_t GetSimulationSeed()
{
    return simulation_seed;
}


double* SampleResultSeeded(
    int NStarStellar,
    int NStarRemnant,
    std::string IMFType
)
{
    double* output = new double[NStarStellar + NStarRemnant];

    // Stream 0 is reserved for mass sampling.
    std::seed_seq seed_sequence{
        simulation_seed,
        0x4d415353u  // "MASS"
    };
    std::mt19937 gen(seed_sequence);
    std::uniform_real_distribution<double> uniform01(0.0, 1.0);

    std::vector<double> remnant_mass;
    std::vector<double> remnant_pdf;
    load_remnant_mass_function(remnant_mass, remnant_pdf);

    std::cout << "Loaded " << remnant_mass.size()
              << " remnant mass-function points." << std::endl;

    tk::spline remnant_spline(remnant_mass, remnant_pdf);

    const double remnant_pdf_max = *std::max_element(remnant_pdf.begin(), remnant_pdf.end());
    const double remnant_mass_min = *std::min_element(remnant_mass.begin(), remnant_mass.end());
    const double remnant_mass_max = *std::max_element(remnant_mass.begin(), remnant_mass.end());

    std::cout << "ConstCRemnant = " << remnant_pdf_max << std::endl;
    std::cout << "RemnantMassMin = " << remnant_mass_min << std::endl;
    std::cout << "RemnantMassMax = " << remnant_mass_max << std::endl;

    std::uniform_real_distribution<double> remnant_proposal(remnant_mass_min, remnant_mass_max);

    for (int i = 0; i < NStarRemnant; ++i)
    {
        double u = uniform01(gen);
        double mass = remnant_proposal(gen);

        while (u > remnant_spline(mass) / remnant_pdf_max)
        {
            u = uniform01(gen);
            mass = remnant_proposal(gen);
        }

        output[NStarStellar + i] = mass;
    }

    const double chabrier_normalization = normalization_chabrier(kStellarMassMin, kStellarMassMax);
    const double step = 0.01;
    const int step_num = static_cast<int>((kStellarMassMax - kStellarMassMin) / step);
    std::vector<double> pdf_test(step_num);

    if (IMFType == "Chabrier")
    {
        for (int i = 0; i < step_num; ++i)
            pdf_test[i] = chabrier_imf(kStellarMassMin + i * step, chabrier_normalization);
    }
    else if (IMFType == "Salpeter")
    {
        for (int i = 0; i < step_num; ++i)
            pdf_test[i] = salpeter_imf(kStellarMassMin + i * step);
    }
    else
    {
        std::cerr << "Unsupported IMF type: " << IMFType << std::endl;
        delete[] output;
        std::exit(EXIT_FAILURE);
    }

    const double stellar_const =
        *std::max_element(pdf_test.begin(), pdf_test.end()) *
        (kStellarMassMax - kStellarMassMin);

    std::cout << "ConstCStellar = " << stellar_const << std::endl;

    std::uniform_real_distribution<double> stellar_proposal(kStellarMassMin, kStellarMassMax);

    for (int i = 0; i < NStarStellar; ++i)
    {
        double u = uniform01(gen);
        double mass = stellar_proposal(gen);

        auto acceptance = [&](double candidate) {
            const double pdf_value = IMFType == "Chabrier"
                ? chabrier_imf(candidate, chabrier_normalization)
                : salpeter_imf(candidate);

            return pdf_value / stellar_const * (kStellarMassMax - kStellarMassMin);
        };

        while (u > acceptance(mass))
        {
            u = uniform01(gen);
            mass = stellar_proposal(gen);
        }

        output[i] = mass;
    }

    std::ofstream sample_test("SampleMethod/SampleTest.bin", std::ofstream::binary);
    sample_test.write(
        reinterpret_cast<char*>(output),
        sizeof(double) * (NStarStellar + NStarRemnant)
    );

    return output;
}


double* CreatMicroLensSeeded(
    double SkyLimitX,
    double SkyLimitY,
    int NStar
)
{
    double* coordinates = new double[NStar * 2];

    // Stream 1 is reserved for lens positions so changing the number of
    // rejection-sampling draws does not alter the coordinate realization.
    std::seed_seq seed_sequence{
        simulation_seed,
        0x504f5349u  // "POSI"
    };
    std::mt19937 gen(seed_sequence);

    std::uniform_real_distribution<double> disx(-SkyLimitX, SkyLimitX);
    std::uniform_real_distribution<double> disy(-SkyLimitY, SkyLimitY);

    for (long i = 0; i < NStar; ++i)
    {
        coordinates[2 * i] = disx(gen);
        coordinates[2 * i + 1] = disy(gen);
    }

    return coordinates;
}
