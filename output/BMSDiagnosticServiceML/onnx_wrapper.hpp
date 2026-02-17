```cpp
#pragma once

#include <onnxruntime_cxx_api.h>
#include <vector>
#include <string>

struct TireFailureResult {
    float failure_score;
};

class TireFailureInferenceWrapper {
public:
    TireFailureInferenceWrapper(const std::string& model_path);
    ~TireFailureInferenceWrapper();

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
    std::vector<const char*> input_names_ = {"tire_pressure_fl", "tire_pressure_fr", "tire_pressure_rl", "tire_pressure_rr", "vehicle_speed_kmh", "ambient_temperature_c"};
    std::vector<const char*> output_names_ = {"failure_score"};

    Ort::MemoryInfo memory_info_;
};

TireFailureInferenceWrapper::TireFailureInferenceWrapper(const std::string& model_path) {
    Ort::ThrowOnError(OrtSessionOptionsCreate(&session_options_));
    Ort::ThrowOnError(OrtEnvCreate(ORT_LOGGING_LEVEL_WARNING, "", &env_));

    Ort::ThrowOnError(OrtSessionOptionsAppendExecutionProvider_CUDA(session_options_, 0));
    Ort::ThrowOnError(OrtSessionOptionsAppendExecutionProvider_CPU(session_options_, 1));

    Ort::ThrowOnError(OrtSessionCreate(env_, model_path.c_str(), session_options_, &session_));
    Ort::ThrowOnError(OrtSessionGetInputCount(session_, &input_count_));
    Ort::ThrowOnError(OrtSessionGetOutputCount(session_, &output_count_));

    memory_info_ = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
}

TireFailureInferenceWrapper::~TireFailureInferenceWrapper() {
    Ort::Release(session_);
    Ort::Release(env_);
}

TireFailureResult TireFailureInferenceWrapper::Infer(
    float tire_pressure_fl, 
    float tire_pressure_fr, 
    float tire_pressure_rl, 
    float tire_pressure_rr, 
    float vehicle_speed_kmh, 
    float ambient_temperature_c
) {
    std::vector<float> input_data = {tire_pressure_fl, tire_pressure_fr, tire_pressure_rl, tire_pressure_rr, vehicle_speed_kmh, ambient_temperature_c};
    Ort::Value input_tensor = Ort::Value::CreateTensor<float>(memory_info_, input_data.data(), input_data.size(), input_dims_.data(), input_dims_.size());

    std::vector<Ort::Value> output_tensors;
    Ort::ThrowOnError(OrtSessionRun(session_, nullptr, input_names_.data(), &input_tensor, 1, output_names_.data(), output_count_, output_tensors.data()));

    float failure_score = *output_tensors[0].GetTensorMutableData<float>();
    return {failure_score};
}
```