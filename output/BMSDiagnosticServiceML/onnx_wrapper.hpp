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
    std::vector<const char*> input_names_;
    std::vector<const char*> output_names_;
};

TireFailureInferenceWrapper::TireFailureInferenceWrapper(const std::string& model_path)
    : env_(ORT_LOGGING_LEVEL_WARNING, "test"), session_(env_, model_path.c_str(), Ort::SessionOptions()) {
    
    Ort::AllocatorWithDefaultOptions allocator;
    Ort::SessionMetadata metadata(session_);
    Ort::SessionOptions session_options;

    input_names_ = {"tire_pressure_fl", "tire_pressure_fr", "tire_pressure_rl", "tire_pressure_rr", "vehicle_speed_kmh", "ambient_temperature_c"};
    output_names_ = {"failure_score"};

    for (const auto& name : input_names_) {
        Ort::AllocatorWithDefaultOptions allocator;
        Ort::TypeInfo type_info = session_.GetInputTypeInfo(allocator.GetMemoryInfo(), 0);
        Ort::TypeAndShapeInfo type_and_shape_info(type_info);
        ONNXTensorElementDataType element_type = type_and_shape_info.GetElementType();
    }

    for (const auto& name : output_names_) {
        Ort::AllocatorWithDefaultOptions allocator;
        Ort::TypeInfo type_info = session_.GetOutputTypeInfo(allocator.GetMemoryInfo(), 0);
        Ort::TypeAndShapeInfo type_and_shape_info(type_info);
        ONNXTensorElementDataType element_type = type_and_shape_info.GetElementType();
    }
}

TireFailureInferenceWrapper::~TireFailureInferenceWrapper() {
    // No-op, resources are managed by RAII
}

TireFailureResult TireFailureInferenceWrapper::Infer(
    float tire_pressure_fl, 
    float tire_pressure_fr, 
    float tire_pressure_rl, 
    float tire_pressure_rr, 
    float vehicle_speed_kmh, 
    float ambient_temperature_c
) {
    Ort::AllocatorWithDefaultOptions allocator;
    std::vector<float> input_data = {tire_pressure_fl, tire_pressure_fr, tire_pressure_rl, tire_pressure_rr, vehicle_speed_kmh, ambient_temperature_c};
    Ort::MemoryInfo memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);

    Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
        memory_info,
        input_data.data(),
        input_data.size(),
        {1, 6},
        ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT
    );

    std::vector<Ort::Value> output_tensors = session_.Run(Ort::RunOptions{nullptr}, input_names_.data(), &input_tensor, 1, output_names_.data(), 1);

    float failure_score = *output_tensors[0].GetTensorMutableData<float>();

    return {failure_score};
}
```