#include <someip/someip.hpp>
#include <onnxruntime_cxx_api.h>
#include <iostream>
#include <string>

class BMSDiagnosticServiceML {
public:
    BMSDiagnosticServiceML() : session(nullptr), service_id(4097), instance_id(1) {}

    void init(const std::string& model_path) {
        try {
            session = Ort::InferenceSession{Ort::Env{ORT_LOGGING_LEVEL_WARNING, "test"}, model_path};
        } catch (const Ort::Exception& e) {
            std::cerr << "Failed to create inference session: " << e.what() << std::endl;
            throw;
        }
    }

    void start_service(someip::server* server) {
        if (!server) {
            throw std::invalid_argument("Server pointer is null");
        }
        server->register_event(service_id, instance_id, 32769, &BMSDiagnosticServiceML::on_battery_warning);
        server->register_method(service_id, instance_id, 1, &BMSDiagnosticServiceML::get_battery_status);
        server->register_method(service_id, instance_id, 3, &BMSDiagnosticServiceML::get_estimated_range);
    }

private:
    Ort::InferenceSession* session;
    someip::service_id_t service_id;
    someip::instance_id_t instance_id;

    void on_battery_warning(someip::message_ptr message) {
        // Implement warning handling logic here
    }

    someip::message_ptr get_battery_status(const someip::request& request) {
        auto response = someip::message::create(request->get_service(), request->get_instance(),
                                               request->getMethod(), request->get_client(), request->get_session());
        response->set_return_code(someip::returncode_type_t::OK);

        try {
            std::vector<float> inputs = {0.85f, 420.0f, -10.0f, 30.0f};
            Ort::MemoryInfo memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
            Ort::Value input_tensor = Ort::Value::CreateTensor<float>(memory_info, inputs.data(), inputs.size(),
                                                                     {1, static_cast<int64_t>(inputs.size())});
            auto output_tensors = session->Run(Ort::RunOptions{nullptr}, nullptr, &input_tensor, 1, nullptr, 1);
            float soc = output_tensors[0].GetTensorMutableData<float>()[0];
            response->set_field("soc", someip::field(soc));
            response->set_field("voltage", someip::field(420.0f));
            response->set_field("current", someip::field(-10.0f));
            response->set_field("temperature", someip::field(30.0f));
            response->set_field("health_status", someip::field(static_cast<uint8_t>(0)));
        } catch (const Ort::Exception& e) {
            std::cerr << "Failed to run inference: " << e.what() << std::endl;
            response->set_return_code(someip::returncode_type_t::NOT_OK);
        }

        return response;
    }

    someip::message_ptr get_estimated_range(const someip::request& request) {
        auto response = someip::message::create(request->get_service(), request->get_instance(),
                                               request->getMethod(), request->get_client(), request->get_session());
        response->set_return_code(someip::returncode_type_t::OK);

        try {
            uint8_t driving_mode = request->get_field("driving_mode").as_uint8();
            float range_km = 100.0f; // Placeholder value
            if (driving_mode != 1) {
                range_km = 0.0f;
            }
            response->set_field("range_km", someip::field(range_km));
        } catch (const std::exception& e) {
            std::cerr << "Failed to process request: " << e.what() << std::endl;
            response->set_return_code(someip::returncode_type_t::NOT_OK);
        }

        return response;
    }
};