CC = cc
CXX = c++
CPPFLAGS += -Isrc -Ibuild
CFLAGS ?= -O2 -g -Wall -std=gnu11
CXXFLAGS ?= -O2 -g -Wall -std=c++17
SOURCES := main globalvars ast semantic symbol codegen
OBJECTS := $(SOURCES:%=build/%.o) build/parser.o build/scanner.o

.PHONY: all test render-test comparison images format format-check clean
all: build/shady

build:
	mkdir -p $@

build/parser.c build/parser.tab.h &: src/parser.y | build
	bison --defines=build/parser.tab.h --output=build/parser.c $<

build/scanner.c: src/scanner.l build/parser.tab.h | build
	flex -l --outfile=$@ $<

build/%.o: src/%.c $(wildcard src/*.h) build/parser.tab.h | build
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

build/parser.o: build/parser.c build/parser.tab.h $(wildcard src/*.h)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

build/scanner.o: build/scanner.c build/parser.tab.h $(wildcard src/*.h)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

build/shady: $(OBJECTS)
	$(CC) $(OBJECTS) -lm -o $@

build/render: tools/render.cpp tests/vendor/stb_image_write.h | build
	$(CXX) $(CXXFLAGS) -Itests/vendor $< -lvulkan -o $@

build/mesh.vert.spv: tools/mesh.vert | build
	glslangValidator -V $< -o $@

test: build/shady
	python3 tools/verify.py

render-test: build/shady build/render build/mesh.vert.spv
	python3 tools/verify.py --render

comparison: render-test
	python3 tools/comparison.py

images: render-test
	python3 tools/visuals.py

format:
	clang-format -i src/*.c src/*.h tools/render.cpp

format-check:
	clang-format --dry-run --Werror src/*.c src/*.h tools/render.cpp

clean:
	rm -rf build
