#include <boost/beast.hpp>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <string>
#include <thread>
#include "server.cpp"

namespace beast = boost::beast;
namespace http = beast::http;
namespace net = boost::asio;
using tcp = boost::asio::ip::tcp;

int main(int argc, char *argv[]) {
    try {
        if (argc != 6) {
            std::cout << "Invalid parameter" << std::endl;
            std::cout << "Parameter: <interval millsec> <turn millisec> <max turn> <start between> <field path>" << std::endl;
            return EXIT_FAILURE;
        }
        auto const address = net::ip::make_address("127.0.0.1");
        auto const port = static_cast<short unsigned int>(8081);
        GameBord *gamebord = new GameBord;
        gamebord->initialize_fields(atoi(argv[1]), atoi(argv[2]), atoi(argv[3]), atoi(argv[4]), argv[5]);
        net::io_context ioc(1);
        tcp::acceptor accepter(ioc, tcp::endpoint(address, port));
        boost::system::error_code error;
        std::thread th(game_progress, gamebord);
        while(true) {
            std::cout << 1 << std::endl;
            tcp::socket socket(ioc);
            accepter.accept(socket, error);
            std::thread{std::bind(
                &serverSession,
                std::move(socket), gamebord)}.detach();
            std::cout << error << std::endl;
        }
        th.join();
    } catch (std::exception &e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return EXIT_FAILURE;
    }
}