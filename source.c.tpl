#include <stdio.h>
#include <sys/mman.h>
#include <unistd.h>
<!--(if threads)-->
#include <pthread.h>
<!--(end)-->

unsigned *regs;

void asm_body(int thread_id) {
    // TODO set up separate stack for user code for second episode
    asm volatile (
        "STMFD r13!, {r0-r12, lr}\n"
        // Zero out registers at start
        <!--(if threads)-->
            // Jump to the right thread label
            <!--(for thread in threads)-->
                "CMP %0, #@!thread!@\n"
                "MOVEQ r0, #0\n" // ugh, but does the job
                "MOVEQ r1, #0\n"
                "MOVEQ r2, #0\n"
                "MOVEQ r3, #0\n"
                "MOVEQ r4, #0\n"
                "MOVEQ r5, #0\n"
                "MOVEQ r6, #0\n"
                "MOVEQ r7, #0\n"
                "MOVEQ r8, #0\n"
                "MOVEQ r9, #0\n"
                "MOVEQ r10, #0\n"
                "MOVEQ r11, #0\n"
                "MOVEQ r12, #0\n"
                "BEQ thread@!thread!@\n"
            <!--(end)-->
        <!--(end)-->
        "MOV r0, #0\n"
        "MOV r1, #0\n"
        "MOV r2, #0\n"
        "MOV r3, #0\n"
        "MOV r4, #0\n"
        "MOV r5, #0\n"
        "MOV r6, #0\n"
        "MOV r7, #0\n"
        "MOV r8, #0\n"
        "MOV r9, #0\n"
        "MOV r10, #0\n"
        "MOV r11, #0\n"
        "MOV r12, #0\n"
        // begin user code
        <!--(for line in source.replace("\r", "").splitlines())-->
        "@!line.replace("\\", "\\\\").replace('%', '%%').replace('"', '\\"')!@\n"
        <!--(end)-->
        // end user code

        <!--(if not threads)-->
        "STMFD r13!, {r0-r12}\n"
        "MOV r0, #0x500\n"
        "MOV r0, r0, LSL #16\n"
        "MOV r1, #0\n"
        "loop:\n"
        "LDMFD r13!, {r2}\n"
        "STR r2, [r0, r1, LSL #2]\n"
        "ADD r1, r1, #1\n"
        "CMP r1, #12\n"
        "BLS loop\n"
        <!--(end)-->
        "LDMFD r13!, {r0-r12, lr}\n"
        :
        : <!--(if threads)--> "r" (thread_id) <!--(end)-->
        : //"r0", "r1", "r2", "r3", "r4", "r5", "r6", "r8", "r9", "r10", "r11", "r12"
    );
    <!--(if not threads)-->
        printf("--------------------------------%s\n", "");
        printf("Obsah registrů na konci programu%s\n", "");
        printf("--------------------------------%s\n", "");
        printf("\n%s", "");
        for (int i = 0; i <= 12; i++) {
            //printf("r%d=%08x\n", i, regs[i]);
            printf("r%d = %u / %d / 0x%x\n", i, regs[i], regs[i], regs[i]);
        }
        printf("\n");
    <!--(end)-->
}

int main() {
    regs = (unsigned*)mmap((void*)0x5000000U, 4096, PROT_READ|PROT_WRITE, MAP_FIXED|MAP_ANONYMOUS|MAP_PRIVATE, -1, 0);
    void* data = (unsigned*)mmap((void*)0x100000U, 1024*4096, PROT_READ|PROT_WRITE, MAP_FIXED|MAP_ANONYMOUS|MAP_PRIVATE, -1, 0);
    //void* aux = (unsigned*)mmap((void*)0x8000000U, 1024*4096, PROT_READ|PROT_WRITE, MAP_FIXED|MAP_ANONYMOUS|MAP_PRIVATE, -1, 0);
    if (regs == NULL || data == NULL) {
        fprintf(stderr, "mmap error: %m\n");
        return 0;
    }

    void *page;
    page = (void *) ((unsigned long) (&printf) & ~(getpagesize() - 1));
    mprotect(page, getpagesize(), PROT_READ | PROT_WRITE | PROT_EXEC);
    page = (void *) ((unsigned long) (&main) & ~(getpagesize() - 1));
    mprotect(page, getpagesize(), PROT_READ | PROT_WRITE | PROT_EXEC);
    <!--(if threads)-->
        pthread_t pthrs[@!len(threads)!@];
        <!--(for idx, thread in enumerate(threads))-->
            //asm_body(@!thread!@); // test
            pthread_create(pthrs+@!idx!@, NULL, asm_body, (void *)@!thread!@);
        <!--(end)-->
        <!--(for idx, thread in enumerate(threads))-->
            pthread_join(pthrs[@!idx!@], NULL);
        <!--(end)-->
    <!--(else)-->
        asm_body(-1);
    <!--(end)-->
    return 0;
}

