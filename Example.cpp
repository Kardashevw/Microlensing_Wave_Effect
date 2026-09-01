#include <cstdlib>
#include <exception>
#include <filesystem>
#include <iostream>
#include <string>

#include "./Micro_field_adaptive.h"

using namespace std;
namespace fs = std::filesystem;

int main(int argc, char* argv[])
{
    double kappa = 0.45;
    double gamma = 0.45;
    double kappaStar_stellar = 0.03;
    double LensRedshift = 0.5;
    double SourceRedshift = 1.0;

    int thread_count = 8;
    int precision_factor = 10;
    int field_id = 15;

    for (int i = 1; i < argc; ++i)
    {
        string arg = argv[i];

        if (arg == "--help" || arg == "-h")
        {
            cout
                << "Usage: ./Example [options]\n\n"
                << "Options:\n"
                << "  --kappa VALUE\n"
                << "  --gamma VALUE\n"
                << "  --kappa-star VALUE\n"
                << "  --lens-z VALUE\n"
                << "  --source-z VALUE\n"
                << "  --threads VALUE\n"
                << "  --precision-factor VALUE\n"
                << "  --field-id VALUE\n";
            return 0;
        }

        if (i + 1 >= argc)
        {
            cerr << "Missing value for " << arg << endl;
            return 2;
        }

        string value = argv[++i];

        try
        {
            if (arg == "--kappa")
                kappa = stod(value);
            else if (arg == "--gamma")
                gamma = stod(value);
            else if (arg == "--kappa-star")
                kappaStar_stellar = stod(value);
            else if (arg == "--lens-z")
                LensRedshift = stod(value);
            else if (arg == "--source-z")
                SourceRedshift = stod(value);
            else if (arg == "--threads")
                thread_count = stoi(value);
            else if (arg == "--precision-factor")
                precision_factor = stoi(value);
            else if (arg == "--field-id")
                field_id = stoi(value);
            else
            {
                cerr << "Unknown option: " << arg << endl;
                return 2;
            }
        }
        catch (const exception&)
        {
            cerr << "Invalid value for " << arg << ": " << value << endl;
            return 2;
        }
    }

    if (thread_count <= 0)
    {
        cerr << "--threads must be > 0" << endl;
        return 2;
    }
    if (precision_factor <= 0)
    {
        cerr << "--precision-factor must be > 0" << endl;
        return 2;
    }
    if (field_id < 0)
    {
        cerr << "--field-id must be >= 0" << endl;
        return 2;
    }

    const string id = to_string(field_id);
    fs::create_directories("MicroField_" + id);
    fs::create_directories("ResultMinimum_" + id);
    fs::create_directories("ResultSaddle_" + id);
    fs::create_directories("ResultMaximum_" + id);
    fs::create_directories("Freq_Time_Domain_Result_" + id);

    cout << "Simulation configuration:" << endl;
    cout << "  kappa            = " << kappa << endl;
    cout << "  gamma            = " << gamma << endl;
    cout << "  kappa_star       = " << kappaStar_stellar << endl;
    cout << "  lens_z           = " << LensRedshift << endl;
    cout << "  source_z         = " << SourceRedshift << endl;
    cout << "  threads          = " << thread_count << endl;
    cout << "  precision_factor = " << precision_factor << endl;
    cout << "  field_id         = " << field_id << endl;

    return MainDiffraction(
        kappa,
        gamma,
        kappaStar_stellar,
        LensRedshift,
        SourceRedshift,
        thread_count,
        precision_factor,
        field_id
    );
}
