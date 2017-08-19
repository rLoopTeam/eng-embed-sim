#include "compile_test_a.h"

// Compiling (any of the following work):
// gcc compile_test_a.c compile_test_main.c -o compile_test_main
// gcc compile_test_main.c compile_test_a.c -o compile_test_main
// gcc *.c -o compile_test_main

int main(void) {
    print_a();
}