cmake_minimum_required(VERSION 3.8)
project(bringup)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)

# ========================================================================
# INSTALL RULES
# ========================================================================

# 1. Install the launch directory
# This copies everything in your local 'launch/' folder to the 
# package's share directory where ROS looks for it.
install(DIRECTORY
  launch config
  DESTINATION share/${PROJECT_NAME}
)

# 2. (Optional) Install config directory
# Since you are using YAML files (like bno055_config.yaml), 
# you should uncomment this if you have a 'config' folder.
# install(DIRECTORY
#   config
#   DESTINATION share/${PROJECT_NAME}
# )

# ========================================================================

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()