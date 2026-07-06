# CMake generated Testfile for 
# Source directory: C:/Users/Yingjie Huang/Downloads/mnn-custom-inference-lib
# Build directory: C:/Users/Yingjie Huang/Downloads/mnn-custom-inference-lib/build-host-quality
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test([=[xq_kernel_correctness]=] "C:/Users/Yingjie Huang/Downloads/mnn-custom-inference-lib/build-host-quality/xq_kernel_correctness.exe")
set_tests_properties([=[xq_kernel_correctness]=] PROPERTIES  _BACKTRACE_TRIPLES "C:/Users/Yingjie Huang/Downloads/mnn-custom-inference-lib/CMakeLists.txt;88;add_test;C:/Users/Yingjie Huang/Downloads/mnn-custom-inference-lib/CMakeLists.txt;0;")
add_test([=[xq_runtime_correctness]=] "C:/Users/Yingjie Huang/Downloads/mnn-custom-inference-lib/build-host-quality/xq_runtime_correctness.exe")
set_tests_properties([=[xq_runtime_correctness]=] PROPERTIES  ENVIRONMENT "PATH=C:/Users/Yingjie Huang/qwen-phone-npu-trial/third_party/toolchains/w64devkit/bin\\;C:/Users/Yingjie Huang/Downloads/mnn-custom-inference-lib/build-host-quality/customlib" _BACKTRACE_TRIPLES "C:/Users/Yingjie Huang/Downloads/mnn-custom-inference-lib/CMakeLists.txt;100;add_test;C:/Users/Yingjie Huang/Downloads/mnn-custom-inference-lib/CMakeLists.txt;0;")
subdirs("customlib")
