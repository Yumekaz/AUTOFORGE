```cpp
#ifndef TIRE_FAILURE_INFERENCE_HPP
#define TIRE_FAILURE_INFERENCE_HPP

#include <onnxruntime_cxx_api.h>
#include <vector>
#include <string>

struct TireFailureResult {
    float failure_score;
};

class TireFailureInference {
public:
    TireFailureInference(const std::string& model_path);
    ~TireFailureInference();

    TireFailureResult Infer(
        float tire_pressure_fl, 
        float tire_pressure_fr, 
        float tire_pressure_rl, 
        float tire_pressure_rr, 
        float vehicle_speed_kmh, 
        float ambient_temperature_c
    );

private:
    Ort::Env env_;
    Ort::Session session_;
    std::vector<const char*> input_names_;
    std::vector<int64_t> input_dims_;
    std::vector<Ort::Value> input_tensors_;

    void PrepareInput(float tire_pressure_fl, float tire_pressure_fr, float tire_pressure_rl, float tire_pressure_rr, float vehicle_speed_kmh, float ambient_temperature_c);
};

#endif // TIRE_FAILURE_INFERENCE_HPP
```