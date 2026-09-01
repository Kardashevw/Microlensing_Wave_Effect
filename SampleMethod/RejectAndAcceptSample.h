#include <iostream>
#include <fstream>
#include <cstdio>
#include <cstdlib>
#include <complex>
#include <time.h>
#include <functional>
#include <algorithm>
#include <ctime>
#include <vector>
#include <thread>
#include <string>
#include <random>
#include "../spline.h"
#include "../ReproducibleRandom.h"

using std::sin;
using std::cos;
using std::tan;
using std::exp; 
using std::pow;
using std::log;
using std::sqrt;
using std::atan;
using std::acos;
using std::log10;

using namespace std;

#define PI acos(-1)

// Keep the legacy implementation available in RejectAndAcceptSample.cpp,
// but route solver call sites through the deterministic implementation.
#define SampleResult(...) SampleResultSeeded(__VA_ARGS__)
