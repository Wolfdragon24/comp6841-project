// gcc main.c -o main -fno-stack-protector -m32 -z execstack

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define SIZE 32

void setupVal(void);
void win(void);
void checkForThoughts(void);

int start = 0;
int guess;

int main(int argc, char **argv) {
    setbuf(stdout, NULL);

    setupVal();
    char string[SIZE];

    printf("Hello there, what's your name?:\n");
    fgets(string, SIZE, stdin);

    printf("Welcome ");
    printf(string);

    printf("What secret number do you think I'd pick?:\n");
    scanf(" %d", &guess);

    printf("%d is a nice guess, any other thoughts?:\n", guess);
    checkForThoughts();

    printf("Farewell!\n");

    return 0;
}

void checkForThoughts(void) {
    char stringTwo[SIZE];
    scanf("%s", stringTwo);
}

void setupVal(void) {
    srand(time(NULL));

    start = rand();
}

void win(void) {
    if (start == guess) {
        printf("Trail well followed, here is your flag: \"DOM_CTF{TRAILBLAZED_THE_DOUBLE}\"!\n");
    } else {
        printf("Hmmm... how did you get here?\n");
    }
};
