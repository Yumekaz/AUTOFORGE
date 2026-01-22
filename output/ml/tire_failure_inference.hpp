/**
 * AUTOFORGE - ML Inference Wrapper
 * Tire Failure Prediction using ONNXRuntime
 * 
 * This wrapper loads a pre-trained ONNX model and provides
 * a C++ interface for real-time tire failure prediction.
 * 
 * Model: tire_failure.onnx
 * Input: Tire pressure signals (FL, FR, RL, RR)
 * Output: Failure probability per tire
 */

#ifndef TIRE_FAILURE_INFERENCE_HPP
#define TIRE_FAILURE_INFERENCE_HPP

#include <onnxruntime_cxx_api.h>
#include <array>
#include <vector>
#include <string>
#include <memory>
#include <stdexcept>

namespace autoforge {
namespace ml {

/**
 * Input structure for tire pressure signals
 * All values in PSI (pounds per square inch)
 */
struct TirePressureInput {
    float tire_pressure_fl;  // Front Left
    float tire_pressure_fr;  // Front Right
    float tire_pressure_rl;  // Rear Left
    float tire_pressure_rr;  // Rear Right
    
    // Additional context signals
    float vehicle_speed_kmh;
    float ambient_temperature_c;
};

/**
 * Output structure for failure prediction
 */
struct TireFailurePrediction {
    float failure_prob_fl;   // Probability 0.0 - 1.0
    float failure_prob_fr;
    float failure_prob_rl;
    float failure_prob_rr;
    
    bool is_any_critical() const {
        constexpr float CRITICAL_THRESHOLD = 0.7f;
        return failure_prob_fl > CRITICAL_THRESHOLD ||
               failure_prob_fr > CRITICAL_THRESHOLD ||
               failure_prob_rl > CRITICAL_THRESHOLD ||
               failure_prob_rr > CRITICAL_THRESHOLD;
    }
};

/**
 * @brief ONNX Runtime Inference Wrapper for Tire Failure Prediction
 * 
 * Usage:
 *   TireFailureInference inference("models/tire_failure.onnx");
 *   TirePressureInput input{32.5f, 33.0f, 31.8f, 32.1f, 80.0f, 25.0f};
 *   auto prediction = inference.predict(input);
 */
class TireFailureInference {
public:
    /**
     * @brief Construct inference engine with ONNX model
     * @param model_path Path to tire_failure.onnx model file
     */
    explicit TireFailureInference(const std::string& model_path)
        : env_(ORT_LOGGING_LEVEL_WARNING, "TireFailure")
        , memory_info_(Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault))
    {
        // Configure session options
        Ort::SessionOptions session_options;
        session_options.SetIntraOpNumThreads(1);
        session_options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_EXTENDED);
        
        // Enable CUDA if available (for vehicle ECU with GPU)
        // OrtCUDAProviderOptions cuda_options;
        // session_options.AppendExecutionProvider_CUDA(cuda_options);
        
        // Create session
        session_ = std::make_unique<Ort::Session>(env_, model_path.c_str(), session_options);
        
        // Get input/output metadata
        InitializeIOMetadata();
    }
    
    /**
     * @brief Run inference on tire pressure signals
     * @param input Tire pressure readings from vehicle sensors
     * @return Failure probability prediction for each tire
     */
    TireFailurePrediction predict(const TirePressureInput& input) {
        // ====================================================================
        // STEP 1: Map tire_pressure_fl float signal into input Tensor
        // ====================================================================
        std::array<float, 6> input_data = {
            input.tire_pressure_fl,      // Index 0: Front Left pressure
            input.tire_pressure_fr,      // Index 1: Front Right pressure
            input.tire_pressure_rl,      // Index 2: Rear Left pressure
            input.tire_pressure_rr,      // Index 3: Rear Right pressure
            input.vehicle_speed_kmh,     // Index 4: Vehicle speed context
            input.ambient_temperature_c  // Index 5: Temperature context
        };
        
        // Create input tensor with shape [1, 6] (batch_size=1, features=6)
        std::array<int64_t, 2> input_shape = {1, 6};
        Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
            memory_info_,
            input_data.data(),
            input_data.size(),
            input_shape.data(),
            input_shape.size()
        );
        
        // ====================================================================
        // STEP 2: Run ONNX inference
        // ====================================================================
        const char* input_names[] = {"tire_signals"};
        const char* output_names[] = {"failure_probabilities"};
        
