#include <stdio.h>
#include <sys/stat.h>

int non_zero_initalized = 3;
int zero_initalized = 0;

extern int _end;

void *_sbrk(int incr) {
  static unsigned char *heap = NULL;
  unsigned char *prev_heap;

  if (heap == NULL) {
    heap = (unsigned char *)&_end;
  }
  prev_heap = heap;

  heap += incr;

  return prev_heap;
}

int _close(int file) {
  return -1;
}

int _fstat(int file, struct stat *st) {
  st->st_mode = S_IFCHR;

  return 0;
}

int _isatty(int file) {
  return 1;
}

int _lseek(int file, int ptr, int dir) {
  return 0;
}

void _exit(int status) {
  while(1);
}

void _kill(int pid, int sig) {
  return;
}

int _getpid(void) {
  return -1;
}

int _write (int file, char * ptr, int len) {
  int written = 0;

  if ((file != 1) && (file != 2) && (file != 3)) {
    return -1;
  }

    return len;
}

int _read (int file, char * ptr, int len) {
  int read = 0;

  if (file != 0) {
    return -1;
  }

  return 0;
}

#define SCS_BASE            (0xE000E000UL)                            /*!< System Control Space Base Address */
#define SysTick_BASE        (SCS_BASE +  0x0010UL)                    /*!< SysTick Base Address */
#define NVIC_BASE           (SCS_BASE +  0x0100UL)                    /*!< NVIC Base Address */
#define SCB_BASE            (SCS_BASE +  0x0D00UL)                    /*!< System Control Block Base Address */

// from the original ELF program
void* (*HAL_TIM_PeriodElapsedCallback)(void*) = (void*(*)(void*))0x080032ad;
void* htim16 = (void*)0x20000218;

void check_call(){
    printf("Check_Call Called\n");
}

void irq_handler() {
  printf("irq handler\n");
  // Call handler directly.
  // If we just call the IRQ handler, it will check to see if the interrupt is
  // enabled by checking bit 0 (UIF) of SR of TIM16. This is hard to emulate,
  // as we would have to modify the GenericPeripheral model that is mapped to
  // 0x40000000 to set this bit on interrupts.
  (*HAL_TIM_PeriodElapsedCallback)(htim16);
}

int main(){

    puts("Hello, world!");

    check_call();

    // enable NVIC vector 21
    // ISER register
    *(uint32_t*)(NVIC_BASE + 0) = 1 << 21;

    *(void**)(0x00000094) = &irq_handler;

    return 0;
}

void exit(int __status){
    while(1);
}
