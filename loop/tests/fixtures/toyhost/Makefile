# Toy host build. Two targets matter to the integration loop:
#   make        -> build/toysim   (the simulator the gate builds and runs)
#   make test   -> build/toytest  (the correctness suite the gate runs)
#
# LIB_SRCS is a wildcard on purpose: an integration agent adding
# src/<feature>.cpp gets it compiled into both binaries without editing this
# file, so a missing Makefile edit can never masquerade as a build failure.

CXX      ?= g++
CXXFLAGS ?= -O2 -std=c++17 -Wall -Wextra -Isrc

LIB_SRCS  := $(filter-out src/sim.cpp,$(wildcard src/*.cpp))
HDRS      := $(wildcard src/*.h)
TEST_SRCS := $(wildcard tests/*.cpp)

all: build/toysim

build:
	mkdir -p build

build/toysim: src/sim.cpp $(LIB_SRCS) $(HDRS) | build
	$(CXX) $(CXXFLAGS) -o $@ src/sim.cpp $(LIB_SRCS)

build/toytest: $(TEST_SRCS) $(LIB_SRCS) $(HDRS) | build
	$(CXX) $(CXXFLAGS) -o $@ $(TEST_SRCS) $(LIB_SRCS)

test: build/toytest
	./build/toytest

clean:
	rm -rf build

.PHONY: all test clean
