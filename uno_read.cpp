#include <iostream>
#include <fstream>
#include <string>
#include <regex>
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>

#define SERIAL_PORT "/dev/ttyACM0"
#define BAUDRATE B9600

#define TEMP_FILE "/home/arduino/app-lab/shared/temperature.txt"
#define HUM_FILE  "/home/arduino/app-lab/shared/humidity.txt"

int main() {
    // 시리얼 포트 열기
    int fd = open(SERIAL_PORT, O_RDONLY | O_NOCTTY);
    if (fd < 0) {
        perror("Serial open failed");
        return 1;
    }

    // 시리얼 설정
    struct termios tty;
    tcgetattr(fd, &tty);

    cfsetispeed(&tty, BAUDRATE);
    cfsetospeed(&tty, BAUDRATE);

    tty.c_cflag |= (CLOCAL | CREAD);
    tty.c_cflag &= ~CSIZE;
    tty.c_cflag |= CS8;
    tty.c_cflag &= ~PARENB;
    tty.c_cflag &= ~CSTOPB;
    tty.c_cflag &= ~CRTSCTS;

    tty.c_lflag = 0;
    tty.c_oflag = 0;
    tty.c_iflag = 0;

    tty.c_cc[VMIN]  = 1;
    tty.c_cc[VTIME] = 0;

    tcsetattr(fd, TCSANOW, &tty);

    std::regex pattern(
        R"(Temp:\s*([0-9.]+)\s*C,\s*Humidity:\s*([0-9.]+))"
    );

    std::string buffer;
    char ch;

    while (true) {
        if (read(fd, &ch, 1) > 0) {
            if (ch == '\n') {
                std::smatch match;
                if (std::regex_search(buffer, match, pattern)) {
                    float temp = std::stof(match[1]);
                    float hum  = std::stof(match[2]);

                    // 파일에 float 값만 저장
                    {
                        std::ofstream tfile(TEMP_FILE);
                        tfile << temp << std::endl;
                    }
                    {
                        std::ofstream hfile(HUM_FILE);
                        hfile << hum << std::endl;
                    }

                    std::cout << "Updated: "
                              << temp << " C, "
                              << hum << " %" << std::endl;
                }
                buffer.clear();
            } else {
                buffer += ch;
            }
        }
    }

    close(fd);
    return 0;
}

