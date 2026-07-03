cmake_minimum_required(VERSION 3.22)
project(xqwen35_mnn_customlib LANGUAGES C CXX)

option(XQ_BUILD_TESTS "Build host-side correctness tests" ON)
option(XQ_ENABLE_MNN "Compile MNN bridge integration when MNN headers/libs are supplied" OFF)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_subdirectory(customlib)

if(ANDROID)
  add_library(xqbench_jni SHARED android/benchmark_app/src/main/cpp/benchmark_jni.cpp)
  target_link_libraries(xqbench_jni PRIVATE xqwen35 log)
  target_include_directories(xqbench_jni PRIVATE customlib/include)

  add_library(xqstock_jni SHARED android/app/src/main/cpp/stock_benchmark_jni.cpp)
  target_link_libraries(xqstock_jni PRIVATE xqwen35 log)
  target_include_directories(xqstock_jni PRIVATE customlib/include)
endif()

if(XQ_BUILD_TESTS AND NOT ANDROID)
  enable_testing()

  add_executable(xq_kernel_correctness customlib/tests/kernel_correctness/test_kernels.cpp)
  target_link_libraries(xq_kernel_correctness PRIVATE xqwen35)
  target_include_directories(xq_kernel_correctness PRIVATE customlib/kernels)
  add_test(NAME xq_kernel_correctness COMMAND xq_kernel_correctness)

  add_executable(xq_runtime_correctness customlib/tests/runtime_correctness/test_runtime.cpp)
  target_link_libraries(xq_runtime_correctness PRIVATE xqwen35)
  add_test(NAME xq_runtime_correctness COMMAND xq_runtime_correctness)
endif()
