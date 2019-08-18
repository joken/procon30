cmake_minimum_required(VERSION 3.5)
project(Procon30Simulator CXX)

set(CMAKE_CXX_STAMDARD 17)
set(CMAKE_CXX_FLAGS "-std=c++17 -lboost_system -lboost_thread -lpthread -Wall -Wextra -g -O3")
add_subdirectory(src)
set(CMAKE_VERBOSE_MAKEFILE TRUE)