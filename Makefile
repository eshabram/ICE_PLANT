CXX := g++
CXXFLAGS := -std=c++17 -Wall -Wextra -O0 -g -Iinclude

SRC := $(wildcard src/*.cpp)
OBJ := $(patsubst src/%.cpp, build/%.o, $(SRC))
BIN := build/myproject

all: $(BIN)

$(BIN): $(OBJ)
	$(CXX) $(OBJ) -o $@

build/%.o: src/%.cpp | build
	$(CXX) $(CXXFLAGS) -c $< -o $@

build:
	mkdir -p build

run: $(BIN)
	./$(BIN)

clean:
	rm -rf build

.PHONY: all run clean
