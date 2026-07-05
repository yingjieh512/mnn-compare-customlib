cmake_minimum_required(VERSION 3.22)
project(xqwen35_mnn_customlib LANGUAGES C CXX)

option(XQ_BUILD_TESTS "Build host-side correctness tests" ON)
option(XQ_ENABLE_MNN "Compile MNN bridge integration when MNN headers/libs are supplied" OFF)
set(MNN_ANDROID_BUILD_DIR "" CACHE PATH "Path to an Android arm64 MNN build with LLM enabled")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_subdirectory(customlib)

if(ANDROID AND XQ_ENABLE_MNN)
  if(NOT MNN_ANDROID_BUILD_DIR)
    set(MNN_ANDROID_BUILD_DIR "${CMAKE_CURRENT_LIST_DIR}/third_party/MNN/build_android_arm64_llm_sep")
  endif()
  get_filename_component(MNN_ANDROID_BUILD_DIR "${MNN_ANDROID_BUILD_DIR}" ABSOLUTE)

  function(xq_import_mnn_so target_name relative_path)
    add_library(${target_name} SHARED IMPORTED GLOBAL)
    set_target_properties(${target_name} PROPERTIES
      IMPORTED_LOCATION "${MNN_ANDROID_BUILD_DIR}/${relative_path}"
    )
  endfunction()

  xq_import_mnn_so(xq_mnn "OFF/${ANDROID_ABI}/libMNN.so")
  xq_import_mnn_so(xq_mnn_llm "OFF/${ANDROID_ABI}/libllm.so")
  xq_import_mnn_so(xq_mnn_express "express/OFF/${ANDROID_ABI}/libMNN_Express.so")
  xq_import_mnn_so(xq_mnn_cl "source/backend/opencl/OFF/${ANDROID_ABI}/libMNN_CL.so")
  xq_import_mnn_so(xq_mnn_vulkan "source/backend/vulkan/OFF/${ANDROID_ABI}/libMNN_Vulkan.so")

  set(XQ_MNN_INCLUDE_DIRS
    "${CMAKE_CURRENT_LIST_DIR}/third_party/MNN/include"
    "${CMAKE_CURRENT_LIST_DIR}/third_party/MNN/express"
    "${CMAKE_CURRENT_LIST_DIR}/third_party/MNN/source"
    "${CMAKE_CURRENT_LIST_DIR}/third_party/MNN/transformers/llm/engine/include"
  )

  if(TARGET xqwen35)
    target_include_directories(xqwen35 PRIVATE ${XQ_MNN_INCLUDE_DIRS})
    target_link_libraries(xqwen35 PRIVATE xq_mnn_llm xq_mnn xq_mnn_express xq_mnn_cl xq_mnn_vulkan)
  endif()
endif()

if(ANDROID)
  add_library(xqbench_jni SHARED android/benchmark_app/src/main/cpp/benchmark_jni.cpp)
  target_link_libraries(xqbench_jni PRIVATE xqwen35 log dl)
  target_include_directories(xqbench_jni PRIVATE customlib/include customlib/kernels)
  if(XQ_ENABLE_MNN)
    target_compile_definitions(xqbench_jni PRIVATE XQ_ENABLE_MNN=1)
    target_include_directories(xqbench_jni PRIVATE ${XQ_MNN_INCLUDE_DIRS})
    target_link_libraries(xqbench_jni PRIVATE xq_mnn_llm xq_mnn xq_mnn_express xq_mnn_cl xq_mnn_vulkan)
  endif()

  add_library(xqstock_jni SHARED android/app/src/main/cpp/stock_benchmark_jni.cpp)
  target_link_libraries(xqstock_jni PRIVATE xqwen35 log)
  target_include_directories(xqstock_jni PRIVATE customlib/include)
  if(XQ_ENABLE_MNN)
    target_compile_definitions(xqstock_jni PRIVATE XQ_ENABLE_MNN=1)
    target_include_directories(xqstock_jni PRIVATE ${XQ_MNN_INCLUDE_DIRS})
    target_link_libraries(xqstock_jni PRIVATE xq_mnn_llm xq_mnn xq_mnn_express xq_mnn_cl xq_mnn_vulkan)
  endif()
endif()

if(XQ_BUILD_TESTS AND NOT ANDROID)
  enable_testing()
  get_filename_component(XQ_TEST_COMPILER_DIR "${CMAKE_CXX_COMPILER}" DIRECTORY)

  set(XQ_KERNEL_TEST_SOURCES
    customlib/kernels/reference/ref_gemv.cpp
    customlib/kernels/reference/ref_rmsnorm.cpp
    customlib/kernels/reference/ref_rope.cpp
    customlib/kernels/reference/ref_attention.cpp
    customlib/kernels/reference/ref_delta.cpp
    customlib/kernels/generated/generated_dispatch.cpp
    customlib/kernels/generated/arm64_neon/xq_gemv_w4a16_neon.cpp
    customlib/kernels/generated/arm64_neon/xq_gemv_w3a16_neon.cpp
    customlib/kernels/generated/arm64_neon/xq_gemv_w2a16_neon.cpp
  )

  add_executable(xq_kernel_correctness
    customlib/tests/kernel_correctness/test_kernels.cpp
    ${XQ_KERNEL_TEST_SOURCES}
  )
  target_link_libraries(xq_kernel_correctness PRIVATE xqwen35)
  target_include_directories(xq_kernel_correctness PRIVATE customlib/kernels)
  add_test(NAME xq_kernel_correctness COMMAND xq_kernel_correctness)

  add_executable(xq_runtime_correctness
    customlib/tests/runtime_correctness/test_runtime.cpp
    customlib/kernels/reference/ref_gemv.cpp
  )
  target_link_libraries(xq_runtime_correctness PRIVATE xqwen35)
  add_custom_command(TARGET xq_runtime_correctness POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_FILE:xqwen35>
            $<TARGET_FILE_DIR:xq_runtime_correctness>
  )
  add_test(NAME xq_runtime_correctness COMMAND xq_runtime_correctness)
  set_tests_properties(xq_runtime_correctness PROPERTIES
    ENVIRONMENT "PATH=${XQ_TEST_COMPILER_DIR}\\;$<TARGET_FILE_DIR:xqwen35>"
  )
endif()
