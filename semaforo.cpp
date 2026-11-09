#include <iostream>
#include <thread>
#include <chrono>
#include <mutex>
using namespace std;

mutex mtx;
bool green = true, yellow = false;
bool red = false;

void trafficLight() {
    while (true) {
        {
            lock_guard<mutex> lock(mtx);
            if (green) {
                cout << "Green Light\n";
                this_thread::sleep_for(
                    chrono::seconds(5));
                green = false;
                yellow = true;
            } else if (yellow) {
                cout << "Yellow Light\n";
                this_thread::sleep_for(
                    chrono::seconds(2));
                yellow = false;
                red = true;
            } else {
                cout << "Red Light\n";
                this_thread::sleep_for(
                    chrono::seconds(5));
                red = false;
                green = true;
            }
        }
    }
}

int main() {
    thread t(trafficLight);
    t.join();
    return 0;
}