#include <stdio.h>

enum { OP_PUSH, OP_ADD, OP_SUB, OP_MUL, OP_MOD, OP_DUP, OP_SWAP, OP_JNZ, OP_DEC, OP_POP, OP_HALT };

/* Computes acc = (acc * 31 + 7 + seed) % 1000003 in a counted loop */
static const int program[] = {
    OP_PUSH, 0,        /* acc */
    OP_PUSH, 5000,     /* counter */
    /* loop body starts at pc = 4 */
    OP_SWAP,
    OP_PUSH, 31,
    OP_MUL,
    OP_PUSH, 7,
    OP_ADD,
    OP_PUSH, 1000003,
    OP_MOD,
    OP_SWAP,
    OP_DEC,
    OP_DUP,
    OP_JNZ, 4,
    OP_POP,
    OP_HALT
};

int run_vm(int seed) {
    int stack[64];
    int sp = 0;
    int pc = 0;
    for (;;) {
        int op = program[pc++];
        switch (op) {
            case OP_PUSH: stack[sp++] = program[pc++]; break;
            case OP_ADD: sp--; stack[sp - 1] = stack[sp - 1] + stack[sp] + seed; break;
            case OP_SUB: sp--; stack[sp - 1] = stack[sp - 1] - stack[sp]; break;
            case OP_MUL: sp--; stack[sp - 1] = stack[sp - 1] * stack[sp]; break;
            case OP_MOD: sp--; stack[sp - 1] = stack[sp - 1] % stack[sp]; break;
            case OP_DUP: stack[sp] = stack[sp - 1]; sp++; break;
            case OP_SWAP: { int t = stack[sp - 1]; stack[sp - 1] = stack[sp - 2]; stack[sp - 2] = t; } break;
            case OP_JNZ: { int target = program[pc++]; sp--; if (stack[sp] != 0) pc = target; } break;
            case OP_DEC: stack[sp - 1]--; break;
            case OP_POP: sp--; break;
            case OP_HALT: return stack[sp - 1];
            default: return -1;
        }
    }
}

int main() {
    long long total = 0;
    for (int r = 0; r < 60; r++) {
        total = (total + run_vm(r % 13)) % 1000000007LL;
    }
    printf("Bytecode VM Total: %lld\n", total);
    return 0;
}
