#include <algorithm>
#include <iostream>
#include <vector>

int main() {
    const int limit = 1000;
    std::vector<int> fibonacci;

    int previous = 0;
    int current = 1;

    while (current <= limit) {
        if (fibonacci.empty() || fibonacci.back() != current) {
            fibonacci.push_back(current);
        }

        int next = previous + current;
        previous = current;
        current = next;
    }

    const std::size_t desiredCount = 15;
    const std::size_t count = std::min(desiredCount, fibonacci.size());

    for (std::size_t i = 0; i < count; ++i) {
        std::size_t index = fibonacci.size() - 1 - i;
        std::cout << fibonacci[index];
        if (i + 1 < count) {
            std::cout << " ";
        }
    }

    std::cout << std::endl;
    return 0;
}
