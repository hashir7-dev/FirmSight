#include <stdio.h>
#include <unistd.h>

int main(void) {
    int counter = 0;
    while (1) {
        printf("Dummy process running... tick %d\n", counter++);
        sleep(2);
    }
    return 0;
}
