#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Дефинираме структура за основните данни в заглавието на .d2s
typedef struct {
    unsigned int header_id; // D2S\0x1A
    unsigned int version;
    char char_name[16];
    unsigned char char_class;
    unsigned int level;
} D2S_Header;

int read_d2s_header(const char *filepath) {
    FILE *file = fopen(filepath, "rb");
    if (file == NULL) {
        perror("Error opening file");
        return 1;
    }

    D2S_Header header;

    // Четем D2S Header ID (0x00)
    if (fread(&header.header_id, sizeof(unsigned int), 1, file) != 1) goto read_error;

    // Четем Version (0x04)
    if (fread(&header.version, sizeof(unsigned int), 1, file) != 1) goto read_error;
    
    // Прескачаме до името на героя (0x24)
    fseek(file, 0x24, SEEK_SET);

    // Четем името на героя (16 bytes)
    if (fread(header.char_name, 1, 16, file) != 16) goto read_error;
    
    // Премахваме нулевия символ в края на името
    header.char_name[15] = '\0'; 
    
    // Четем Class ID (0x4C)
    fseek(file, 0x4C, SEEK_SET);
    if (fread(&header.char_class, sizeof(unsigned char), 1, file) != 1) goto read_error;

    // Четем Level (0x4D)
    fseek(file, 0x4D, SEEK_SET);
    if (fread(&header.level, sizeof(unsigned int), 1, file) != 1) goto read_error;

    // Извеждане на резултатите
    printf("--- Basic D2S Data Found ---\n");
    printf("File ID: %c%c%c%c\n", (char)(header.header_id & 0xFF), (char)((header.header_id >> 8) & 0xFF), (char)((header.header_id >> 16) & 0xFF), (char)((header.header_id >> 24) & 0xFF));
    printf("Version: %u\n", header.version);
    printf("Character Name: %s\n", header.char_name);
    printf("Class ID: %u\n", header.char_class);
    printf("Level: %u\n", header.level);

    fclose(file);
    return 0;

read_error:
    perror("Error reading data from file");
    fclose(file);
    return 1;
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <path_to_d2s_file>\n", argv[0]);
        return 1;
    }

    // Примерна команда: ./d2s_reader /usr/local/pvpgn/var/pvpgn/charsave/zgan/sorsi
    return read_d2s_header(argv[1]);
}