        auto output_tensors = session_->Run(
            Ort::RunOptions{nullptr},
            input_names,
            &input_tensor,
            1,  // num inputs
            output_names,
            1   // num outputs
        );
        
        // ====================================================================
        // STEP 3: Extract output tensor to prediction struct
        // ====================================================================
        float* output_data = output_tensors[0].GetTensorMutableData<float>();
        
        TireFailurePrediction prediction;
        prediction.failure_prob_fl = output_data[0];
        prediction.failure_prob_fr = output_data[1];
        prediction.failure_prob_rl = output_data[2];
        prediction.failure_prob_rr = output_data[3];
        
        return prediction;
    }
    
    /**
     * @brief Batch prediction for multiple samples
     */
    std::vector<TireFailurePrediction> predictBatch(
        const std::vector<TirePressureInput>& inputs
    ) {
        std::vector<TireFailurePrediction> results;
        results.reserve(inputs.size());
        
        for (const auto& input : inputs) {
            results.push_back(predict(input));
        }
        
        return results;
    }

private:
    Ort::Env env_;
    Ort::MemoryInfo memory_info_;
    std::unique_ptr<Ort::Session> session_;
    
    // Input/Output names from model metadata
    std::vector<std::string> input_names_;
    std::vector<std::string> output_names_;
    
    void InitializeIOMetadata() {
        Ort::AllocatorWithDefaultOptions allocator;
        
        // Get input info
        size_t num_inputs = session_->GetInputCount();
        for (size_t i = 0; i < num_inputs; ++i) {
            auto name = session_->GetInputNameAllocated(i, allocator);
            input_names_.emplace_back(name.get());
        }
        
        // Get output info
        size_t num_outputs = session_->GetOutputCount();
        for (size_t i = 0; i < num_outputs; ++i) {
            auto name = session_->GetOutputNameAllocated(i, allocator);
            output_names_.emplace_back(name.get());
        }
    }
};

// ============================================================================
// Convenience function for quick inference
// ============================================================================
inline TireFailurePrediction predictTireFailure(
    const std::string& model_path,
    float fl_pressure,
    float fr_pressure,
    float rl_pressure,
    float rr_pressure,
    float speed_kmh = 0.0f,
    float temp_c = 25.0f
) {
    static TireFailureInference inference(model_path);
    
    TirePressureInput input{
        fl_pressure, fr_pressure,
        rl_pressure, rr_pressure,
        speed_kmh, temp_c
    };
    
    return inference.predict(input);
}

}  // namespace ml
}  // namespace autoforge

#endif  // TIRE_FAILURE_INFERENCE_HPP


// ============================================================================
// Example Usage (can be removed in production)
// ============================================================================
#ifdef AUTOFORGE_EXAMPLE_MAIN

#include <iostream>
#include <iomanip>

int main() {
    using namespace autoforge::ml;
    
    try {
        // Initialize inference engine
        TireFailureInference inference("models/tire_failure.onnx");
        
        // Simulate real-time sensor readings
        TirePressureInput current_reading{
            .tire_pressure_fl = 32.5f,   // Normal: 32-35 PSI
            .tire_pressure_fr = 33.0f,
            .tire_pressure_rl = 28.0f,   // LOW - potential issue!
            .tire_pressure_rr = 32.1f,
            .vehicle_speed_kmh = 80.0f,
            .ambient_temperature_c = 25.0f
        };
        
        // Run prediction
        auto prediction = inference.predict(current_reading);
        
        // Output results
        std::cout << std::fixed << std::setprecision(2);
        std::cout << "=== Tire Failure Prediction ===" << std::endl;
        std::cout << "FL: " << prediction.failure_prob_fl * 100 << "%" << std::endl;
        std::cout << "FR: " << prediction.failure_prob_fr * 100 << "%" << std::endl;
        std::cout << "RL: " << prediction.failure_prob_rl * 100 << "%" << std::endl;
        std::cout << "RR: " << prediction.failure_prob_rr * 100 << "%" << std::endl;
        
        if (prediction.is_any_critical()) {
            std::cout << "\n⚠️  CRITICAL: Tire failure risk detected!" << std::endl;
        }
        
    } catch (const Ort::Exception& e) {
        std::cerr << "ONNX Runtime Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}

#endif  // AUTOFORGE_EXAMPLE_MAIN
